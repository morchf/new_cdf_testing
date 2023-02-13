import collections
import functools
import os
import re
import traceback
from colors import color
import boto3
from botocore.exceptions import (ClientError,
                                 NoCredentialsError,
                                 NoRegionError,
                                 WaiterError)
import json

_ec2 = None
_cfn_client = None
_cfn_resource = None

def print_success():
    print(color('ok.', fg='green'))

def print_error(message):
    print(color('error!', fg='red') + ' ' + message)

def has_keys(mapping, keys):
    for key in keys:
        if key not in mapping:
            return False
    else:
        return True

def transform_aws_to_dict(mapping):
    """Transform an AWS-style dict to a natural dict. If a key appears multiple
    times, the last value is used.

    Arguments:
        mapping {list} -- A list of the form [{'__Key': KeyValue, '__Value': Value}]

    Returns:
        dict -- A dict of the form {'KeyValue': Value}
    """
    def flatten_item(item):
        out_dict = {}
        for key, value in item.items():
            if key.endswith('Key'):
                out_key = value
            elif key.endswith('Value'):
                out_value = value
        out_dict[out_key] = out_value
        return out_dict

    natural_dict = {
        key: value
        for i in map(
            flatten_item,
            mapping
        )
        for key, value in i.items()
    }

    return natural_dict

def transform_dict_to_aws(mapping, prefix='Parameter'):
    """Transform a natural dict to an AWS-style dict

    Arguments:
        mapping {dict} -- A dict of the form {'KeyValue': 'Value'}

    Keyword Arguments:
        prefix {str} -- The prefix to use before '__Key' and '__Value' (default: {'Parameter'})

    Returns:
        dict -- A dict of the form {'PrefixKey': KeyValue, 'PrefixValue': Value}
    """
    return [
      { prefix + 'Key': key,  prefix + 'Value': value }
      for key, value in mapping.items()
    ]

def initialize_boto():
    print('Initializing boto3... ', end='')
    try:
        global _ec2
        global _cfn_client
        global _cfn_resource
        _ec2 = boto3.client('ec2')
        _cfn_client = boto3.client('cloudformation')
        _cfn_resource = boto3.resource('cloudformation')
    except (NoCredentialsError, NoRegionError) as err:
        print_error(err.fmt)
        exit(1)
    except:
        print_error('An unexpected error occurred')
        traceback.print_exc()
        exit(1)
    else:
        print_success()

def create_stack(template_file_name, stack_inputs):
    script_path = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(script_path, template_file_name)
    with open(template_path, mode='r') as file:
        template_body = file.read()

    action = _cfn_client.create_stack(
        Parameters=stack_inputs['Parameters'],
        StackName=stack_inputs['StackName'],
        TemplateBody=template_body,
        TimeoutInMinutes=30
    )

    waiter = _cfn_client.get_waiter('stack_create_complete')
    waiter.wait(StackName=action['StackId'])
    return action['StackId']

def extract_gateway_props(stack_props):
    """Map the properties for each gateway to the gateway ID

    Arguments:
        stack_props {dict} -- A dict containing all stack properties

    Returns:
        dict -- A dict mapping gateway IDs to properties
    """
    matching_props = collections.defaultdict(dict)
    pattern = r"^Gateway(?P<id>[A-Z])(?P<attr>\w*)$"
    for key, value in stack_props.items():
        match = re.match(pattern, key)
        if match is not None:
            gateway_key = match['id']
            prop_key = match['attr']
            matching_props[gateway_key][prop_key] = value
    return matching_props

def map_attachments_to_vpns(gateway_props, transit_gateway_id):
    """Map transit gateway attachments to VPN connections based on ID

    Arguments:
        gateway_props {dict} -- A dict mapping gateway IDs to gateway properties
        transit_gateway_id {string} -- The ID of a Transit Gateway
    """
    attachments = _ec2.describe_transit_gateway_attachments(
        Filters=[{'Name': 'transit-gateway-id', 'Values': [transit_gateway_id]}]
    )['TransitGatewayAttachments']

    for attachment in attachments:
        for props in gateway_props.values():
            if props['VpnConnection'] == attachment['ResourceId']:
                props['TransitGatewayAttachment'] = attachment['TransitGatewayAttachmentId']


