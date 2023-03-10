#!/usr/bin/env python

import argparse
import json
import thing
import policy
import certs
import misc
import boto3
import sys
import os

def check_aws_configuration():
    mysession = boto3.session.Session()
    if not (mysession._session._config['profiles']):
        print("AWS not configured. Please run `aws configure`.")
        sys.exit(1)


def prereq():
    with open('configure.json') as file:
        json_text = json.load(file)

    # If using existing policy, make sure policy exists before 
    # creating the thing
    thing_name = json_text.get('thing_name',"")
    mac_addr = json_text.get('mac_addr', "")

    # Create a Thing
    thing_obj = thing.Thing(thing_name)
    if not thing_obj.create():
        # Create a Certificate
        cert_obj = certs.Certificate()
        result = cert_obj.create()

        # Store certId
        cert_id = result['certificateId']
        cert_id_filename = thing_name + '_cert_id.txt'
        cert_id_file = open(cert_id_filename, 'w')
        cert_id_file.write(cert_id)
        cert_id_file_path = os.path.abspath(cert_id_filename)
        os.chmod(cert_id_file_path, 0o664)
        cert_id_file.close()

        # Store cert_pem as file
        cert_pem = result['certificatePem']
        cert_pem_filename = thing_name + '_cert.pem'
        cert_pem_file = open(cert_pem_filename, 'w')
        cert_pem_file.write(cert_pem)
        cert_pem_file_path = os.path.abspath(cert_pem_filename)
        os.chmod(cert_pem_file_path, 0o664)
        cert_pem_file.close()

        # Store private key PEM as file
        private_key_pem = result['keyPair']['PrivateKey']
        private_key_pem_filename = thing_name + '_private_key.pem'
        private_key_pem_file = open(private_key_pem_filename, 'w')
        private_key_pem_file.write(private_key_pem)
        private_key_pem_file_path = os.path.abspath(private_key_pem_filename)
        os.chmod(private_key_pem_file_path, 0o664)
        private_key_pem_file.close()

        # Create thing policy
        policy_document_text = misc.create_policy_document_text(thing_name)
        if policy_document_text:
            policy_obj = policy.Policy(thing_name, policy_document_text)
            cert_policy_name = policy_obj.create()
            print('Creating Certificate Policy {}'.format(cert_policy_name))

        # Attach the Policy to the Cert, Cert to thing
        cert_obj.attach_thing(thing_name)
        cert_obj.attach_policy(cert_policy_name)


def update_credential_file():
    with open('configure.json') as file:
        json_text = json.load(file)

    if json_text.get('afr_source_dir', None):
        afr_source_dir = os.path.expanduser(json_text['afr_source_dir'])
    else:
        afr_source_dir = None

    thing_name = json_text.get('thing_name',"")
    mac_addr = json_text.get('mac_addr', "")
    wifi_ssid = json_text.get('wifi_ssid', "")
    wifi_passwd = json_text.get('wifi_password', "")
    wifi_security = json_text.get('wifi_security', "")

    # Read cert_pem from file
    cert_pem_filename = thing_name + '_cert.pem'
    try:
        cert_pem_file = open(cert_pem_filename, 'r')
    except IOError:
        print("%s file not found. Run prerequisite step"%cert_pem_filename)
        sys.exit(1)
    else:
        cert_pem = cert_pem_file.read()

    # Read private_key_pem from file
    private_key_pem_filename = thing_name + '_private_key.pem'
    try:
        private_key_pem_file = open(private_key_pem_filename, 'r')
    except IOError:
        print("%s file not found. Run prerequisite step"%private_key_pem_filename)
        sys.exit(1)
    else:
        private_key_pem = private_key_pem_file.read()

    # Modify 'aws_clientcredential.h' file
    misc.update_client_credentials(
        afr_source_dir, thing_name, wifi_ssid, wifi_passwd, wifi_security)

    # Modify 'aws_clientcredential_keys.h' file
    misc.update_client_credential_keys(
        afr_source_dir, cert_pem, private_key_pem)

    # Modify 'thing_config.py' file
    misc.update_thing_config(thing_name, mac_addr)

