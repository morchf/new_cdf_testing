import os
import pytest


def test_cdf_creation(upload_file):
    # call the upload_file fixture in conftest.py which returns a list
    # containing upload status, status[4] and the cdf api response json, status[0]
    status = upload_file(operation_type="create")
    if not status[4]:
        pytest.fail("Upload of the test file to the cdf bucket failed")

    if "error" in status[0]:
        pytest.fail(status[0]["error"])

    # check if created deviceId matches deviceId passed in from conftest.py
    # and if device has been assigned a certId
    if "results" in status[0]:
        assert status[0]["results"][0]["deviceId"] == status[1]
        assert len(status[0]["results"][0]["attributes"]["devCertId"]) == 64


def test_agency_has_certs(cert_check):

    if "error" in cert_check:
        pytest.fail(
            cert_check["error"]
            + ". \nEither the agency does not exist or you entered the region or agency name incorrectly."
        )

    if "attributes" in cert_check:
        if (
            cert_check["attributes"]["caCertId"] == "NULL_CA"
            or cert_check["attributes"]["vpsCertId"] == "NULL_CERT"
        ):

            pytest.fail(
                f'\nThis agency does not have a caCertId attached. Current caCert value is: "{cert_check["attributes"]["caCertId"]}".'
                + f'\nThis agency does not have a vpsCertId attached. Current vpsCert value is: "{cert_check["attributes"]["vpsCertId"]}".'
            )

        if (
            cert_check["attributes"]["caCertId"] != "NULL_CA"
            and cert_check["attributes"]["vpsCertId"] != "NULL_CERT"
        ):
            print(
                f'\nThis agency\'s current caCert value is: "{cert_check["attributes"]["caCertId"]}".'
                + f'\nThis agency\'s current vpsCert value is: "{cert_check["attributes"]["vpsCertId"]}".'
            )

        assert len(cert_check["attributes"]["caCertId"]) == 64
        assert len(cert_check["attributes"]["vpsCertId"]) == 64


def test_agency_has_caCert(cert_check):
    if "error" in cert_check:
        pytest.fail(
            cert_check["error"]
            + ". \nEither the agency does not exist or you entered the region or agency name incorrectly."
        )

    if "attributes" in cert_check:
        if cert_check["attributes"]["caCertId"] == "NULL_CA":
            pytest.fail(
                f'\nThis agency does not have a caCertId attached. Current caCert value is: "{cert_check["attributes"]["caCertId"]}".'
            )

        if cert_check["attributes"]["caCertId"] != "NULL_CA":
            print(
                f'\nThis agency\'s current caCert value is: "{cert_check["attributes"]["caCertId"]}".'
            )

        assert len(cert_check["attributes"]["caCertId"]) == 64


def test_agency_has_vpsCert(cert_check):
    if "error" in cert_check:
        pytest.fail(
            cert_check["error"]
            + ". \nEither the agency does not exist or you entered the region or agency name incorrectly."
        )

    if "attributes" in cert_check:
        if cert_check["attributes"]["vpsCertId"] == "NULL_CERT":
            pytest.fail(
                f'\nThis agency does not have a vpsCertId attached. Current vpsCert value is: "{cert_check["attributes"]["vpsCertId"]}".'
            )

        if cert_check["attributes"]["vpsCertId"] != "NULL_CERT":
            print(
                f'\nThis agency\'s current vpsCert value is: "{cert_check["attributes"]["vpsCertId"]}".'
            )

        assert len(cert_check["attributes"]["vpsCertId"]) == 64


def test_cdf_deletion(upload_file):
    # call the upload_file fixture in conftest.py which returns a list
    # containing upload status, status[4] and the cdf api response json, status[0]
    status = upload_file(operation_type="delete")
    if not status[4]:
        pytest.fail("Upload of the test file to the cdf bucket failed")

    if "error" in status[0]:
        pytest.fail(status["error"])

    # check if result set is empty. if it is, then delete was successful
    if "results" in status[0]:
        assert status[0]["results"] == []

