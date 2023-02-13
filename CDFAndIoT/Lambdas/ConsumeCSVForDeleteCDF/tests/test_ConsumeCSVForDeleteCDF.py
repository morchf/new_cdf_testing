import pytest
import os
import sys
import json
import csv
from moto import mock_s3
import boto3

sys.path.append('../lambda-code')
import ConsumeCSVForDeleteCDF as ccd

dir_path = os.path.dirname(os.path.realpath(__file__))
bkt = 'test-bucket'
csv_name = 'data.csv'

def create_csv(fieldnames, values):
    with open(csv_name, 'w') as file:
        csv_writer = csv.writer(file, delimiter=',')
        csv_writer.writerow('DO NOT DELETE')
        csv_writer.writerow(fieldnames)
        csv_writer.writerow(values)

@pytest.fixture(scope = 'function')
def manage_data():
    file_name = os.path.join(dir_path, "input.json")
    with open(file_name, 'r') as file:
        data = json.load(file)

    data['input']['detail']['requestParameters']['key'] = csv_name
    data['input']['detail']['requestParameters']['bucketName'] = bkt

    yield data

    # Remove CSV file from download path
    path = f'/tmp/{csv_name}'
    print(path)
    if os.path.exists(path):
        os.remove(path)
        print("Removed CSV from download path")
    else:
        print("The file does not exist")

    # Remove CSV file created for upload
    path = f'./{csv_name}'
    print(path)
    if os.path.exists(path):
        os.remove(path)
        print("Removed CSV used for upload")
    else:
        print("The file does not exist")

# Test ConsumeCSVForDeleteCDF for region data
def test_lambda_handler_no_detail(manage_data):
    fieldnames = ['region', 'name', 'regionDNS', 'description']
    values = ['region', 'regtest86', '10.3.1.23', 'test region']
    create_csv(fieldnames, values)
    with mock_s3():
        with pytest.raises(Exception) as info:
            conn = boto3.resource('s3', region_name='us-east-1')
            conn.create_bucket(Bucket=bkt)
            conn.Object(bkt, csv_name).upload_file(f'{csv_name}')

            data = manage_data
            del data['input']['detail']

            rc = ccd.lambda_handler(data['input'], None)

    assert str(info.value) == 'Input data lacks detail field, cannot download CSV from S3'

# Test ConsumeCSVForDeleteCDF for region data
def test_lambda_handler_no_key(manage_data):
    fieldnames = ['region', 'name', 'regionDNS', 'description']
    values = ['region', 'regtest86', '10.3.1.23', 'test region']
    create_csv(fieldnames, values)
    with mock_s3():
        with pytest.raises(Exception) as info:
            conn = boto3.resource('s3', region_name='us-east-1')
            conn.create_bucket(Bucket=bkt)
            conn.Object(bkt, csv_name).upload_file(f'{csv_name}')

            data = manage_data
            del data['input']['detail']['requestParameters']['key']

            rc = ccd.lambda_handler(data['input'], None)

    assert str(info.value) == 'Input data missing S3 key, cannot download CSV from S3'


# Test ConsumeCSVForDeleteCDF for region data
def test_lambda_handler_region(manage_data):
    fieldnames = ['region', 'name', 'regionDNS', 'description']
    values = ['region', 'regtest86', '10.3.1.23', 'test region']
    create_csv(fieldnames, values)
    with mock_s3():
        conn = boto3.resource('s3', region_name='us-east-1')
        conn.create_bucket(Bucket=bkt)
        conn.Object(bkt, csv_name).upload_file(f'{csv_name}')

        data = manage_data

        rc = ccd.lambda_handler(data['input'], None)

    assert rc == {'regions': 'regtest86', 'agencies': '', 'vehicles': '', 'phase_selectors': '', 'communicators': '', 'invalid_rows': ''}

# Test ConsumeCSVForDeleteCDF for agency data
def test_lambda_handler_agency(manage_data):
    fieldnames = ['agency', 'name', 'region', 'description', 'city', 'state', 'timezone', 'agencyCode', 'priority', 'agencyID']
    values = ['agency', 'agytest86', 'regtest86', 'test agency', 'Eugene', 'OR', 'Pacific', '111', 'High', '111']
    create_csv(fieldnames, values)
    with mock_s3():
        conn = boto3.resource('s3', region_name='us-east-1')
        conn.create_bucket(Bucket=bkt)
        conn.Object(bkt, csv_name).upload_file(f'{csv_name}')

        data = manage_data

        rc = ccd.lambda_handler(data['input'], None)

    assert rc == {'regions': '', 'agencies': 'regtest86/agytest86', 'vehicles': '', 'phase_selectors': '', 'communicators': '', 'invalid_rows': ''}

