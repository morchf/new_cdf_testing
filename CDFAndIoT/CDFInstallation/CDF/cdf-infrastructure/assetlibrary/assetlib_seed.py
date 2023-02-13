
#!/usr/bin/env python3

import assetlib_templates as al_t
import json
from config_assetlib import log, valid_device_templates, valid_group_templates
import sys, os
import boto3

check_order = False    # TRUE = Do not call asset lib API, just check the sequence
delete_templates = False   # TRUE = Delete templates

#
# Rule #1:
#    Relationships cannot be created unless the template in the relationship exists.
#
#    Note: Sequence is critical because of the relationship. The template will be
#        created regardless of whether the template in the relation exists or not,
#        but if the template does not exist, the relationship does not get created.
#        The issue is not realized until after a device is added to a group where a
#        relationship is expected, but does not exist. The API call to asset library
#        returns a "" error.
#
#    Action: Here we define relationships in groups, so device templates mush be
#        created before the group relationships. If you define relatioships in the
#        device templates, then create the group templates before the device
#        templates.
#
# Rule #2:
#    Device templates referenced in a relationship cannot be deleted.
#
#    Note: Sequence is critical because of the relationship. The
#        API call to asset library returns a "" error if an attempt is made to
#        delete a device template referenced in a relationship in a group template.
#
#    Action: Delete the group templates with the relationships before deleting
#        the device templates.
#
# Rule #3
#    Only templates with no instances can be deleted.
#
#    Action: If delete fails, the check for instances of that template. Delete
#        the instances before attempting to delete the template.
#
#
def parse_url(url_input):
    url_parts = url_input.split('/')
    api_env = url_parts[-1]  # url_parts = ['https', '', <HOST>, 'Prod']
    host = url_parts[2]  # url_parts = ['https', '', <HOST>, 'Prod']
    base = 'https://{}'.format(host)
    return base, host, api_env

def get_url_info(env):
    client = boto3.client('cloudformation')
    stack_name = 'cdf-assetlibrary-{}'.format(env)
    describe_stacks = client.describe_stacks(StackName=stack_name)
    stacks = describe_stacks['Stacks']
    for stack in stacks:
        outputs = stack['Outputs']
        for output in outputs:
            export_name='cdf-assetlibrary-{}-apigatewayurl'.format(env)
            if output['ExportName'] == export_name:
                base, host, api_env = parse_url(output['OutputValue'])
                os.environ['BASE_URL'] = base
                os.environ['HOST'] = host
                os.environ['API_ENV'] = api_env
                return

def main():

    try:
        environment = sys.argv[1]
    except:
        environment = None

    if environment:

        get_url_info(environment)

        if delete_templates:
            template_types = ['group', 'device']
        else:
            template_types = ['device', 'group']

        for template_type in template_types:

            log.info('@@@@@@@@ LIST {} @@@@@@@'.format(template_type))
            if not check_order:
                al_t.list_templates(template_type, pub_or_draft='draft')
                al_t.list_templates(template_type)

            if template_type == 'group':
                valid_templates = valid_group_templates
            elif template_type == 'device':
                valid_templates = valid_device_templates
            else:
                log.error('Bad template type: {}'.format(template_type))
                break

            for template in valid_templates:
                if check_order:
                    log.info('@@@@@@@@ CHECK  {} {} @@@@@@@'.format(template_type, template))
                    continue

                if delete_templates:
                    log.info('@@@@@@@@ DELETE  {} {} @@@@@@@'.format(template_type, template))
                    al_t.delete_template(template_type, template)
                    break
                if template == 'communicator':
                    with open('communicator_template.json') as json_file:
                        body_dict = json.load(json_file)
                elif template == 'vehiclev2':
                    with open('vehiclev2_template.json') as json_file:
                        body_dict = json.load(json_file)
                elif template == 'phaseselector':
                    with open('phaseselector_template.json') as json_file:
                        body_dict = json.load(json_file)
                elif template == 'agency':
                    with open('agency_template.json') as json_file:
                        body_dict = json.load(json_file)
                elif template == 'region':
                    with open('region_template.json') as json_file:
                        body_dict = json.load(json_file)
                else:
                    log.error('Bad template name: {}'.format(template))
                    break

                log.info('@@@@@@@@ CREATE {} {} @@@@@@@'.format(template_type, template))
                al_t.create_template(template_type, template, body_dict)
                log.info('@@@@@@@@ PUBLISH {} {} @@@@@@@'.format(template_type, template))
                al_t.publish_template(template_type, template)
            if not check_order:
                al_t.list_templates(template_type, pub_or_draft='draft')
                al_t.list_templates(template_type)

    else:
        print('Need ENVIRONMENT')
if __name__ == "__main__":
    main()