def delete_prereq():
    with open('configure.json') as file:
        json_text = json.load(file)

    # Delete Thing
    thing_name = json_text['thing_name']
    thing_obj = thing.Thing(thing_name)
    thing_obj.delete()

    # Delete certificate
    cert_id_filename = thing_name + '_cert_id.txt'
    cert_id_file = open(cert_id_filename, 'r')
    cert_id =  cert_id_file.read()
    cert_obj = certs.Certificate(cert_id)
    cert_obj.delete()
    cert_id_file.close()
    cert_id_file_path = os.path.abspath(cert_id_filename)
    os.chmod(cert_id_file_path, 0o666)
    os.remove(cert_id_filename)

    # Delete cert_pem file and private_key_pem file
    cert_pem_filename = thing_name + '_cert.pem'
    private_key_pem_filename = thing_name + '_private_key.pem'
    cert_pem_file_path = os.path.abspath(cert_pem_filename)
    private_key_pem_file_path = os.path.abspath(private_key_pem_filename)
    os.chmod(cert_pem_file_path, 0o666)
    os.chmod(private_key_pem_file_path, 0o666)
    os.remove(cert_pem_filename)
    os.remove(private_key_pem_filename)

    # Delete policy
    policy_obj = policy.Policy(thing_name)
    policy_obj.delete()

def cleanup_local_files():
    with open('configure.json') as file:
        json_text = json.load(file)

    if json_text.get('afr_source_dir', None):
        afr_source_dir = os.path.expanduser(json_text['afr_source_dir'])
    else: 
        afr_source_dir = None
    
    # Cleanup modified 'aws_clientcredential.h' file
    misc.cleanup_client_credential_file(afr_source_dir)

    # Cleanup modified 'aws_clientcredential_keys.h' file
    misc.cleanup_client_credential_keys_file(afr_source_dir)

    # Cleanup modified 'thing_config.py' file
    misc.cleanup_thing_config()

def setup():
    prereq()
    update_credential_file()

def cleanup():
    delete_prereq()
    cleanup_local_files()

def list_certificates():
    client = boto3.client('iot')
    certs = client.list_certificates()['certificates']
    for cert in certs:
        certId = cert.get('certificateId', None)
        print(certId)
        print(cert)
        if certId != None :
            print(client.describe_certificate(certificateId=certId))
            break

def list_things():
    client = boto3.client('iot')
    things = client.list_things()['things']
    print(things)

def list_policies():
    client = boto3.client('iot')
    policies = client.list_policies()['policies']
    print(policies)

if __name__ == "__main__":

    arg_parser = argparse.ArgumentParser()
    sub_arg_parser = arg_parser.add_subparsers(help='Available commands',
        dest='command')
    setup_parser = sub_arg_parser.add_parser('setup', help='setup aws iot')
    clean_parser = sub_arg_parser.add_parser('cleanup', help='cleanup aws iot')
    list_cert_parser = sub_arg_parser.add_parser('list_certificates',
        help='list certificates')
    list_thing_parser = sub_arg_parser.add_parser('list_things',
        help='list things')
    list_policy_parser = sub_arg_parser.add_parser('list_policies',
        help='list policies')
    prereq_parser = sub_arg_parser.add_parser('prereq',
        help='Setup Prerequisites for aws iot')
    update_creds = sub_arg_parser.add_parser('update_creds',
        help='Update credential files')
    delete_prereq_parser = sub_arg_parser.add_parser('delete_prereq',
        help='Delete prerequisites created')
    cleanup_creds_parser = sub_arg_parser.add_parser('cleanup_creds',
        help='Cleanup credential files')
    args = arg_parser.parse_args()

    check_aws_configuration()

    if args.command == 'setup':
        setup()
    elif args.command == 'cleanup':
        cleanup()
    elif args.command == 'list_certificates':
        list_certificates()
    elif args.command == 'list_things':
        list_things()
    elif args.command == 'list_policies':
        list_policies()
    elif args.command == 'prereq':
        prereq()
    elif args.command == 'update_creds':
        update_credential_file()
    elif args.command == 'delete_prereq':
        delete_prereq()
    elif args.command == 'cleanup_creds':
        cleanup_local_files()
    else:
        print("Command does not exist")