def tag_vpn_attachments(gateway_props):
    """Assign a Name tag to each VPN attachment based on gateway ID

    Arguments:
        gateway_props {dict} -- A dict mapping gateway IDs to gateway properties
    """
    for gateway_id, props in gateway_props.items():
        resource_id = props['TransitGatewayAttachment']
        try:
            _ec2.create_tags(
                Resources=[resource_id],
                Tags=[
                    {
                        'Key': 'Name',
                        'Value': 'Attachment to Gateway {0} VPN'.format(gateway_id)
                    }
                ]
            )
        except ClientError:
            raise

def associate_vpn_attachments(gateway_props, tg_route_table_id):
    """Associate each VPN attachment with a Transit Gateway route table

    Arguments:
        gateway_props {dict} -- A dict mapping gateway IDs to gateway properties
        tg_route_table_id {string} -- The ID of a Transit Gateway route table
    """
    for gateway_id, props in gateway_props.items():
        attachment_id = props['TransitGatewayAttachment']

        try:
            _ec2.associate_transit_gateway_route_table(
                TransitGatewayRouteTableId=tg_route_table_id,
                TransitGatewayAttachmentId=attachment_id
            )
        except ClientError as err:
            if err.response['Error']['Code'] != 'Resource.AlreadyAssociated':
                raise

def pre_cfn(tg_stack_inputs, evpc_stack_inputs):
    print('Creating Transit Gateway stack... ', end='', flush=True)
    try:
        tg_inputs = json.JSONDecoder().decode(tg_stack_inputs)
        tg_stack_id = create_stack('transit-gateway.yml', tg_inputs)
    except (ClientError, WaiterError) as e:
        print_error(e.response['Error']['Message'])
        exit(1)
    except json.JSONDecodeError as e:
        print_error('Invalid JSON in --stack-inputs.')
        exit(1)
    except KeyError as e:
        missing_key = e.args[0]
        print_error('Missing key \'{0}\' in --stack-inputs.'.format(missing_key))
        exit(1)
    except:
        print_error('An unexpected error occurred')
        traceback.print_exc()
        exit(1)
    else:
        print_success()

    # The Egress VPC stack needs the Transit Gateway ID from the Transit
    # Gateway stack as an input.
    tg_stack = _cfn_resource.Stack(tg_stack_id) # pylint: disable=no-member
    tg_stack_outputs = transform_aws_to_dict(tg_stack.outputs)
    tg_id = tg_stack_outputs['TransitGateway']

    print('Creating Egress VPC stack... ', end='', flush=True)
    try:
        evpc_inputs = json.JSONDecoder().decode(evpc_stack_inputs)
        evpc_parameters = evpc_inputs['Parameters']

        # Upsert the Transit Gateway ID in the Egress VPC stack inputs.
        for inp in evpc_parameters:
            if inp['ParameterKey'] == 'TransitGatewayId':
                inp['ParameterValue'] = tg_id
                break
        else:
            evpc_parameters.append({ 'ParameterKey': 'TransitGatewayId', 'ParameterValue': tg_id })

        evpc_stack_id = create_stack('egress-vpc.yml', evpc_inputs)
    except (ClientError, WaiterError) as e:
        print_error(e.response['Error']['Message'])
        exit(1)
    except json.JSONDecodeError as e:
        print_error('Invalid JSON in --stack-inputs.')
        exit(1)
    except KeyError as e:
        missing_key = e.args[0]
        print_error('Missing key \'{0}\' in --stack-inputs.'.format(missing_key))
        exit(1)
    except:
        print_error('An unexpected error occurred')
        traceback.print_exc()
        exit(1)
    else:
        print_success()

    return tg_stack_id, evpc_stack_id

