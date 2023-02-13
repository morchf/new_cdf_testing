import os
import time
import json
import boto3
import pytest
import logging
import requests
from botocore.exceptions import ClientError
import sys

sys.path.append(
    os.path.join(os.path.abspath(os.path.realpath(__file__) + 2 * "/.."), "CDFBackend")
)
# from ui import (  # noqa: E402
  #  new_region,
   # new_agency,
   # new_vehicle,
  #  del_region,
  #  del_agency,
  #  del_vehicle,
#)

# get correct create and delete buckets
#create_bucket = os.environ["CREATE_CSV_BKT"]
#delete_bucket = os.environ["DELETE_CSV_BKT"]

# setup cdf api request parameters
#BASE_URL = os.environ["CDF_URL"]
ACCEPT = "application/vnd.aws-cdf-v2.0+json"
CONTENT_TYPE = "application/vnd.aws-cdf-v2.0+json"
HEADERS = {
    "Accept": ACCEPT,
    "content-type": CONTENT_TYPE,
}

# setup cdf api request parameters
#VPS_URL = os.environ["VPS_URL"]
ACCEPT = "application/vnd.aws-cdf-v2.0+json"
CONTENT_TYPE = "application/vnd.aws-cdf-v2.0+json"
HEADERS = {"Accept": ACCEPT, "content-type": CONTENT_TYPE}

# setup parametrized fixture. more test cases can be added simply by 1.
# placing a csv containing a
# single device in the location "lambdas/tests/testdata" and 2. adding
# a new tuple to the list of params
# below. Note that testcases should only contain one device
# (either phaseselector or vehicle)!


# setup cdf api request parameters
new_CDF_URL = "https://c6wn53rywi.execute-api.us-east-1.amazonaws.com/dev"
ACCEPT = "application/vnd.aws-cdf-v2.0+json"
CONTENT_TYPE = "application/vnd.aws-cdf-v2.0+json"
HEADERS = {"Accept": ACCEPT, "content-type": CONTENT_TYPE}


@pytest.fixture(
    scope="function",
    params=[
        ("CreateCDFClintonPS.csv", "mp705520", "uticarome", "clintonfiredept"),
        ("CreateCDFClintonVeh.csv", "mp705398", "uticarome", "clintonfiredept"),
    ],
)
def upload_file(request, upload_file_to_s3):
    """Setup function - uploads the passed in test case csv to step function
    create bucket, waits for 60 seconds for cdf device creation, then uploads
    same csv to step function delete bucket. Note that testcases
    should only contain one device(either phaseselector or vehicle)

        :params[0]: file name
        :params[1]: deviceId
        :params[2]: region
        :params[3]: agency
    """

    # setup urls and payload
    region_url = request.param[2]
    agency_url = request.param[3]

    urlSuffix = "/groups/%2fregion%2fagency/members/devices"
    urlSuffix = urlSuffix.replace("region", region_url)
    urlSuffix = urlSuffix.replace("agency", agency_url)

    fullUrl = BASE_URL + urlSuffix
    payload = {}

    # create the device and give time for cdf creation to complete
    file_path = request.fspath.join("..")
    upload_to_create_bkt = upload_file_to_s3(
        f"{file_path}/testdata/{request.param[0]}", create_bucket, request.param[1]
    )
    time.sleep(60)

    # call the cdf api to see if region, agency, and device creation succeeded
    create_response = requests.request("GET", fullUrl, headers=HEADERS, data=payload)
    create_data = json.loads(create_response.text)

    # delete the device and give time for cdf deletion to complete
    upload_to_delete_bkt = upload_file_to_s3(
        f"{file_path}/testdata/{request.param[0]}", delete_bucket, request.param[1]
    )
    time.sleep(30)

    # call the cdf api to see if region, agency, and device deletion succeeded
    delete_response = requests.request("GET", fullUrl, headers=HEADERS, data=payload)
    delete_data = json.loads(delete_response.text)

    # return either create or delete result to test function
    def _specify_operation(operation_type):
        if operation_type == "create":
            return (
                create_data,
                request.param[1],
                request.param[2],
                request.param[3],
                upload_to_create_bkt,
            )
        elif operation_type == "delete":
            return (
                delete_data,
                request.param[1],
                request.param[2],
                request.param[3],
                upload_to_delete_bkt,
            )

    return _specify_operation


@pytest.fixture(scope="module")
def upload_file_to_s3():
    def _upload_file_to_s3(file_name, bucket, object_name=None):
        """Upload a file to an S3 bucket

        :param file_name: File to upload
        :param bucket: Bucket to upload to
        :param object_name: S3 object name. If not specified then file_name is used
        :return: True if file was uploaded, else False
        """

        # If S3 object_name was not specified, use file_name
        if object_name is None:
            object_name = file_name

        # Upload the file
        s3_client = boto3.client("s3")
        try:
            response = s3_client.upload_file(file_name, bucket, object_name)
            print(response)
        except ClientError as e:
            logging.error(e)
            return False
        return True

    return _upload_file_to_s3


