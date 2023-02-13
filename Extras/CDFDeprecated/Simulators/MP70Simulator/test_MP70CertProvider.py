import pytest
from unittest.mock import patch
import os
from MP70CertProvider import MP70CertProvider
import MP70CertProviderConfig
import re

zipfilecontent = b"PK\x03\x04\x14\x00\x00\x00\x00\x00\xc1X\xfeP\xd1<9\xb2\x11\x00\x00\x00\x11\x00\x00\x00\x08\x00\x00\x00cert.pemHello World Cert!PK\x03\x04\x14\x00\x00\x00\x00\x00\xccX\xfeP\xe1\xdd\x1c\xb6\x10\x00\x00\x00\x10\x00\x00\x00\x07\x00\x00\x00key.keyHello World Key!PK\x03\x04\x14\x00\x00\x00\x00\x00\xd9X\xfeP\x082\xbe\x9b\x14\x00\x00\x00\x14\x00\x00\x00\n\x00\x00\x00rootCA.pemHello World Root CA!PK\x01\x02\x14\x00\x14\x00\x00\x00\x00\x00\xc1X\xfeP\xd1<9\xb2\x11\x00\x00\x00\x11\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x01\x00 \x00\x00\x00\x00\x00\x00\x00cert.pemPK\x01\x02\x14\x00\x14\x00\x00\x00\x00\x00\xccX\xfeP\xe1\xdd\x1c\xb6\x10\x00\x00\x00\x10\x00\x00\x00\x07\x00\x00\x00\x00\x00\x00\x00\x01\x00 \x00\x00\x007\x00\x00\x00key.keyPK\x01\x02\x14\x00\x14\x00\x00\x00\x00\x00\xd9X\xfeP\x082\xbe\x9b\x14\x00\x00\x00\x14\x00\x00\x00\n\x00\x00\x00\x00\x00\x00\x00\x01\x00 \x00\x00\x00l\x00\x00\x00rootCA.pemPK\x05\x06\x00\x00\x00\x00\x03\x00\x03\x00\xa3\x00\x00\x00\xa8\x00\x00\x00\x00\x00"
uploaded_csvs = []
deleted_csvs = []

MP70CertProviderConfig.BACKOFF = 1
MP70CertProviderConfig.NUM_TRIES = 2
MP70CertProviderConfig.CDF_ASSETLIB_ENDPOINT = (
    # "https://fake.execute-api.us-east-1.amazonaws.com/Prod"
    "https://oo9fn5p38b.execute-api.us-east-1.amazonaws.com/Prod"
)


def mock_make_api_call(self, operation_name, kwarg):
    global uploaded_csvs
    global deleted_csvs
    if operation_name == "PutObject":
        uploaded_csvs.append(kwarg["Key"])
    if operation_name == "DeleteObject":
        deleted_csvs.append(kwarg["Key"])
    if operation_name == "GetObject":

        class mock_read:
            def read(self):
                return zipfilecontent

        return {"Body": mock_read()}
    return None


def mock_make_api_call_error(self, operation_name, kwarg):
    raise ConnectionError("")


def mock_make_requests_call(method, url, **kwargs):
    class mock_request:
        text = {}
        status_code = 404
        content = zipfilecontent

    return mock_request()


def mock_make_requests_call_error(method, url, **kwargs):
    raise ConnectionError("")


def mock_does_region_exist(region_name):
    return False


def mock_does_agency_exist(region_name, agency_name):
    return False


def mock_does_vehicle_exist(vehicle_name):
    return False


def setup_cert_provider():
    cp = MP70CertProvider(logging=True)
    cp.__does_region_exist_cdf__ = mock_does_region_exist
    cp.__does_agency_exist_cdf__ = mock_does_agency_exist
    cp.__does_vehicle_exist_cdf__ = mock_does_vehicle_exist
    return cp


def test_close():
    global uploaded_csvs
    global deleted_csvs
    uploaded_csvs, deleted_csvs = [], []
    exampleVehConfig = [{"priority": "High", "class": 10}]
    with patch("botocore.client.BaseClient._make_api_call", new=mock_make_api_call):
        with patch("requests.request", new=mock_make_requests_call):
            cp = setup_cert_provider()
            cp.get_certs(1, exampleVehConfig)
            assert len(uploaded_csvs) == 1
            cp.close()
            assert len(uploaded_csvs) == 2
            assert len(deleted_csvs) == 2
            assert uploaded_csvs[0] == deleted_csvs[0]
            assert uploaded_csvs[1] == deleted_csvs[1]


