#!/usr/bin/env python3

import sys, os, datetime, time, json, boto3, requests
from config_assetlib import *
from asslib_iam_auth import create_auth_header_str


'''
*************************************
template functions
 - check_valid_template() - make sure device name is on list
 - template_list() - list all device templates, including root
 - template_create() - create a device template
 - tempalte_publish() - publish a device template after it has been create
 - template_patch() - modify an existing device template after it has been created
 - template_delete() - delete a published device template
 - template_list_instances() - list instance of a template
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

    
def template_list(template_type, pub_or_draft='published'):

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
        log.error('Invalid template type : {}'.format(template_type))
        status_code = 400
    return status_code


def template_create(template_type, template_name):

    if check_valid_template(template_type, template_name):
        template_file_pathname = './data/{}_template.json'.format(template_name)
        if os.path.exists(template_file_pathname):
            with open(template_file_pathname) as json_file:
                    body_dict = json.load(json_file)
            t = datetime.datetime.utcnow()
            datetime_str= t.strftime('%Y%m%dT%H%M%SZ') 
            date_str = t.strftime('%Y%m%d') 

            path_url = '/{}/templates/{}/{}'.format(os.getenv('API_ENV'), template_type, template_name)
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
            log.error('Invalid template name: {}'.format(template_name))
            status_code = 400
    else:
        log.error('Invalid template type or name: {}, {}'.format(template_type, template_name))
        status_code = 400
        
    return  status_code


def template_publish(template_type, template_name):
    
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
        for retry in range(RETRY_COUNT):
            r = requests.put(url, headers=headers)
            if r != 502:
                break
            log.info('********* Asset Library \"Internal Server Error\" *******')
            time.sleep(RETRY_WAIT)
        log.info('response code = {}'.format(r.status_code))
        log.info('response text = {}'.format(r.text))
        status_code = r.status_code

    else:
        log.error('Invalid template type or name: {}'.format(template_type, template_name))
        status_code = 400
        
    return  status_code

def template_patch(template_type, template_name):
    
    if check_valid_template(template_type, template_name):
        template_file_pathname = './data/{}_template.json'.format(template_name)
        if os.path.exists(template_file_pathname):
            with open(template_file_pathname) as json_file:
                    body_dict = json.load(json_file)
            t = datetime.datetime.utcnow()
            datetime_str= t.strftime('%Y%m%dT%H%M%SZ') 
            date_str = t.strftime('%Y%m%d') 

            path_url = '/{}/templates/{}/{}'.format(os.getenv('API_ENV'), template_type, template_name)
            query_str = ''
            url='{}{}'.format(os.getenv('BASE_URL'), path_url)
            auth_header_str = create_auth_header_str('PATCH', path_url, query_str, datetime_str, date_str, json.dumps(body_dict))
            headers = {'Accept':ACCEPT, 
                    'Content-Type':CONTENT_TYPE, 
                    'Host':os.getenv('HOST'), 
                    'X-Amz-Date':datetime_str, 
                    'Authorization':auth_header_str}

            log.debug(str(headers))
            log.info('url = {}'.format(url))
            for retry in range(RETRY_COUNT):
                r = requests.patch(url, headers=headers, json=body_dict)
                if r != 502:
                    break
                log.info('********* Asset Library \"Internal Server Error\" *******')
                time.sleep(RETRY_WAIT)
            log.info('response code = {}'.format(r.status_code))
            log.info('response text = {}'.format(r.text))
            status_code = r.status_code
        else:
            log.error('Invalid template name: {}'.format(template_name))
            status_code = 400
    else:
        log.error('Invalid template type or name: {}, {}'.format(template_type, template_name))
        status_code = 400
        
    return  status_code

def template_delete(template_type, template_name):

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
        log.error('Invalid template type or name: {}'.format(template_type, template_name))
        status_code = 400
        
    return  status_code

def template_list_instances(template_type, template_name):

    if check_valid_template(template_type, template_name):
        t = datetime.datetime.utcnow()
        datetime_str= t.strftime('%Y%m%dT%H%M%SZ') 
        date_str = t.strftime('%Y%m%d') 

        path_url = '/{}/search'.format(os.getenv('API_ENV'))
        body_str = ''
        query_str = 'type={}'.format(template_name)
        url='{}{}?{}'.format(os.getenv('BASE_URL'), path_url, query_str)
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
        log.error('Invalid template type or name: {}'.format(template_name))
        status_code = 400
        
    return  status_code

