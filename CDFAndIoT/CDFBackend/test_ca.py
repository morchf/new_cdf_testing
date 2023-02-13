"""
    test_ca.py provides a test frame work for aws_cert_auth.py.
    One test includes sending MQTT messages to AWS IoT Core using
    mqtt_client.py with pre-defined values on config.py.
    Note that each function is it's own test case. The order of
    execution of particular tests cannot be controlled; therefore,
    each test is inclusive within itself. Everything needed for
    a test is generated and then deleted if the test completes
    successfully.
"""
import pytest
import os
from aws_cert_auth import (
    generate_key,
    generate_iot_registration_code,
    update_configuration_file,
    store_cert_data_as_zip,
    delete_zip_data,
    new_root_ca,
    del_root_ca,
    new_sub_ca,
    del_sub_ca,
    new_dev,
    del_dev,
    get_cert_id,
    get_cert_data,
    entity_clean_up,
    validate_cert_length,
)
import misc
import certs
import policy
import thing
import mqtt_client

debug = True

if os.path.exists("/tmp/log.txt"):
    os.remove("/tmp/log.txt")
if os.path.exists("/tmp/err.txt"):
    os.remove("/tmp/err.txt")


@pytest.fixture(scope="function")
def entity_cleanup():
    # let test run
    yield

    # if test fails entities are not deleted
    # run deletes for entities
    del_dev("r1", "a1", "v1")
    del_sub_ca("r1", "a1")
    del_root_ca("r1")


