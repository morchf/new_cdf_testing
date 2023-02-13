#!/usr/bin/env python3
'''
This file is not part of the normal CDF distribution. 

This file deletes the CDF stacks. Without this program, all of the 10+ stacks have to be deleted manually. 

Additionally, the cdf_network_stage stack does not delete cleaning. The successful manual sequence to delete 
cdf_network_stack is to:
1. delete cdf_network_stack
2. Wait for a delete failure.
3. Look up the IP subnets that are the source of the delete failure
4. Delete the IP subnets
5. delete the cdf_network_stack again

This file deletes all the cdf stacks and prints the ipsubnets of cdf_network_stack to help facilitate 
the process of deleting cdf stacks..

No longer is manual deltion of CF stacks needed with this program. The process is:
    1. run "python cdf_delete_stacks.py"
    2. run "python cdf_delete_stacks.py" again every few minutes
    4. Wait for cdf_network_stack to indicate "DELETE_FAILED"
    5. Look at ipsubnets from cdf_network_stack then manually delete the listed subnet(s) in aws console
    6. run "python cdf_delete_stacks.py" again
'''

import boto3
import os

def main():
    print('Do you really want to stop all CDF cloud formation stacks? Answer Upper case YES, if true.')
    answer = input()
    if answer == "YES" :
        client = boto3.client('cloudformation', region_name='us-west-2')

        stack_info = {}
        list_stacks = client.list_stacks()
        for stackSummary in list_stacks.get('StackSummaries', None):
            stackName = stackSummary.get('StackName', None)
            stackStatus = stackSummary.get('StackStatus', None)
            if 'cdf-' in stackName :
                if stackName == 'cdf-network-stage' and stackStatus == 'DELETE_IN_PROGRESS':
                    print(stackName)
                    resourceSummaries = client.list_stack_resources(StackName=stackName)
                    resourceList = resourceSummaries['StackResourceSummaries']
                    for resource in resourceList:
                        resourceId = resource['LogicalResourceId']
                        if 'PrivateSubnetOne' == resourceId or 'PrivateSubnetTwo' == resourceId:

                            rid = resource['PhysicalResourceId']
                            print('\t', resourceId, rid)
                if stackStatus in stack_info:
                    stacks = stack_info[stackStatus]
                    stacks.append(stackName)
                    stack_info.update({stackStatus:stacks})
                else:
                    stacks = []
                    stacks.append(stackName)
                    stack_info[stackStatus] = stacks

        for stackStatus, stacks in stack_info.items():
            if stackStatus != 'DELETE_COMPLETE':
                print(stackStatus)
                for stackName in stacks:
                    print('\t',stackName)
                    if stackStatus == 'UPDATE_ROLLBACK_COMPLETE' or stackStatus == 'UPDATE_COMPLETE' or stackStatus == 'CREATE_COMPLETE' or stackStatus == 'DELETE_FAILED':
                        client.delete_stack(StackName=stackName)

'''
StackName='string',
RoleARN='string',
ClientRequestToken='string'
'''

if __name__ == "__main__":
    main()