def post_cfn(tg_stack_id, evpc_stack_id):
    tg_stack = _cfn_resource.Stack(tg_stack_id) # pylint: disable=no-member
    evpc_stack = _cfn_resource.Stack(evpc_stack_id) # pylint: disable=no-member

    try:
        tg_stack_properties = transform_aws_to_dict(tg_stack.outputs)
        evpc_stack_properties = transform_aws_to_dict(evpc_stack.outputs)
    except ClientError as e:
        print_error(e.response['Error']['Message'])
        exit(1)
    except:
        print_error('An unexpected error occurred')
        traceback.print_exc()
        exit(1)

    # Pull out specific values from stack outputs
    tg_id = tg_stack_properties['TransitGateway']
    ingress_rt_id = tg_stack_properties['IngressTransitGatewayRouteTable']
    egress_rt_id = tg_stack_properties['EgressTransitGatewayRouteTable']
    tg_vpc_attachment = evpc_stack_properties['TransitGatewayAttachment']

    # Pick out the properties for each gateway from the Transit Gateway
    # stack properties
    gateway_properties = extract_gateway_props(tg_stack_properties)
    map_attachments_to_vpns(gateway_properties, tg_id)

    # Use the gateway properties to tag and associate VPN attachments
    print('Tagging VPN attachments... ', end='')
    try:
        tag_vpn_attachments(gateway_properties)
    except ClientError as e:
        print_error(e.response['Error']['Message'])
        exit(1)
    except:
        print_error('An unknown error occurred')
        exit(1)
    else:
        print_success()

    print('Associating VPN attachments with the Egress Transit Gateway route table... ', end='')
    try:
        associate_vpn_attachments(gateway_properties, egress_rt_id)
    except ClientError as e:
        print_error(e.response['Error']['Message'])
        exit(1)
    except:
        print_error('An unknown error occurred')
        exit(1)
    else:
        print_success()

    print('Associating Egress VPC attachment with Ingress Transit Gateway route table... ', end='')
    try:
        _ec2.associate_transit_gateway_route_table(
            TransitGatewayRouteTableId=ingress_rt_id,
            TransitGatewayAttachmentId=tg_vpc_attachment
        )
    except ClientError as err:
        if err.response['Error']['Code'] != 'Resource.AlreadyAssociated':
            print_error(err.response['Error']['Message'])
            exit(1)
    else:
        print_success()

    print('Done.')

def create_stack_skeleton():
    skeleton = {
        'StackName': '',
        'Parameters': [
            {
                'ParameterKey': '',
                'ParameterValue': ''
            }
        ]
    }

    return json.dumps(skeleton, indent=2)

def create_routes_skeleton():
    skeleton = {
        'vpn-0123456abcde': [],
        'vpn-1234567bcdef': [],
        'vpn-2345678cdefg': []
    }

    return json.dumps(skeleton, indent=2)

