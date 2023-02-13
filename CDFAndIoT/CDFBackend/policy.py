#!/usr/bin/env python

import boto3


class Policy:
    def __init__(self, thing_name, policy_text=""):
        self.policy_name = thing_name + "_" + "CertPolicy"
        self.policy_text = policy_text
        self.client = boto3.client("iot")

    def create(self):
        assert not self.exists(), "Policy already exists"
        try:
            self.client.create_policy(
                policyName=self.policy_name, policyDocument=self.policy_text
            )
        except Exception as e:
            print("Policy create exception: {}".format(str(e)))
            return None
        return self.policy_name

    def delete(self):
        assert self.exists(), "Policy does not exist, cannot be deleted"

        try:
            rc = self.client.delete_policy(policyName=self.policy_name)
        except Exception as e:
            rc = e
            print(f"Policy delete exception: {str(e)}")

        return rc

    def exists(self):
        try:
            self.client.get_policy(policyName=self.policy_name)
            return True
        except Exception as e:
            print(f"Policy exists exception: {str(e)}")
            return False