def test_upload():
    global uploaded_csvs
    global deleted_csvs
    uploaded_csvs, deleted_csvs = [], []
    with patch("botocore.client.BaseClient._make_api_call", new=mock_make_api_call):
        with patch("requests.request", new=mock_make_requests_call):
            cp = MP70CertProvider(logging=True)
            cp.__upload_csv__("testBucket", "testCsvString")
            assert len(uploaded_csvs) == 1


def test_addFunctionality():
    with patch("botocore.client.BaseClient._make_api_call", new=mock_make_api_call):
        with patch("requests.request", new=mock_make_requests_call):
            cp = setup_cert_provider()
            import MP70CertProviderConfig

            # REGION
            MP70CertProviderConfig.REGION_NAME = "testRegion"
            MP70CertProviderConfig.REGION_DESCRIPTION = "unittesting"
            MP70CertProviderConfig.REGION_DNS = "1.1.1.1"
            assert (
                cp.__add_region__()
                == f"region,name,description{os.linesep}region,testRegion,unittesting{os.linesep}"
            )

            # AGENCY
            MP70CertProviderConfig.AGENCY_NAME = "testAgency"
            MP70CertProviderConfig.AGENCY_DESCRIPTION = "unittest agency"
            MP70CertProviderConfig.AGENCY_CITY = "other city"
            MP70CertProviderConfig.AGENCY_STATE = "other"
            MP70CertProviderConfig.AGENCY_TIMEZONE = "UTC"
            MP70CertProviderConfig.AGENCY_CODE = "9876"
            MP70CertProviderConfig.AGENCY_PRIORITY = "None"
            MP70CertProviderConfig.AGENCY_ID = "1111"
            assert (
                cp.__add_agency__()
                == f"agency,name,region,description,city,state,timezone,agencyCode,priority{os.linesep}agency,testAgency,testRegion,unittest agency,other city,other,UTC,9876,None{os.linesep}"
            )

            # DEVICE
            assert (
                cp.__add_device_header__()
                == f"vehicleV2,deviceId,region,agency,name,description,type,priority,class,VID{os.linesep}"
            )

            MP70CertProviderConfig.VEHICLE_DESCRIPTION = "unittesting vehicle"
            MP70CertProviderConfig.VEHICLE_MAC = "123"
            MP70CertProviderConfig.VEHICLE_IP = "0.0.0.0"
            MP70CertProviderConfig.VEHICLE_IMEI = "1234"
            MP70CertProviderConfig.VEHICLE_MAKE = "MP70"
            MP70CertProviderConfig.VEHICLE_VID = "9999"
            MP70CertProviderConfig.VEHICLE_MODEL = "unittestMP70"
            exampleVehConfig = [{"priority": "High", "class": 10}]
            cp.added_devices = 0
            assert (
                cp.__add_device__(exampleVehConfig)[1]
                == f"vehicleV2,SimDevice0100,testRegion,testAgency,SimDevice0100,unittesting vehicle,Ladder Truck,High,10,0100{os.linesep}"
            )

            # COMMUNICATOR
            assert (
                re.match(
                    r"communicator,SimDevice0100Com,testRegion,testAgency,SimDevice0100,MP70 Simulator Communicator,SimDevice0100Com,\d+,10.22.22.1,10.22.22.1,22:22:22:00:00:01,MP70,unittestMP70",
                    cp.__add_communicator__()[1],
                )
                is not None
            )


def test_download():
    with patch("botocore.client.BaseClient._make_api_call", new=mock_make_api_call):
        with patch("requests.request", new=mock_make_requests_call):
            cp = setup_cert_provider()

            certs = cp.__download_certs__("1150_1150")
            print(certs)
            with open(certs["cafile_filename"], "r") as f:
                assert "Hello World Root CA!" == f.read()

            with open(certs["cert_filename"], "r") as f:
                assert "Hello World Cert!" == f.read()

            with open(certs["key_filename"], "r") as f:
                assert "Hello World Key!" == f.read()


def test_cantdownload():
    with patch(
        "botocore.client.BaseClient._make_api_call", new=mock_make_api_call_error
    ):
        with patch("requests.request", new=mock_make_requests_call_error):
            cp = MP70CertProvider(logging=True)

            certs = cp.__download_certs__("1150_1150")
            assert certs["cafile_filename"] is None
            assert certs["cert_filename"] is None
            assert certs["key_filename"] is None


def test_cantupload():
    with patch(
        "botocore.client.BaseClient._make_api_call", new=mock_make_api_call_error
    ):
        with patch("requests.request", new=mock_make_requests_call):
            cp = MP70CertProvider(logging=True)

            with pytest.raises(ConnectionError):
                cp.__upload_csv__("", "")
