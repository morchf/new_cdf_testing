import boto3
import pytest
import random
import string

from certs import Certificate

iot = boto3.client("iot")


class TestCerts:
    @pytest.fixture
    def random_suffix(self):
        chars = string.digits + string.ascii_uppercase
        return "".join(random.choice(chars) for i in range(0, 12))

    @pytest.fixture
    def policy_data(self, random_suffix):
        policy = iot.create_policy(
            policyName=f"test_policy_{random_suffix}",
            policyDocument="""{
        "Version": "2012-10-17",
        "Statement": [
          {
            "Effect": "Allow",
            "Action": "iot:Connect",
            "Resource": "*"
          }
        ]
      }""",
        )
        yield policy
        iot.delete_policy(policyName=policy["policyName"])

    @pytest.fixture
    def thing_data(self, random_suffix):
        thing = iot.create_thing(thingName=f"test_thing_{random_suffix}")
        yield thing
        iot.delete_thing(thingName=thing["thingName"])

    @pytest.fixture
    def cert_data(self):
        cert = iot.create_keys_and_certificate(setAsActive=True)
        cert_arn = cert["certificateArn"]
        cert_id = cert["certificateId"]

        yield cert

        cert_things = iot.list_principal_things(principal=cert_arn)["things"]
        for thing in cert_things:
            iot.detach_thing_principal(thingName=thing, principal=cert_arn)

        cert_policies = iot.list_attached_policies(target=cert_arn)["policies"]
        for policy in cert_policies:
            iot.detach_policy(policyName=policy["policyName"], target=cert_arn)

        iot.update_certificate(certificateId=cert_id, newStatus="INACTIVE")
        iot.delete_certificate(certificateId=cert_id)

    @pytest.fixture
    def cert(self, cert_data):
        return Certificate(cert_data["certificateId"])

    @pytest.fixture
    def empty_cert(self):
        return Certificate("")

    def policy_attached_to_cert(self, policy_name, cert_arn):
        found = False
        policies = iot.list_attached_policies(target=cert_arn)["policies"]
        for policy in policies:
            if policy["policyName"] == policy_name:
                found = True

        return found

    def thing_attached_to_cert(self, thing_name, cert_arn):
        things = iot.list_principal_things(principal=cert_arn)["things"]
        return thing_name in things

    def test_constructor(self, empty_cert):
        assert empty_cert.id == ""
        assert empty_cert.arn == ""
        assert not empty_cert.exists()

    def test_constructor_already_exists(self, cert, cert_data):
        assert cert.id == cert_data["certificateId"]
        assert cert.arn == cert_data["certificateArn"]
        assert cert.exists()

    def test_constructor_invalid_id(self):
        random_hex = "c71417ed70f94aa523643b434f8411aebb1aa7330eb91790f3bdcf56ab2bf4b0"
        with pytest.raises(iot.exceptions.ResourceNotFoundException):
            Certificate(random_hex)

    def test_create(self, empty_cert):
        empty_cert.create()
        created_id = empty_cert.id
        expected_arn = empty_cert.arn
        cert = iot.describe_certificate(certificateId=created_id)[
            "certificateDescription"
        ]

        assert cert["certificateArn"] == expected_arn
        assert cert["status"] == "ACTIVE"

        # cleanup
        iot.update_certificate(certificateId=created_id, newStatus="INACTIVE")
        iot.delete_certificate(certificateId=created_id)

    def test_delete(self, policy_data, thing_data):
        cert = Certificate("")
        cert.create()
        cert.attach_thing(thing_data["thingName"])
        cert.attach_policy(policy_data["policyName"])

        cert.delete()

        with pytest.raises(iot.exceptions.ResourceNotFoundException):
            iot.describe_certificate(certificateId=cert.id)

    def test_exists(self, empty_cert):
        assert not empty_cert.exists()
        empty_cert.create()
        assert empty_cert.exists()

        # cleanup
        iot.update_certificate(certificateId=empty_cert.id, newStatus="INACTIVE")
        iot.delete_certificate(certificateId=empty_cert.id)

    def test_get_arn(self, cert, cert_data):
        assert cert.get_arn() == cert_data["certificateArn"]

    def test_list_policies(self, policy_data, cert):
        iot.attach_policy(policyName=policy_data["policyName"], target=cert.get_arn())
        expected_policies = iot.list_attached_policies(target=cert.get_arn())[
            "policies"
        ]
        actual_policies = cert.list_policies()

        assert actual_policies == expected_policies

    def test_attach_policy(self, policy_data, cert):
        policy_name = policy_data["policyName"]
        cert_arn = cert.get_arn()

        assert not self.policy_attached_to_cert(policy_name, cert_arn)
        cert.attach_policy(policy_name)
        assert self.policy_attached_to_cert(policy_name, cert_arn)

    def test_detach_policy(self, policy_data, cert):
        policy_name = policy_data["policyName"]
        cert_arn = cert.get_arn()

        iot.attach_policy(policyName=policy_name, target=cert_arn)
        assert self.policy_attached_to_cert(policy_name, cert_arn)
        cert.detach_policy(policy_name)
        assert not self.policy_attached_to_cert(policy_name, cert_arn)

    def test_list_things(self, thing_data, cert):
        thing_name = thing_data["thingName"]
        cert_arn = cert.get_arn()

        iot.attach_thing_principal(thingName=thing_name, principal=cert_arn)
        expected_things = iot.list_principal_things(principal=cert_arn)["things"]
        actual_things = cert.list_things()
        assert actual_things == expected_things

    def test_attach_thing(self, thing_data, cert):
        thing_name = thing_data["thingName"]
        cert_arn = cert.get_arn()

        assert not self.thing_attached_to_cert(thing_name, cert_arn)
        cert.attach_thing(thing_name)
        assert self.thing_attached_to_cert(thing_name, cert_arn)

    def test_detach_thing(self, thing_data, cert):
        thing_name = thing_data["thingName"]
        cert_arn = cert.get_arn()

        iot.attach_thing_principal(thingName=thing_name, principal=cert_arn)
        assert self.thing_attached_to_cert(thing_name, cert_arn)
        cert.detach_thing(thing_name)
        assert not self.thing_attached_to_cert(thing_name, cert_arn)