# Test ConsumeCSVForDeleteCDF for vehicle data
def test_lambda_handler_vehicle(manage_data):
    fieldnames = ['vehicle', 'deviceId', 'region', 'agency', 'description', 'gttSerial', 'addressMAC', 'addressLAN', 'addressWAN',
    'IMEI', 'make', 'model', 'priority', 'class', 'VID']
    values = ['vehicle', 'veh86', 'regtest86', 'agytest86', 'test vehicle', '2100IO9803', '03:94:02:88:02:34', '10.2.2.111', '10.2.3.1', '358000000000000', 'Sierra Wireless', 'MP-70', 'High', '10', '1532']
    create_csv(fieldnames, values)
    with mock_s3():
        conn = boto3.resource('s3', region_name='us-east-1')
        conn.create_bucket(Bucket=bkt)
        conn.Object(bkt, csv_name).upload_file(f'{csv_name}')

        data = manage_data

        rc = ccd.lambda_handler(data['input'], None)

    assert rc == {'regions': '', 'agencies': '', 'vehicles': 'regtest86/agytest86/veh86', 'phase_selectors': '', 'communicators': '', 'invalid_rows': ''}

# Test ConsumeCSVForDeleteCDF for communicator data
def test_lambda_handler_communicator(manage_data):
    fieldnames = ['communicator', 'deviceId', 'region', 'agency', 'description', 'manufacSerial', 'gttSerial', 'addressMAC', 'addressLAN', 'addressWAN', 'IMEI', 'make', 'model', 'vehDevGUID', 'type', 'attachedDeviceId']
    values = ['communicator', 'comm86', 'UnitTest', 'testing', 'modem on veh1234', '123457', 'MP70JH7778', '03:94:02:88:02:34', '22.22.22.57', '10.2.3.1', '358123000000000', 'Sierra Wireless', 'MP-70', 'NULL_GUID', 'SIERRAWIRELESS', 'veh1234']
    create_csv(fieldnames, values)
    with mock_s3():
        conn = boto3.resource('s3', region_name='us-east-1')
        conn.create_bucket(Bucket=bkt)
        conn.Object(bkt, csv_name).upload_file(f'{csv_name}')

        data = manage_data

        rc = ccd.lambda_handler(data['input'], None)

    assert rc == {'regions': '', 'agencies': '', 'vehicles': '', 'phase_selectors': '', 'communicators': 'UnitTest/testing/comm86', 'invalid_rows': ''}


# Test ConsumeCSVForDeleteCDF for phaseselector data
def test_lambda_handler_phaseselector(manage_data):
    fieldnames = ['phaseselector', 'deviceId', 'region', 'agency', 'description', 'gttSerial', 'addressMAC', 'addressLAN',
    'addressWAN', 'IMEI', 'make', 'model', 'lat', 'long']
    values = ['phaseselector', 'ps86', 'regtest86', 'agytest86', 'test phaseselector', '7640uw1324', '03:94:02:88:02:34', '22.22.22.57', '10.2.3.1', '358000000000000', 'Sierra Wireless', 'MP-70', '47.0001', '-91']
    create_csv(fieldnames, values)
    with mock_s3():
        conn = boto3.resource('s3', region_name='us-east-1')
        conn.create_bucket(Bucket=bkt)
        conn.Object(bkt, csv_name).upload_file(f'{csv_name}')

        data = manage_data

        rc = ccd.lambda_handler(data['input'], None)

    assert rc == {'regions': '', 'agencies': '', 'vehicles': '', 'phase_selectors': 'regtest86/agytest86/ps86', 'communicators': '', 'invalid_rows': ''}

# Test ConsumeCSVForDeleteCDF for bad region data missing region name
def test_lambda_handler_no_region_name(manage_data):
    fieldnames = ['region', 'name', 'regionDNS', 'description']
    values = ['region', '', '10.3.1.23', 'test region']
    create_csv(fieldnames, values)
    with mock_s3():
        conn = boto3.resource('s3', region_name='us-east-1')
        conn.create_bucket(Bucket=bkt)
        conn.Object(bkt, csv_name).upload_file(f'{csv_name}')

        data = manage_data

        rc = ccd.lambda_handler(data['input'], None)

    assert rc == {'regions': '', 'agencies': '', 'vehicles': '', 'phase_selectors': '', 'communicators': '', 'invalid_rows': '2'}

