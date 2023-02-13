
#!/usr/bin/env python3

from assetlib_templates import *
from config_assetlib import *
import sys, os, json, boto3
from botocore.config import Config



def cert_rotation_lambda(event, context):


    log.info('hello\n{}\n{}'.format(access_key, secret_key))

    environment = 'stage'

    log.info('environment = {}'.format(environment))

    if environment:

        log.info('hello again')

        get_url_info(environment)

        template_types = ['device', 'group']

        for template_type in template_types:

            template_list(template_type, pub_or_draft='published')

    message = {'d1':'new myron'}
    pub_retries = Config(retries={'max_attempts': 4})
    client = boto3.client('iot-data', config=pub_retries)
    client.publish(topic='/testing/one', qos=1, payload=json.dumps(message))


