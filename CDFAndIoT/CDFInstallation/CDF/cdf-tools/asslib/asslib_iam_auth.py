#!/usr/bin/env python3

import boto3
import sys, os, base64, datetime, hashlib, hmac, urllib
import json
from config_assetlib import *
import requests

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

        request_hash_str = request_hash_str.replace('%2f', '%252F')
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

