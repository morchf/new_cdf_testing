
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

            if template_type == 'group':
                valid_template_names = valid_group_templates
            elif template_type == 'device':
                valid_template_names = valid_device_templates
            else:
                log.error('Bad template type: {}'.format(template_type))
                break

            for template_name in valid_template_names:
                template_create(template_type, template_name)
                template_publish(template_type, template_name)

    else:
        argp.print_help()

if __name__ == "__main__":
    main()
