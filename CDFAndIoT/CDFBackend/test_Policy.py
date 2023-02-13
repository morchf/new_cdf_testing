import boto3
import pytest
import random
import string

from policy import Policy

iot = boto3.client("iot")


class TestPolicy:
    @pytest.fixture
    def random_suffix(self):
        chars = string.digits + string.ascii_uppercase
        return "".join(random.choice(chars) for i in range(0, 12))

    @pytest.fixture
    def thing_name(self, random_suffix):
        return f"thing_name_{random_suffix}"

    @pytest.fixture
    def policy_document(self):
        return """{
        "Version": "2012-10-17",
        "Statement": [
          {
            "Effect": "Allow",
            "Action": "iot:Connect",
            "Resource": "*"
          }
        ]
      }"""

    @pytest.fixture
    def policy(self, thing_name, policy_document):
        return Policy(thing_name, policy_document)

    def test_constructor_policy(self, thing_name, policy_document):
        policy = Policy(thing_name, policy_document)
        assert policy.policy_name == f"{thing_name}_CertPolicy"
        assert policy.policy_text == policy_document

    def test_constructor_no_policy(self, thing_name):
        policy = Policy(thing_name)
        assert policy.policy_name == f"{thing_name}_CertPolicy"
        assert policy.policy_text == ""

    def test_create_new(self, thing_name, policy):
        with pytest.raises(iot.exceptions.ResourceNotFoundException):
            iot.get_policy(policyName=policy.policy_name)

        policy_name = policy.create()
        actual_policy = iot.get_policy(policyName=policy_name)
        assert actual_policy["policyDocument"] == policy.policy_text

        iot.delete_policy(policyName=policy.policy_name)

    def test_create_empty(self, thing_name):
        policy = Policy(thing_name)  # default empty policy document
        assert policy.create() is None

    def test_create_exists(self, thing_name, policy_document, policy):
        iot.create_policy(
            policyName=f"{thing_name}_CertPolicy", policyDocument=policy_document
        )

        # cannot create if policy already exists
        with pytest.raises(AssertionError):
            policy.create()

        iot.delete_policy(policyName=policy.policy_name)

    def test_delete(self, policy):
        iot.create_policy(
            policyName=policy.policy_name, policyDocument=policy.policy_text
        )

        policy.delete()

        with pytest.raises(iot.exceptions.ResourceNotFoundException):
            iot.get_policy(policyName=policy.policy_name)

    def test_delete_not_exists(self, policy):
        with pytest.raises(iot.exceptions.ResourceNotFoundException):
            iot.get_policy(policyName=policy.policy_name)

        # cannot delete if policy doesn't exist
        with pytest.raises(AssertionError):
            policy.delete()

    def test_exists(self, policy):
        assert not policy.exists()
        policy.create()
        assert policy.exists()
        iot.delete_policy(policyName=policy.policy_name)
        assert not policy.exists()
