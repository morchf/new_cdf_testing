#!/usr/bin/env python3

import sys, os, datetime, time, json, boto3, requests
from config_assetlib import *
from asslib_iam_auth import create_auth_header_str


'''
*************************************
template functions
 - check_valid_device() - make sure device name is valid
 - device_create_instance() - create an instance for this device
 - device_list_instance() - list an instance of this this device
 - device_delete_instance() - delete an instance of this device
 -- device_list_devices() - list the devices having a relationship to this device
************************************
'''
def check_valid_device(pathname):
    return os.path.exists(pathname)

def device_create_instance(instance_name):
    pathname = './data/{}.json'.format(instance_name)
    if check_valid_device(pathname):
        with open(pathname) as json_file:
            body_dict = json.load(json_file)
        t = datetime.datetime.utcnow()
        datetime_str= t.strftime('%Y%m%dT%H%M%SZ') 
        date_str = t.strftime('%Y%m%d') 

        path_url = '/{}/devices'.format(os.getenv('API_ENV'))
        query_str = ''
        url='{}{}'.format(os.getenv('BASE_URL'), path_url)
        auth_header_str = create_auth_header_str('POST', path_url, query_str, datetime_str, date_str, json.dumps(body_dict))
        headers = {'Accept':ACCEPT, 
                'Content-Type':CONTENT_TYPE, 
                'Host':os.getenv('HOST'), 
                'X-Amz-Date':datetime_str, 
                'Authorization':auth_header_str}

        log.debug(str(headers))
        log.info('url = {}'.format(url))
        for retry in range(RETRY_COUNT):
            r = requests.post(url, headers=headers, json=body_dict)
            if r != 502:
                break
            log.info('********* Asset Library \"Internal Server Error\" *******')
            time.sleep(RETRY_WAIT)
        log.info('response code = {}'.format(r.status_code))
        log.info('response text = {}'.format(r.text))
        status_code = r.status_code
    else:
        log.error('Invalid device instance: {}'.format(instance_name))
        status_code = 400
        
    return  status_code
    
def device_list_instance(instance_name):
    pathname = './data/{}.json'.format(instance_name)
    if check_valid_device(pathname):
        t = datetime.datetime.utcnow()
        datetime_str= t.strftime('%Y%m%dT%H%M%SZ') 
        date_str = t.strftime('%Y%m%d') 

        path_url = '/{}/devices/{}'.format(os.getenv('API_ENV'), instance_name)
        query_str = ''
        body_str = ''
        url='{}{}'.format(os.getenv('BASE_URL'), path_url)
        auth_header_str = create_auth_header_str('GET', path_url, query_str, datetime_str, date_str, body_str)
        headers = {'Accept':ACCEPT, 
                'Content-Type':CONTENT_TYPE, 
                'Host':os.getenv('HOST'), 
                'X-Amz-Date':datetime_str, 
                'Authorization':auth_header_str}

        log.debug(str(headers))
        log.info('url = {}'.format(url))
        for retry in range(RETRY_COUNT):
            r = requests.get(url, headers=headers)
            if r != 502:
                break
            log.info('********* Asset Library \"Internal Server Error\" *******')
            time.sleep(RETRY_WAIT)
        log.info('response code = {}'.format(r.status_code))
        log.info('response text = {}'.format(r.text))
        status_code = r.status_code
    else:
        log.error('Invalid device instance: {}'.format(instance_name))
        status_code = 400
        
    return  status_code
    
def device_delete_instance(instance_name):
    pathname = './data/{}.json'.format(instance_name)
    if check_valid_device(pathname):
        t = datetime.datetime.utcnow()
        datetime_str= t.strftime('%Y%m%dT%H%M%SZ') 
        date_str = t.strftime('%Y%m%d') 

        path_url = '/{}/devices/{}'.format(os.getenv('API_ENV'), instance_name)
        query_str = ''
        body_str = ''
        url='{}{}'.format(os.getenv('BASE_URL'), path_url)
        auth_header_str = create_auth_header_str('DELETE', path_url, query_str, datetime_str, date_str, body_str)
        headers = {'Accept':ACCEPT, 
                'Content-Type':CONTENT_TYPE, 
                'Host':os.getenv('HOST'), 
                'X-Amz-Date':datetime_str, 
                'Authorization':auth_header_str}

        log.debug(str(headers))
        log.info('url = {}'.format(url))
        for retry in range(RETRY_COUNT):
            r = requests.delete(url, headers=headers)
            if r != 502:
                break
            log.info('********* Asset Library \"Internal Server Error\" *******')
            time.sleep(RETRY_WAIT)
        log.info('response code = {}'.format(r.status_code))
        log.info('response text = {}'.format(r.text))
        status_code = r.status_code
    else:
        log.error('Invalid device instance: {}'.format(instance_name))
        status_code = 400
        
    return  status_code
    
