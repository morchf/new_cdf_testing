#!/usr/bin/env python

import boto3
import json
import os


class Policy():
    def __init__(self, thing_name, policy_text=''):
        self.policy_name = thing_name + '_' + 'CertPolicy'
        self.policy_text = policy_text
        self.client = boto3.client('iot')

    def create(self):
        assert self.exists() == False, "Policy already exists"
        try:
            self.client.create_policy(policyName=self.policy_name,
                policyDocument=self.policy_text)
        except Exception as e:
            print('Policy create exception: {}'.format(str(e)))
            return None
        policy_file = open(self.policy_name + '.json','w')
        policy_file.write(self.policy_text)
        policy_file.close()
        return self.policy_name

    def delete(self):
        assert self.exists() == True, "Policy does not exist, cannot be deleted"
        try: 
            self.client.delete_policy(policyName=self.policy_name)
        except Exception as e:
            print('Policy delete exception: {}'.format(str(e)))
        try:
            os.remove(self.policy_name + '.json')
        except Exception as e:
            print('Policy delete file exception: {}'.format(str(e)))

    def exists(self):
        policies = self.client.list_policies()['policies']
        for policy in policies:
            if self.policy_name == policy['policyName']:
                return True
        return False