# Test ConsumeCSVForDeleteCDF for agency data missing agency name
def test_lambda_handler_no_agency_name(manage_data):
    fieldnames = ['agency', 'name', 'region', 'description', 'city', 'state', 'timezone', 'agencyCode', 'priority', 'agencyID']
    values = ['agency', '', 'regtest86', 'test agency', 'Eugene', 'OR', 'Pacific', '111', 'High', '111']
    create_csv(fieldnames, values)
    with mock_s3():
        conn = boto3.resource('s3', region_name='us-east-1')
        conn.create_bucket(Bucket=bkt)
        conn.Object(bkt, csv_name).upload_file(f'{csv_name}')

        data = manage_data

        rc = ccd.lambda_handler(data['input'], None)

    assert rc == {'regions': '', 'agencies': '', 'vehicles': '', 'phase_selectors': '', 'communicators': '', 'invalid_rows': '2'}

# Test ConsumeCSVForDeleteCDF for vehicle data missing deviceId
def test_lambda_handler_no_vehicle_deviceId(manage_data):
    fieldnames = ['vehicle', 'deviceID', 'region', 'agency', 'description', 'gttSerial', 'addressMAC', 'addressLAN', 'addressWAN',
    'IMEI', 'make', 'model', 'priority', 'class', 'VID']
    values = ['vehicle', '', 'regtest86', 'agytest86', 'test vehicle', '2100IO9803', '03:94:02:88:02:34', '10.2.2.111', '10.2.3.1', '358000000000000', 'Sierra Wireless', 'MP-70', 'High', '10', '1532']
    create_csv(fieldnames, values)
    with mock_s3():
        conn = boto3.resource('s3', region_name='us-east-1')
        conn.create_bucket(Bucket=bkt)
        conn.Object(bkt, csv_name).upload_file(f'{csv_name}')

        data = manage_data

        rc = ccd.lambda_handler(data['input'], None)

    assert rc == {'regions': '', 'agencies': '', 'vehicles': '', 'phase_selectors': '', 'communicators': '', 'invalid_rows': '2'}

# Test ConsumeCSVForDeleteCDF for communicator data
def test_lambda_handler_no_communicator_deviceId(manage_data):
    fieldnames = ['communicator', 'deviceId', 'region', 'agency','description', 'manufacSerial', 'gttSerial', 'addressMAC', 'addressLAN', 'addressWAN', 'IMEI', 'make', 'model', 'vehDevGUID', 'type', 'attachedDeviceId']
    values = ['communicator', '', 'UnitTest', 'testing', 'modem on veh1234', '123457', 'MP70JH7778', '03:94:02:88:02:34', '22.22.22.57', '10.2.3.1', '358123000000000', 'Sierra Wireless', 'MP-70', 'NULL_GUID', 'SIERRAWIRELESS', 'veh1234']
    create_csv(fieldnames, values)
    with mock_s3():
        conn = boto3.resource('s3', region_name='us-east-1')
        conn.create_bucket(Bucket=bkt)
        conn.Object(bkt, csv_name).upload_file(f'{csv_name}')

        data = manage_data

        rc = ccd.lambda_handler(data['input'], None)

    assert rc == {'regions': '', 'agencies': '', 'vehicles': '', 'phase_selectors': '', 'communicators': '', 'invalid_rows': '2'}


# Test ConsumeCSVForDeleteCDF for phaseselector data missing deviceId
def test_lambda_handler_no_phaseselector_deviceId(manage_data):
    fieldnames = ['phaseselector', 'deviceID', 'region', 'agency', 'description', 'gttSerial', 'addressMAC', 'addressLAN',
    'addressWAN', 'IMEI', 'make', 'model', 'lat', 'long']
    values = ['phaseselector', '', 'regtest86', 'agytest86', 'test phaseselector', '7640uw1324', '03:94:02:88:02:34', '22.22.22.57', '10.2.3.1', '358000000000000', 'Sierra Wireless', 'MP-70', '47.0001', '-91']
    create_csv(fieldnames, values)
    with mock_s3():
        conn = boto3.resource('s3', region_name='us-east-1')
        conn.create_bucket(Bucket=bkt)
        conn.Object(bkt, csv_name).upload_file(f'{csv_name}')

        data = manage_data

        rc = ccd.lambda_handler(data['input'], None)

    assert rc == {'regions': '', 'agencies': '', 'vehicles': '', 'phase_selectors': '', 'communicators': '', 'invalid_rows': '2'}

