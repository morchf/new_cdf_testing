
#!/usr/bin/env python3

from assetlib_templates import *
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

        template_types = ['device', 'group']

        for template_type in template_types:

            template_list(template_type, pub_or_draft='published')

    else:
        argp.print_help()

if __name__ == "__main__":
    main()
