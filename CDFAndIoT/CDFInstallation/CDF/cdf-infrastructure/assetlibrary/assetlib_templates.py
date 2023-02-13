#!/usr/bin/env python3

import boto3
import sys, os, base64, datetime, hashlib, hmac, urllib
import json
from config_assetlib import log, valid_device_templates, valid_group_templates
import requests

# Config paramters for http requests
ACCEPT='application/vnd.aws-cdf-v2.0+json'
CONTENT_TYPE='application/vnd.aws-cdf-v2.0+json'
SERVICE='execute-api'
AUTH_TYPE='IAM-USER'

session = boto3.Session()
cred = session.get_credentials()
region = session.region_name
access_key = cred.access_key
secret_key = cred.secret_key


'''
*************************************
Support functions
 - sign() - sign a message
 - getSignatureKey() - generate a key to sign a message
 - create_auth_header_str() - create the string for the Authorization header
************************************
'''
def sign(key, msg):
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

def getSignatureKey(key, date_stamp, regionName, serviceName):
        kDate = sign(('AWS4' + key).encode('utf-8'), date_stamp)
        kRegion = sign(kDate, regionName)
        kService = sign(kRegion, serviceName)
        kSigning = sign(kService, 'aws4_request')
        return kSigning

def create_auth_header_str(method, url_to_be_hashed, query_to_be_hashed, datetime_str, date_str, payload_str):

    auth_header_str = None
    if AUTH_TYPE == 'IAM-USER':
        # Auth header string for IAM-user has 4 sections:
        #  - encryption = SHA256
        #  - Credential = access key, region, service
        #  - SignedHeaders = all header included in signature
        #  - Signature = encrypted signature composed of many things
        ALGORITHM='AWS4-HMAC-SHA256'
        credential_to_be_hashed='{}/{}/{}/aws4_request'.\
                format(date_str, region, SERVICE)
        credential_str='Credential={}/{}/{}/{}/aws4_request'.\
                format(access_key, date_str, region, SERVICE)
        SIGNED_HEADER_STR='host;x-amz-date'

        payload_hash = hashlib.sha256((payload_str).encode('utf-8')).hexdigest()

        headers_to_be_hashed = 'host:{}\nx-amz-date:{}\n'.\
                format(os.getenv('HOST'), datetime_str)

        if query_to_be_hashed != None:
            request_hash_str = '{meth}\n{url}\n{qry}\n{hdrs}\n{shdrs}\n{payl}'.\
                format(meth=method,
                    url=url_to_be_hashed,
                    qry=query_to_be_hashed,
                    hdrs=headers_to_be_hashed,
                    shdrs=SIGNED_HEADER_STR,
                    payl=payload_hash)

        else :
            request_hash_str = '{meth}\n{url}\n{hdrs}\n{shdrs}\n{payl}'.\
                format(meth=method,
                    url=url_to_be_hashed,
                    hdrs=headers_to_be_hashed,
                    shdrs=SIGNED_HEADER_STR,
                    payl=payload_hash)

        log.debug('\n*******\nrequest_hash_str = {}'.format(request_hash_str))

        request_hash = hashlib.sha256(request_hash_str.encode('utf-8')).hexdigest()

        string_to_be_signed = '{alg}\n{datetime}\n{cred}\n{rqst_hash}'.\
                format(alg=ALGORITHM,
                       datetime=datetime_str,
                       cred=credential_to_be_hashed,
                       rqst_hash=request_hash)

        log.debug('\n*******\nstring_to_be_signed = {}'.format(string_to_be_signed))

        signing_key = getSignatureKey(secret_key, date_str, region, SERVICE)
        signature = hmac.new(signing_key, (string_to_be_signed).encode('utf-8'), hashlib.sha256).hexdigest() 

        signed_header_str='SignedHeaders={}'.format(SIGNED_HEADER_STR)
        signature_str='Signature={}'.format(signature)

        auth_header_str = '{alg} {cred}, {shdrs}, {sig}'.\
                format(alg=ALGORITHM, 
                       cred=credential_str,
                       shdrs=signed_header_str,
                       sig=signature_str)

    return auth_header_str

'''
*************************************
template functions
 - check_valid_template() - make sure device name is on list
 - list_templates() - list all device templates, including root
 - create_template() - create a device template
 - publish_template() - publish a device template after it has been create
 - patch_template() - modify an existing device template after it has been created
 - delete_template() - delete a published device template
************************************
'''
def check_valid_template(template_type, check_this_template_name=None):
    rc = False
    if template_type == 'device':
        if check_this_template_name:
            rc = (check_this_template_name in valid_device_templates)
        else:
            rc = True
    elif template_type == 'group':
        if check_this_template_name:
            rc = (check_this_template_name in valid_group_templates)
        else:
            rc = True
    return rc

    
def list_templates(template_type, pub_or_draft='published'):

    if check_valid_template(template_type):
        t = datetime.datetime.utcnow()
        datetime_str= t.strftime('%Y%m%dT%H%M%SZ') 
        date_str = t.strftime('%Y%m%d') 

        path_url = '/{}/templates/{}'.format(os.getenv('API_ENV'), template_type)
        query_str = 'status={}'.format(pub_or_draft)
        body_str = ''
        url='{}{}?{}'.format(os.getenv('BASE_URL'), path_url, query_str)
        auth_header_str = create_auth_header_str('GET', path_url, query_str, datetime_str, date_str, body_str)
        headers = {'Accept':ACCEPT, 
                'Content-Type':CONTENT_TYPE, 
                'Host':os.getenv('HOST'), 
                'X-Amz-Date':datetime_str, 
                'Authorization':auth_header_str}

        log.debug(str(headers))
        log.info('url = {}'.format(url))
        r = requests.get(url, headers=headers)
        log.info('response code = {}'.format(r.status_code))
        log.info('response text = {}'.format(r.text))
        
        status_code = r.status_code
    else:
        log.error('Invalid template type : {}'.format(template_type))
        status_code = 400
    return status_code