def create_routes_for_gateways(tg_stack_id, evpc_stack_id, route_input_json):
    """Create routes in the Transit Gateway and the Egress VPC for each VPN
    connection

    Arguments:
        tg_stack_id {string} -- The ID of the Transit Gateway stack
        evpc_stack_id {string} -- The ID of the Egress VPC stack
        route_inputs {dict} -- A dict mapping VPN connections to CIDR ranges
    """
    tg_stack = _cfn_resource.Stack(tg_stack_id)     # pylint: disable=no-member
    evpc_stack = _cfn_resource.Stack(evpc_stack_id) # pylint: disable=no-member

    try:
        tg_stack_outputs = transform_aws_to_dict(tg_stack.outputs)
        evpc_stack_outputs = transform_aws_to_dict(evpc_stack.outputs)
    except ClientError as e:
        print_error(e.response['Error']['Message'])
        exit(1)
    except:
        print_error('An unexpected error occurred')
        traceback.print_exc()
        exit(1)

    # Pull out specific values from stack outputs
    tg_id = tg_stack_outputs['TransitGateway']
    egress_tg_rt_id = tg_stack_outputs['EgressTransitGatewayRouteTable']
    ingress_tg_rt_id = tg_stack_outputs['IngressTransitGatewayRouteTable']
    tg_vpc_attachment = evpc_stack_outputs['TransitGatewayAttachment']
    evpc_public_rt = evpc_stack_outputs['PublicSubnetRouteTable']
    evpc_private_rt = evpc_stack_outputs['PrivateSubnetRouteTable']

    # Create the default 0.0.0.0/0 route in the Ingress Transit Gateway
    # route table
    print('Creating default route to Egress VPC in Egress Transit Gateway route table... ', end='')
    try:
        _ec2.create_transit_gateway_route(
            DestinationCidrBlock='0.0.0.0/0',
            TransitGatewayRouteTableId=egress_tg_rt_id,
            TransitGatewayAttachmentId=tg_vpc_attachment,
            Blackhole=False
        )
    except ClientError as e:
        if e.response['Error']['Code'] != 'RouteAlreadyExists':
            print_error(e.response['Error']['Message'])
            exit(1)

    print_success()

    print('Creating return routes to VPN connections in the Ingress Transit Gateway route table... ', end='')
    try:
        route_inputs = json.JSONDecoder().decode(route_input_json)
    except json.JSONDecodeError as e:
        print_error('Invalid JSON in --route-inputs.')
        exit(1)
    else:
        print('')

    # Match the VPN connection ID keys provided to the user to the IDs
    # returned by describing the Transit Gateway attachments.
    tg_attachments = _ec2.describe_transit_gateway_attachments(
        Filters=[{'Name': 'transit-gateway-id', 'Values': [tg_id]}]
    )['TransitGatewayAttachments']

    keys_from_describe = set([
        item['ResourceId']
        for item in tg_attachments
        if item['ResourceType'] == 'vpn'
    ])
    user_keys = set(route_inputs.keys())
    matching_keys = user_keys & keys_from_describe

    # Create routes for each VPN in the Ingress Transit Gateway route table
    for key in user_keys:
        for item in tg_attachments:
            if item['ResourceId'] == key:
                attachment = item['TransitGatewayAttachmentId']

        for cidr in route_inputs[key]:
            print('\tCreating route {0} to {1}... '.format(cidr, color(key, fg='magenta')), end='')
            if key in matching_keys:
                try:
                    _ec2.create_transit_gateway_route(
                        DestinationCidrBlock=cidr,
                        TransitGatewayRouteTableId=ingress_tg_rt_id,
                        TransitGatewayAttachmentId=attachment,
                        Blackhole=False
                    )
                except ClientError as e:
                    if e.response['Error']['Code'] != 'RouteAlreadyExists':
                        print_error(e.response['Error']['Message'])
                        exit(1)

                print_success()
            else:
                print(color('skipped!', fg='cyan') + ' The VPN connection does not exist.')

    # Create routes for each gateway in the Egress VPC public route table
    print('Creating return routes to the Transit Gateway in the Egress VPC public route table... ')
    for key in user_keys:
        for cidr in route_inputs[key]:
            print('\tCreating route {0} to {1}... '.format(cidr, color(tg_id, fg='magenta')), end='')
            if key in matching_keys:
                try:
                    _ec2.create_route(
                        DestinationCidrBlock=cidr,
                        RouteTableId=evpc_public_rt,
                        TransitGatewayId=tg_id
                    )
                except ClientError as e:
                    if e.response['Error']['Code'] != 'RouteAlreadyExists':
                        print_error(e.response['Error']['Message'])
                        exit(1)

                print_success()
            else:
                print(color('skipped!', fg='cyan') + ' The VPN connection does not exist.')

    # Create routes for each gateway in the Egress VPC private route table
    print('Creating return routes to the Transit Gateway in the Egress VPC private route table... ')
    for key in user_keys:
        for cidr in route_inputs[key]:
            print('\tCreating route {0} to {1}... '.format(cidr, color(tg_id, fg='magenta')), end='')
            if key in matching_keys:
                try:
                    _ec2.create_route(
                        DestinationCidrBlock=cidr,
                        RouteTableId=evpc_private_rt,
                        TransitGatewayId=tg_id
                    )
                except ClientError as e:
                    if e.response['Error']['Code'] != 'RouteAlreadyExists':
                        print_error(e.response['Error']['Message'])
                        exit(1)

                print_success()
            else:
                print(color('skipped!', fg='cyan') + ' The VPN connection does not exist.')

    print('Done.')

def delete_transit_gateway_routes(tg_rt_id):
    """Deletes all static routes from a Transit Gateway route table

    Arguments:
        tg_rt_id {string} -- The ID of a Transit Gateway route table
    """
    routes = _ec2.search_transit_gateway_routes(
        TransitGatewayRouteTableId=tg_rt_id,
        Filters=[{'Name': 'type', 'Values': ['static']}]
    )['Routes']

    for route in routes:
        cidr = route['DestinationCidrBlock']
        print('\tDeleting route {0}... '.format(color(cidr, fg='magenta')), end='')
        _ec2.delete_transit_gateway_route(
            TransitGatewayRouteTableId=tg_rt_id,
            DestinationCidrBlock=cidr
        )
        print_success()