def pytest_addoption(parser):
    parser.addoption("--region", action="append")
    parser.addoption("--agency", action="append")


@pytest.fixture(scope="session")
def agency(request):
    agency_value = request.config.option.agency
    if agency_value is None:
        pytest.skip()
    return agency_value


@pytest.fixture(scope="session")
def region(request):
    region_value = request.config.option.region
    if region_value is None:
        pytest.skip()
    return region_value


@pytest.fixture(scope="session")
def cert_check(region, agency):
    # setup region and agency url and payload
    region_url = region[0].lower()
    agency_url = agency[0].lower()

    urlSuffix = "/groups/%2fregion%2fagency"
    urlSuffix = urlSuffix.replace("region", region_url)
    urlSuffix = urlSuffix.replace("agency", agency_url)

    fullUrl = BASE_URL + urlSuffix

    payload = {}

    response = requests.request("GET", fullUrl, headers=HEADERS, data=payload)

    json_data = json.loads(response.text)

    return json_data

@pytest.fixture(scope="session")
def read_Region():
    url = new_CDF_URL +'/regions'
    
    response = requests.get(url)
    data = response.text
   # data_json_str = json.dumps(data)
    data_json_object = json.loads(data)
       
    #assert response.status_code == 200
    print("listing all regions in CDF")
    #print(response.text)
    x=None
    for i in data_json_object:
        if i['name'] == 'tsptest':
            x = i['id']
            print(x)
            print(i['id'])
            print(i['name'])
         
        break
    with open('testdata/new_states.json', 'w') as f:
        json.dump(x, f, indent=2)
    return x

@pytest.fixture(scope="session")
def read_Agency(read_Region):
    _region = read_Region
    url = new_CDF_URL +'/agencies/region?id=[_region]'
    
    response = requests.get(url)
    data = response.text
   # data_json_str = json.dumps(data)
    data_json_object = json.loads(data)
       
    #assert response.status_code == 200
    print("listing all agencies in selected region in CDF")
    #print(response.text)
    x="e465f5f4-1a58-44e0-a5aa-9886f9c50c60"
    for i in data_json_object:
        if i['name'] == 'tsptest':
            x = i['id']
            print(x)
            print(i['id'])
            print(i['name'])
         
        break
    return x

def move_CDF_entity_data_to_tmp(filename, data):
    with open(f"/tmp/{filename}.json", "w") as f:
        f.write(data)
    f.close()


@pytest.fixture()
def setup_teardown_CDF_vehicle():
    region_name = "IntTestRegion"
    agency_name = "IntTestAgency"
    veh_name = "IntTestVeh"

    # move data to /tmp to allow CDF entities to be created
    data = open_json_file("valid_region_cdf_data.json")
    data = json.loads(data)
    data["name"] = region_name
    data["groupPath"] = f"/{region_name}"

    move_CDF_entity_data_to_tmp(region_name, json.dumps(data))

    data = open_json_file("valid_agency_cdf_data.json")
    data = json.loads(data)
    data["name"] = agency_name
    data["parentPath"] = f"/{region_name}"
    data["groupPath"] = f"/{region_name}/{agency_name}"

    move_CDF_entity_data_to_tmp(agency_name, json.dumps(data))

    data = open_json_file("valid_device_cdf_data.json")
    data = json.loads(data)
    data["deviceId"] = veh_name
    data["attributes"]["make"] = "Sierra Wireless"
    data["groups"]["ownedby"] = [f"/{region_name}/{agency_name}"]

    move_CDF_entity_data_to_tmp(veh_name, json.dumps(data))

    # create entities
    new_region(region_name)
    new_agency(region_name, agency_name)
    new_vehicle(region_name, agency_name, veh_name)

    # allow test to run
    yield

    # clean up CDF for next test
    del_vehicle(region_name, agency_name, veh_name)
    del_agency(region_name, agency_name)
    del_region(region_name)

    if os.path.exists(f"/tmp/{region_name}.json"):
        os.remove(f"/tmp/{region_name}.json")

    if os.path.exists(f"/tmp/{agency_name}.json"):
        os.remove(f"/tmp/{agency_name}.json")

    if os.path.exists(f"/tmp/{veh_name}.json"):
        os.remove(f"/tmp/{veh_name}.json")


@pytest.fixture()
def mock_event():
    event = open_json_file("valid_data.json")
    event = json.loads(event)
    return event


def open_json_file(file_name):
    json_str = None
    if os.path.exists(file_name):
        with open(f"{file_name}", "r") as f:
            json_str = f.read()
        json_str = json_str.replace("\r", "").replace("\n", "").replace(" ", "")
    else:
        print(f"{file_name} not found.")
    return json_str