def create_template(template_type, template_name, template_body_dict):

    if check_valid_template(template_type, template_name):
        t = datetime.datetime.utcnow()
        datetime_str= t.strftime('%Y%m%dT%H%M%SZ') 
        date_str = t.strftime('%Y%m%d') 

        path_url = '/{}/templates/{}/{}'.format(os.getenv('API_ENV'), template_type, template_name)
        query_str = ''
        url='{}{}'.format(os.getenv('BASE_URL'), path_url)
        auth_header_str = create_auth_header_str('POST', path_url, query_str, datetime_str, date_str, json.dumps(template_body_dict))
        headers = {'Accept':ACCEPT, 
                'Content-Type':CONTENT_TYPE, 
                'Host':os.getenv('HOST'), 
                'X-Amz-Date':datetime_str, 
                'Authorization':auth_header_str}

        log.debug(str(headers))
        log.info('url = {}'.format(url))
        r = requests.post(url, headers=headers, json=template_body_dict)
        log.info('response code = {}'.format(r.status_code))
        log.info('response text = {}'.format(r.text))
        status_code = r.status_code
    else:
        log.error('Invalid template type or name: {}'.format(template_type, template_name))
        status_code = 400
        
    return  status_code


def publish_template(template_type, template_name):
    
    if check_valid_template(template_type, template_name):

        t = datetime.datetime.utcnow()
        datetime_str= t.strftime('%Y%m%dT%H%M%SZ') 
        date_str = t.strftime('%Y%m%d') 

        path_url = '/{}/templates/{}/{}/publish'.format(os.getenv('API_ENV'), template_type, template_name)
        body_str = ''
        query_str = ''
        url='{}{}'.format(os.getenv('BASE_URL'), path_url)
        auth_header_str = create_auth_header_str('PUT', path_url, query_str, datetime_str, date_str, body_str)
        headers = {'Accept':ACCEPT, 
                'Content-Type':CONTENT_TYPE, 
                'Host':os.getenv('HOST'), 
                'X-Amz-Date':datetime_str, 
                'Authorization':auth_header_str}

        log.debug(str(headers))
        log.info('url = {}'.format(url))
        r = requests.put(url, headers=headers)
        log.info('response code = {}'.format(r.status_code))
        log.info('response text = {}'.format(r.text))
        status_code = r.status_code

    else:
        log.error('Invalid template type or name: {}'.format(template_type, template_name))
        status_code = 400
        
    return  status_code

def patch_template(template_type, template_name, template_body_dict):
    
    if check_valid_template(template_type, template_name):

        t = datetime.datetime.utcnow()
        datetime_str= t.strftime('%Y%m%dT%H%M%SZ') 
        date_str = t.strftime('%Y%m%d') 

        path_url = '/{}/templates/{}/{}'.format(os.getenv('API_ENV'), template_type, template_name)
        body_str = ''
        query_str = ''
        url='{}{}'.format(os.getenv('BASE_URL'), path_url)
        auth_header_str = create_auth_header_str('PATCH', path_url, query_str, datetime_str, date_str, json.dumps(template_body_dict))
        headers = {'Accept':ACCEPT, 
                'Content-Type':CONTENT_TYPE, 
                'Host':os.getenv('HOST'), 
                'X-Amz-Date':datetime_str, 
                'Authorization':auth_header_str}

        log.debug(str(headers))
        log.info('url = {}'.format(url))
        r = requests.patch(url, headers=headers, json=template_body_dict)
        log.info('response code = {}'.format(r.status_code))
        log.info('response text = {}'.format(r.text))
        status_code = r.status_code

    else:
        log.error('Invalid template type or name: {}'.format(template_type, template_name))
        status_code = 400
        
    return  status_code

def delete_template(template_type, template_name):

    if check_valid_template(template_type, template_name):
        t = datetime.datetime.utcnow()
        datetime_str= t.strftime('%Y%m%dT%H%M%SZ') 
        date_str = t.strftime('%Y%m%d') 

        path_url = '/{}/templates/{}/{}'.format(os.getenv('API_ENV'), template_type, template_name)
        body_str = ''
        query_str = ''
        url='{}{}'.format(os.getenv('BASE_URL'), path_url)
        auth_header_str = create_auth_header_str('DELETE', path_url, query_str, datetime_str, date_str, body_str)
        headers = {'Accept':ACCEPT, 
                'Content-Type':CONTENT_TYPE, 
                'Host':os.getenv('HOST'), 
                'X-Amz-Date':datetime_str, 
                'Authorization':auth_header_str}

        log.debug(str(headers))
        log.info('url = {}'.format(url))
        r = requests.delete(url, headers=headers)
        log.info('response code = {}'.format(r.status_code))
        log.info('response text = {}'.format(r.text))
        status_code = r.status_code
    else:
        log.error('Invalid template type or name: {}'.format(template_type, template_name))
        status_code = 400
        
    return  status_code

