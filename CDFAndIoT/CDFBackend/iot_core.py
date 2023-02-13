#!/usr/bin/env python

import certs
import policy
import thing
import misc

log = True


def register_thing(name, certId):
    try:
        name = name.upper()
        cert_obj = certs.Certificate(certId)
        thing_obj = thing.Thing(name)
        thing_obj.create()
        policy_document_text = misc.create_policy_document_text(name)
        policy_obj = policy.Policy(name, policy_document_text)

        cert_policy_name = policy_obj.create()
        cert_obj.attach_policy(cert_policy_name)
        cert_obj.attach_thing(name)
    except Exception as e:
        if log:
            print(f"thing create IoT Core exception = {str(e)}")
        pass


def remove_thing(name, certId):
    try:
        name = name.upper()
        cert_obj = certs.Certificate(certId)
        print("certId is: " + certId)
        thing_obj = thing.Thing(name)
        policy_obj = policy.Policy(name, "")
        print("policy_obj.policy_name is: " + policy_obj.policy_name)
        cert_obj.detach_thing(name)
        thing_obj.delete()
        cert_obj.detach_policy(policy_obj.policy_name)
        policy_obj.delete()
    except Exception as e:
        if log:
            print(f"device delete IoT Core exception = {str(e)}")
        pass
