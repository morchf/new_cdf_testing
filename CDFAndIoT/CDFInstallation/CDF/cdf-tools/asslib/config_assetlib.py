#!/usr/bin/env python3

import logging, boto3, os

#logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s', level=logging.INFO)
logging.basicConfig(format='%(asctime)s: %(levelname)s: %(funcName)15s: %(message)s', level=logging.INFO)
logger = logging.getLogger()
log = logger

valid_device_templates = [
        'vehicle',            
        'phaseselector']     

valid_group_templates = [
        'region',              
        'agency']              

# Config paramters for http requests
ACCEPT='application/vnd.aws-cdf-v2.0+json'
CONTENT_TYPE='application/vnd.aws-cdf-v2.0+json'
SERVICE='execute-api'
AUTH_TYPE='IAM-USER'

RETRY_COUNT = 3
RETRY_DELAY = 20

session = boto3.Session()
cred = session.get_credentials()
region = session.region_name
access_key = cred.access_key
secret_key = cred.secret_key

def parse_url(url_input):
    url_parts = url_input.split('/')
    api_env = url_parts[-1]  # url_parts = ['https', '', <HOST>, 'Prod']
    host = url_parts[2]  # url_parts = ['https', '', <HOST>, 'Prod']
    base = 'https://{}'.format(host)
    return base, host, api_env

def get_url_info(env):
    client = boto3.client('cloudformation')
    stack_name = 'cdf-assetlibrary-{}'.format(env)
    describe_stacks = client.describe_stacks(StackName=stack_name)
    stacks = describe_stacks['Stacks']
    for stack in stacks:
        outputs = stack['Outputs']
        for output in outputs:
            export_name='cdf-assetlibrary-{}-apigatewayurl'.format(env)
            if output['ExportName'] == export_name:
                base, host, api_env = parse_url(output['OutputValue'])
                os.environ['BASE_URL'] = base
                os.environ['HOST'] = host
                os.environ['API_ENV'] = api_env
                return

