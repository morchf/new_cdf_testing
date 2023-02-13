
#!/usr/bin/env python3

from assetlib_devices import *
from config_assetlib import *
import sys, os, json, boto3, argparse


def main():

    argp = argparse.ArgumentParser(description='try this arg parser')
    argp.add_argument('env', help='enter environment')
    args = argp.parse_args()

    environment = args.env

    log.debug('environment = {}'.format(environment))

    if environment:
        get_url_info(environment)
        device_instances = ['firetruck99', 'firetruck101', 'MalfunctionJunction', 'SpaghettiJunction']
        for instance_name in device_instances:
            device_create_instance(instance_name)
            device_list_instance(instance_name)

    else:
        argp.print_help()

if __name__ == "__main__":
    main()
