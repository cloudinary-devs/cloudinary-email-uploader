from flask import Flask, request, render_template
import os
import json
from retry import retry

import cloudinary
import cloudinary.uploader

import sendgrid
from sendgrid.helpers.inbound.config import Config
from sendgrid.helpers.inbound.parse import Parse

app = Flask(__name__)
config = Config()

@app.route('/', methods=['POST'])
@retry(tries=5, delay=2)
def inbound_parse():
    """Process POST from Inbound Parse and print received data."""
    parse = Parse(config, request)
    # Sample processing action
    # print(parse.key_values())
    email = parse.key_values()
    #parse cloudnames from incoming webhook
    cloudnames = []
    j = json.loads(email['envelope'])
    for full_add in j['to']:
        cloudnames.append(full_add.split('@')[0].strip())
    print ('Will attempt upload to the following clouds: ')
    print (cloudnames)
    
    #parse attachments in base64 format from webhook
    atts = parse.attachments()
    if len(atts)>0:
        for attachment in atts:
            print ('Will try and upload to cloudinary', attachment['file_name'])
            if 'image' in attachment['type']:
                print ('content type:'+ attachment['type'] + ' is approved for upload')
                for cloudname in cloudnames:
                    try:
                        r = cloudinary.uploader.unsigned_upload(
                            'data:'+attachment['type']+';base64,'+attachment['contents'],
                            upload_preset,
                            public_id=attachment['file_name'],
                            cloud_name = cloudname
                        )
                        print(r)
                    except Exception as e:
                        print(e)
            else:
                print ('content type:'+ attachment['type'] + ' is not approved for upload, skipping it.')


    # Tell SendGrid's Inbound Parse to stop sending POSTs
    # Everything is 200 OK :)
    return "OK"


if __name__ == '__main__':
  port = int(os.environ.get('PORT', 80))
  upload_preset = str(os.environ.get('UP_PRESET', 'email_uploader'))
  print ("app will run on port:", port)
  app.run(host='0.0.0.0', port=port)