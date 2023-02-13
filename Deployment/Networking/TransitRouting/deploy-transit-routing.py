#!/usr/bin/env python3
"""This script exists because CloudFormation support for Transit Gateway and
VPN connection attachments is currently spotty: it can't tag VPN attachments
or associate VPN attachments with a TG route table.

The term "gateway" refers to a Customer Gateway for a Site-to-Site VPN in
AWS. The stack associated with this script accepts up to 4 gateways as
parameters named A, B, C, and D. The letter associated with the gateway
will be referred to as the "ID" for the gateway in this script.

Gateway A is always present, but B-D are optional.

See the deployutils module for implementation details.
"""

import click
from deployutils import (initialize_boto,
                         pre_cfn,
                         post_cfn,
                         create_stack_skeleton,
                         create_routes_skeleton,
                         create_routes_for_gateways,
                         delete_all_routes)

@click.group()
def cli():
    pass

@cli.command(help='Output a JSON skeleton for a command that accepts JSON as input.')
@click.argument('skeleton-type', type=click.Choice(['create-stacks', 'create-routes']))
def create_json_skeleton(skeleton_type):
    if skeleton_type == 'create-stacks':
        print(create_stack_skeleton())
    elif skeleton_type == 'create-routes':
        print(create_routes_skeleton())

@cli.command(help='Create Transit Gateway and Egress VPC stacks, then run post-create actions.')
@click.option('--tg-stack-inputs', required=True, help='JSON-formatted stack inputs.')
@click.option('--evpc-stack-inputs', required=True, help='JSON-formatted stack inputs.')
def create_stacks(tg_stack_inputs, evpc_stack_inputs):
    initialize_boto()
    tg_stack_id, evpc_stack_id = pre_cfn(tg_stack_inputs, evpc_stack_inputs)
    post_cfn(tg_stack_id, evpc_stack_id)

@cli.command(help='Run post-create actions on existing stacks.')
@click.option('--tg-stack-id', required=True, help='Transit Gateway stack ID.')
@click.option('--evpc-stack-id', required=True, help='Egress VPC stack ID.')
def run_post_actions(tg_stack_id, evpc_stack_id):
    initialize_boto()
    post_cfn(tg_stack_id, evpc_stack_id)

@cli.command(help='Create routes for each Gateway attached to the Transit Gateway')
@click.option('--tg-stack-id', required=True, help='Transit Gateway stack ID')
@click.option('--evpc-stack-id', required=True, help='Egress VPC stack ID')
@click.option('--route-inputs', required=True, help='Routes to create for each Gateway')
def create_routes(tg_stack_id, evpc_stack_id, route_inputs):
    initialize_boto()
    create_routes_for_gateways(tg_stack_id, evpc_stack_id, route_inputs)

@cli.command(help='Delete routes from the Transit Gateway and the Egress VPC route tables')
@click.option('--tg-stack-id', required=True, help='Transit Gateway stack ID')
@click.option('--evpc-stack-id', required=True, help='Egress VPC stack ID')
def delete_routes(tg_stack_id, evpc_stack_id):
    initialize_boto()
    delete_all_routes(tg_stack_id, evpc_stack_id)

if __name__ == '__main__':
    cli()
