import pytest
import boto3
import random
import string

import certs
from iot_core import register_thing, remove_thing

iot = boto3.client("iot")


class TestIotCore:
    @pytest.fixture
    def random_suffix(self):
        chars = string.digits + string.ascii_uppercase
        return "".join(random.choice(chars) for i in range(0, 12))

    @pytest.fixture
    def thing_name(self, random_suffix):
        return f"test_thing_{random_suffix}".upper()

    @pytest.fixture
    def cert_id(self):
        cert = certs.Certificate()
        cert.create()
        yield cert.id
        cert.delete()

    def test_register_thing(self, thing_name, cert_id):
        register_thing(thing_name, cert_id)

        # the thing exists
        iot.describe_thing(thingName=thing_name)

        # the cert exists
        cert = iot.describe_certificate(certificateId=cert_id)["certificateDescription"]
        cert_arn = cert["certificateArn"]

        # the thing is attached to the cert
        principals = iot.list_principal_things(principal=cert_arn)["things"]
        assert thing_name in principals, "thing is not attached to certificate"

        # the policy is attached to the cert
        policies = iot.list_attached_policies(target=cert_arn)["policies"]
        matches = list(
            filter(lambda p: p["policyName"] == f"{thing_name}_CertPolicy", policies)
        )
        assert len(matches) == 1, "policy is not attached to certificate"

        policy = matches[0]

        # cleanup
        iot.detach_thing_principal(thingName=thing_name, principal=cert_arn)
        iot.delete_thing(thingName=thing_name)
        iot.detach_policy(policyName=policy["policyName"], target=cert_arn)
        iot.delete_policy(policyName=policy["policyName"])

    def test_remove_thing(self, thing_name, cert_id):
        register_thing(thing_name, cert_id)
        remove_thing(thing_name, cert_id)

        # thing is deleted
        with pytest.raises(iot.exceptions.ResourceNotFoundException):
            iot.describe_thing(thingName=thing_name)

        # policy is deleted
        with pytest.raises(iot.exceptions.ResourceNotFoundException):
            iot.get_policy(policyName=f"{thing_name}_CertPolicy")