# Test ConsumeCSVForDeleteCDF for vehicle data missing agency name
def test_lambda_handler_vehicle_no_agency_name(manage_data):
    fieldnames = ['vehicle', 'deviceID', 'region', 'agency', 'description', 'gttSerial', 'addressMAC', 'addressLAN', 'addressWAN',
    'IMEI', 'make', 'model', 'priority', 'class', 'VID']
    values = ['vehicle', 'veh86', 'regtest86', '', 'test vehicle', '2100IO9803', '03:94:02:88:02:34', '10.2.2.111', '10.2.3.1', '358000000000000', 'Sierra Wireless', 'MP-70', 'High', '10', '1532']
    create_csv(fieldnames, values)
    with mock_s3():
        conn = boto3.resource('s3', region_name='us-east-1')
        conn.create_bucket(Bucket=bkt)
        conn.Object(bkt, csv_name).upload_file(f'{csv_name}')

        data = manage_data

        rc = ccd.lambda_handler(data['input'], None)

    assert rc == {'regions': '', 'agencies': '', 'vehicles': '', 'phase_selectors': '', 'communicators': '', 'invalid_rows': '2'}

# Test ConsumeCSVForDeleteCDF for phaseselector data missing agency name
def test_lambda_handler_phaseselector_no_agency_name(manage_data):
    fieldnames = ['phaseselector', 'deviceID', 'region', 'agency', 'description', 'gttSerial', 'addressMAC', 'addressLAN',
    'addressWAN', 'IMEI', 'make', 'model', 'lat', 'long']
    values = ['phaseselector', 'ps86', 'regtest86', '', 'test phaseselector', '7640uw1324', '03:94:02:88:02:34', '22.22.22.57', '10.2.3.1', '358000000000000', 'Sierra Wireless', 'MP-70', '47.0001', '-91']
    create_csv(fieldnames, values)
    with mock_s3():
        conn = boto3.resource('s3', region_name='us-east-1')
        conn.create_bucket(Bucket=bkt)
        conn.Object(bkt, csv_name).upload_file(f'{csv_name}')

        data = manage_data

        rc = ccd.lambda_handler(data['input'], None)

    assert rc == {'regions': '', 'agencies': '', 'vehicles': '', 'phase_selectors': '', 'communicators': '', 'invalid_rows': '2'}

# Test ConsumeCSVForDeleteCDF for vehicle data missing region name
def test_lambda_handler_vehicle_no_region_name(manage_data):
    fieldnames = ['vehicle', 'deviceID', 'region', 'agency', 'description', 'gttSerial', 'addressMAC', 'addressLAN', 'addressWAN',
    'IMEI', 'make', 'model', 'priority', 'class', 'VID']
    values = ['vehicle', 'veh86', '', 'agytest86', 'test vehicle', '2100IO9803', '03:94:02:88:02:34', '10.2.2.111', '10.2.3.1', '358000000000000', 'Sierra Wireless', 'MP-70', 'High', '10', '1532']
    create_csv(fieldnames, values)
    with mock_s3():
        conn = boto3.resource('s3', region_name='us-east-1')
        conn.create_bucket(Bucket=bkt)
        conn.Object(bkt, csv_name).upload_file(f'{csv_name}')

        data = manage_data

        rc = ccd.lambda_handler(data['input'], None)

    assert rc == {'regions': '', 'agencies': '', 'vehicles': '', 'phase_selectors': '', 'communicators': '', 'invalid_rows': '2'}

# Test ConsumeCSVForDeleteCDF for phaseselector data missing region name
def test_lambda_handler_phaseselector_no_region_name(manage_data):
    fieldnames = ['phaseselector', 'deviceID', 'region', 'agency', 'description', 'gttSerial', 'addressMAC', 'addressLAN',
    'addressWAN', 'IMEI', 'make', 'model', 'lat', 'long']
    values = ['phaseselector', 'ps86', '', 'agytest86', 'test phaseselector', '7640uw1324', '03:94:02:88:02:34', '22.22.22.57', '10.2.3.1', '358000000000000', 'Sierra Wireless', 'MP-70', '47.0001', '-91']
    create_csv(fieldnames, values)
    with mock_s3():
        conn = boto3.resource('s3', region_name='us-east-1')
        conn.create_bucket(Bucket=bkt)
        conn.Object(bkt, csv_name).upload_file(f'{csv_name}')

        data = manage_data

        rc = ccd.lambda_handler(data['input'], None)

    assert rc == {'regions': '', 'agencies': '', 'vehicles': '', 'phase_selectors': '', 'communicators': '', 'invalid_rows': '2'}

# Test ConsumeCSVForDeleteCDF for done
def test_lambda_handler_done(manage_data):
    fieldnames = ['Done']
    values = ['']
    create_csv(fieldnames, values)
    with mock_s3():
        conn = boto3.resource('s3', region_name='us-east-1')
        conn.create_bucket(Bucket=bkt)
        conn.Object(bkt, csv_name).upload_file(f'{csv_name}')

        data = manage_data

        rc = ccd.lambda_handler(data['input'], None)

    assert rc == {'regions': '', 'agencies': '', 'vehicles': '', 'phase_selectors': '', 'communicators': '', 'invalid_rows': ''}

