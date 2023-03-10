#!/usr/bin/env python

import os
import boto3
import shutil
import sys
import json


def describe_endpoint():
    client = boto3.client('iot')
    endpoint = client.describe_endpoint(endpointType='iot:Data-ATS')
    return endpoint['endpointAddress']

def get_account_id():
    client = boto3.client('sts')
    aws_account_id = client.get_caller_identity()['Account']
    return aws_account_id.strip('\n')

def get_aws_region():
    my_session = boto3.session.Session()
    aws_region = my_session.region_name
    return aws_region.strip('\n')

def create_policy_document_text(thing_name):
    policy_template = os.path.join(os.getcwd(), 'Policy.templ')
    try:
        with open(policy_template) as policy_template_file:
            policy_document_text = policy_template_file.read()
    except:
        print('Could not open {}.templ.'.fomrat(policy_template))
        return None

    region_name = str(get_aws_region())
    aws_account_id  = str(get_account_id())
    # Replace Account ID and AWS Region
    policy_document_text = policy_document_text.replace(
        '<aws-region>', region_name)
    policy_document_text = policy_document_text.replace(
        '<aws-account-id>', aws_account_id)
    policy_document_text = policy_document_text.replace(
        '<thing-name>', thing_name)

    return policy_document_text

def format_credential_keys_text(credentialText):
    credentialTextLines = credentialText.split('\n')
    formattedCredentialTextLines = []

    for credentialTextLine in credentialTextLines:
        if credentialTextLine.strip():
            formattedCredentialTextLine = '"' + credentialTextLine + '\\n"'
            formattedCredentialTextLines.append(formattedCredentialTextLine)

    formattedCredentialText = '\\\n'.join(formattedCredentialTextLines)
    return formattedCredentialText

def update_client_credentials(afr_source_dir, thing_name, wifi_ssid, wifi_passwd, wifi_security):
    if afr_source_dir:
        file_to_modify = os.path.join(
            afr_source_dir, 'demos', 'include', 'aws_clientcredential.h')
    else :
        file_to_modify = os.path.join(
            os.getcwd(), 'aws_clientcredential.h')

    filename = "aws_clientcredential.templ"
    with open(filename,'r') as template_file:
        file_text = template_file.read()
        new_text = file_text.replace("<WiFiSSID>", "\"" + wifi_ssid + "\"")
        new_text = new_text.replace("<WiFiPasswd>", "\"" + wifi_passwd + "\"")
        new_text = new_text.replace("<WiFiSecurity>", wifi_security)
        new_text = new_text.replace("<IOTThingName>", "\"" + thing_name + "\"")
        new_text = new_text.replace(
            "<IOTEndpoint>", "\"" + describe_endpoint() + "\"")
        header_file = open(str(file_to_modify),'w')
        header_file.write(new_text)
        header_file.close()

def update_client_credential_keys(afr_source_dir, client_certificate_pem, client_private_key_pem):
    if afr_source_dir:
        file_to_modify = os.path.join(
            afr_source_dir, 'demos', 'include', 'aws_clientcredential_keys.h')
    else :
        file_to_modify = os.path.join(
            os.getcwd(), 'aws_clientcredential_keys.h')

    filename = "aws_clientcredential_keys.templ"
    with open(filename,'r') as template_file:
        file_text = template_file.read()
        new_text = file_text.replace("<ClientCertificatePEM>",
                format_credential_keys_text(client_certificate_pem))
        new_text = new_text.replace("<ClientPrivateKeyPEM>",
                format_credential_keys_text(client_private_key_pem))
        header_file = open(str(file_to_modify),'w')
        header_file.write(new_text)
        header_file.close()

def update_thing_config(thing_name, mac_addr):
    ouput_file_name = 'thing_config.py'
    template_file_name = 'thing_config.templ'

    with open(template_file_name,'r') as template_file:
        input_text = template_file.read()
        output_text = input_text.replace("<thing-name>", '\'' + thing_name + '\'')
        output_text = output_text.replace("<mac-addr>", '\'' + mac_addr + '\'')
        out_file = open(str(ouput_file_name),'w')
        out_file.write(output_text)
        out_file.close()

def cleanup_client_credential_file(afr_source_dir):
    if afr_source_dir:
        client_credential_file = os.path.join(
            afr_source_dir, 'demos', 'include', 'aws_clientcredential.h')
    else :
        client_credential_file = os.path.join(
            os.getcwd(), 'aws_clientcredential.h')

    os.remove(client_credential_file)

def cleanup_client_credential_keys_file(afr_source_dir):
    if afr_source_dir:
        client_credential_keys_file = os.path.join(
            afr_source_dir, 'demos', 'include', 'aws_clientcredential_keys.h')
    else :
        client_credential_keys_file = os.path.join(
            os.getcwd(), 'aws_clientcredential_keys.h')

    os.remove(client_credential_keys_file)

def cleanup_thing_config():
    thing_config_file = os.path.join(
        os.getcwd(), 'thing_config.py')

    os.remove(thing_config_file)