def delete_vpc_routes(tg_id, vpc_rt_id):
    """Deletes all Transit Gateway routes from a VPC subnet route table

    Arguments:
        tg_id {string} -- The ID of a Transit Gateway
        vpc_rt_id {string} -- The ID of a VPC subnet route table
    """
    routes = _ec2.describe_route_tables(
        RouteTableIds=[vpc_rt_id]
    )['RouteTables'][0]['Routes']

    tg_routes = filter(
        lambda item: 'TransitGatewayId' in item and item['TransitGatewayId'] == tg_id,
        routes
    )

    for route in tg_routes:
        cidr = route['DestinationCidrBlock']
        print('\tDeleting route {0}... '.format(color(cidr, fg='magenta')), end='')
        _ec2.delete_route(
            RouteTableId=vpc_rt_id,
            DestinationCidrBlock=cidr
        )
        print_success()

def delete_all_routes(tg_stack_id, evpc_stack_id):
    """Delete all routes from the Transit Gateway route tables and the
    Transit Gateway routes from the Egress VPC public subnet

    Arguments:
        tg_stack_id {string} -- The ID of the Transit Gateway stack
        evpc_stack_id {string} -- The ID of the Egress VPC stack
    """
    tg_stack = _cfn_resource.Stack(tg_stack_id)     # pylint: disable=no-member
    evpc_stack = _cfn_resource.Stack(evpc_stack_id) # pylint: disable=no-member

    try:
        tg_stack_outputs = transform_aws_to_dict(tg_stack.outputs)
        evpc_stack_outputs = transform_aws_to_dict(evpc_stack.outputs)
    except ClientError as e:
        print_error(e.response['Error']['Message'])
        exit(1)
    except:
        print_error('An unexpected error occurred')
        traceback.print_exc()
        exit(1)

    tg_id = tg_stack_outputs['TransitGateway']
    ingress_tg_rt_id = tg_stack_outputs['IngressTransitGatewayRouteTable']
    egress_tg_rt_id = tg_stack_outputs['EgressTransitGatewayRouteTable']
    evpc_public_rt = evpc_stack_outputs['PublicSubnetRouteTable']
    evpc_private_rt = evpc_stack_outputs['PrivateSubnetRouteTable']

    # Delete all routes from the Ingress and Egress Transit Gateway route tables
    print('Deleting routes in the Ingress Transit Gateway route table...')
    try:
        delete_transit_gateway_routes(ingress_tg_rt_id)
    except ClientError as e:
        print_error(e.response['Error']['Message'])
        exit(1)
    except:
        print_error('An unexpected error occurred')
        traceback.print_exc()
        exit(1)

    print('Deleting routes in the Egress Transit Gateway route table...')
    try:
        delete_transit_gateway_routes(egress_tg_rt_id)
    except ClientError as e:
        print_error(e.response['Error']['Message'])
        exit(1)
    except:
        print_error('An unexpected error occurred')
        traceback.print_exc()
        exit(1)

    # Delete routes associated with the Transit Gateway from the Egress VPC
    # public route table
    print('Deleting Transit Gateway routes in the Egress VPC public subnet... ')
    try:
        delete_vpc_routes(tg_id, evpc_public_rt)
    except ClientError as e:
        print_error(e.response['Error']['Message'])
        exit(1)
    except:
        print_error('An unexpected error occurred')
        traceback.print_exc()
        exit(1)

    # Delete routes associated with the Transit Gateway from the Egress VPC
    # private route table
    print('Deleting Transit Gateway routes in the Egress VPC private subnet... ')
    try:
        delete_vpc_routes(tg_id, evpc_private_rt)
    except ClientError as e:
        print_error(e.response['Error']['Message'])
        exit(1)
    except:
        print_error('An unexpected error occurred')
        traceback.print_exc()
        exit(1)

    print('Done.')