class TestCertAuth:

    """
    Generate and delete CDF entity resources in S3 and IoT
    """

    def test_generate_key(self):
        rc = generate_key("cheese")
        assert rc == 0, f"failed generate_key() rc = {rc}"

        # clean up
        os.remove("/tmp/cheese.key")

    """
        Generate a registration code from IoT Core
    """

    def test_iot_registration_code(self):
        rc = generate_iot_registration_code()
        assert rc is not None, f"failed generate_iot_registration_code() rc = {rc}"

    """
        Register CA with IoT Core
    """

    def test_register_CA_in_iot_core(self):
        rc = generate_iot_registration_code()
        assert rc is not None, f"failed generate_iot_registration_code() rc = {rc}"

    """
        Register CA with IoT Core
    """

    def test_update_configuration_file(self):
        update_configuration_file("R1_ROOTCA")
        os.remove("/tmp/R1_ROOTCA_openssl.conf")

    """
        test storing cert data in S3
    """

    def test_store_cert_data_as_zip(self):
        store_cert_data_as_zip("name_name_vps", "r1")
        delete_zip_data("name_name_vps", "r1")

    """
        test no exception thrown on valid device cert
    """

    def test_validate_cert_length(self):
        with open("./TestFiles/test_device_cert.pem", "r") as file:
            pem = file.read()
        file.close()

        validate_cert_length(pem)

    """
        test removes 3 end characters from a valid device cert and
        verifies exception thrown
    """

    def test_validate_cert_length_missing_end_chars(self):
        with pytest.raises(Exception) as info:
            with open("./TestFiles/test_device_cert.pem", "r") as file:
                pem = file.read()
            file.close()

            validate_cert_length(pem[:-3])
        assert (
            str(info.value)
            == "[('PEM routines', 'get_header_and_data', 'bad end line')]"
        )

    """
        test removes 3 starting characters from a valid device cert and
        verifies exception thrown
    """

    def test_validate_cert_length_missing_starting_chars(self):
        with pytest.raises(Exception) as info:
            with open("./TestFiles/test_device_cert.pem", "r") as file:
                pem = file.read()
            file.close()

            validate_cert_length(pem[-3:])
        assert str(info.value) == "[('PEM routines', 'get_name', 'no start line')]"

    """
        Generate and delete CDF entity resources in S3 and IoT,
        first with failing to delete and then succeeding
    """

    def test_create_delete_root_ca(self, entity_cleanup):
        rc = new_root_ca("r1", False)
        assert rc, "failed new_root_ca()"
        rc = del_root_ca("r1")
        assert rc, "failed del_root_ca()"

    """
        Create root CA, create sub CA, delete sub CA, delete root CA
    """

    def test_create_root_ca_sub_ca_delete_sub_ca_root_ca(self):
        rc = new_root_ca("r1", False)
        assert rc, "failed new_root_ca()"
        rc = new_sub_ca("r1", "a1")
        assert rc, "failed new_sub_ca()"
        rc = del_sub_ca("r1", "a1")
        assert rc, "failed del_sub_ca()"
        rc = del_root_ca("r1")
        assert rc, "failed del_root_ca()"

    """
        Create root CA, create sub CA, create device cert,
        delete device cert, delete sub CA, delete root CA
    """

    def test_create_root_ca_sub_ca_device_delete_device_sub_ca_root_ca(self):
        rc = new_root_ca("r1", False)
        assert rc, "failed new_root_ca()"
        rc = new_sub_ca("r1", "a1")
        assert rc, "failed new_sub_ca()"
        rc = new_dev("r1", "a1", "v1")
        assert rc, "failed new_dev()"
        rc = del_dev("r1", "a1", "v1")
        assert rc, "failed del_dev()"
        rc = del_sub_ca("r1", "a1")
        assert rc, "failed del_sub_ca()"
        rc = del_root_ca("r1")
        assert rc, "failed del_root_ca()"

    """
        Complete Lifecycle of an agency and a device with
        verified communication to the device.
        #1. create root CA cert
        #2. create sub CA cert
        #3. create device cert
        #4. create thing
        #5. create policy
        #6. attach policy to cert
        #7. attach cert to thing
        #8. send MQTT messages
        #9. detach cert from thing and delete thing
        #10. detach policy from cert and delete policy
        #11. delete device cert
        #12. delete sub CA cert
        #13. delete root CA cert
    """

    def test_complete_lifecycle(self):
        region_name = "r1"
        agency_name = "a1"
        communicator_name = "c1"
        thing_name = agency_name.upper() + "_" + communicator_name.upper()
        ca = f"{region_name.upper()}_{agency_name.upper()}_SUBCA"
        prefixRoot = region_name.upper()
        prefix = prefixRoot + "/AGENCIES/" + agency_name.upper()
        prefixCert = prefix + "/DEVICES"

        # 1. create root CA cert
        rc = new_root_ca(region_name, False)
        assert rc, "failed new_root_ca()"

        # 2. create sub CA cert
        rc = new_sub_ca(region_name, agency_name, False)
        assert rc, "failed new_sub_ca()"

        # 3. create device cert
        rc = new_dev(region_name, agency_name, communicator_name)
        assert rc, "failed new_dev()"

        # Get certificate object based on cert_id
        thing_cert_id = get_cert_id(thing_name, prefixCert)
        print(thing_cert_id)

        cert_obj = certs.Certificate(thing_cert_id)
        if debug:
            print(f"arn = {cert_obj.arn}")
        assert cert_obj.arn != "", "cert does not exist"

        # 4. create thing
        thing_obj = thing.Thing(thing_name)
        if debug:
            print(f"thing_obj = {thing_obj}")
        assert thing_obj is not None, "did not create thing object"

        rc = thing_obj.create()
        if debug:
            print(f"thing_create rc = {rc}")
        assert rc, "did not create thing object"

        # 5. create policy
        policy_document_text = misc.create_policy_document_text(thing_name)
        if debug:
            print(f"policy text  = {policy_document_text:10}")
        assert policy_document_text is not None, "did not create policy object"

        policy_obj = policy.Policy(thing_name, policy_document_text)
        if debug:
            print(f"policy_obj = {policy_obj}")
        assert policy_obj is not None, "did not create policy object"

        cert_policy_name = policy_obj.create()
        assert cert_policy_name is not None, "did not create policy"

        # 6. attach policy to cert
        cert_obj.attach_policy(cert_policy_name)

        # 7. attach cert to thing
        cert_obj.attach_thing(thing_name)

        # Get local copies of cert and CA
        get_cert_data(thing_name, prefixCert)
        get_cert_data(ca, prefix)

        # 8. send MQTT messages
        mqtt_client.main()

        # 9. detach cert from thing and delete thing
        cert_obj.detach_thing(thing_name)

        rc = thing_obj.delete()
        if debug:
            print(f"delete thing rc = {rc}")
        assert (
            rc["ResponseMetadata"]["HTTPStatusCode"] == 200
        ), "did not delete thing object"

        # 10. detach policy from cert and delete policy
        cert_obj.detach_policy(cert_policy_name)

        rc = policy_obj.delete()
        if debug:
            print(f"detach_policy_to_cert rc = {rc}")
        assert (
            rc["ResponseMetadata"]["HTTPStatusCode"] == 200
        ), "did not delete policy object"

        # delete local cert data
        try:
            os.remove(f"{thing_name}.pem")
            os.remove(f"{thing_name}.key")
            os.remove(f"{ca}.key")
            os.remove(f"{ca}.pem")
        except Exception as e:
            print(e)
            print("failed to remove cert files")

        # 11. delete device cert
        rc = del_dev(region_name, agency_name, communicator_name)
        assert rc, "failed del_dev"

        # 12. delete sub CA cert
        rc = del_sub_ca(region_name, agency_name)
        assert rc, "failed del_sub_ca"

        # 13. delete root CA cert
        rc = del_root_ca(region_name)
        assert rc, "failed del_root_ca"

    def test_entity_clean_up(self, entity_cleanup):
        new_root_ca("r1", False)
        print("REGION DONE")
        new_sub_ca("r1", "a1", False)
        print("AGENCY DONE")
        new_dev("r1", "a1", "c1")
        print("DEVICE DONE")
        regPrefix = "R1"
        agyPrefix = regPrefix + "/AGENCIES/A1"
        devPrefix = agyPrefix + "/DEVICES"

        cu = entity_clean_up("A1_C1", devPrefix)
        assert cu
        cu = entity_clean_up("R1_A1_SUBCA", agyPrefix)
        assert cu
        cu = entity_clean_up("R1_ROOTCA", regPrefix)
        assert cu

    def test_entity_clean_up_failure(self, entity_cleanup):
        new_root_ca("r1", False)
        print("REGION DONE")
        new_sub_ca("r1", "a1", False)
        print("AGENCY DONE")
        new_dev("r1", "a1", "c1")
        print("DEVICE DONE")
        regPrefix = "R1"
        agyPrefix = regPrefix + "/AGENCIES/A1"
        devPrefix = agyPrefix + "/DEVICES"

        # attempt to delete with incorrect names
        # should fail
        cu = entity_clean_up("blah_dev36", devPrefix)
        assert not cu
        cu = entity_clean_up("blah_agy36_subCA", agyPrefix)
        assert not cu
        cu = entity_clean_up("blah_rootCA", regPrefix)
        assert not cu

        cu = entity_clean_up("A1_C1", devPrefix)
        assert cu
        cu = entity_clean_up("R1_A1_SUBCA", agyPrefix)
        assert cu
        cu = entity_clean_up("R1_ROOTCA", regPrefix)
        assert cu
