
#!/usr/bin/env python3

from assetlib_groups import *
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
        group_paths = ['/portlandmetro/stumptown', '/portlandmetro/firedept']
        relationships = ['ownedby']
        for group_path in group_paths:
            for relationship in relationships:
                group_list_devices(group_path, relationship)

    else:
        argp.print_help()

if __name__ == "__main__":
    main()
