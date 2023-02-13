import pytest
import os
import sys
import json
import csv
from moto import mock_s3
import boto3

# allow tests to find lambda
sys.path.append('../lambda-code')
import ConsumeCSV as cc

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

# Test consume-csv for region content data
def test_lambda_handler_region_header(manage_data):
    fieldnames = ['region', 'name', 'regionDNS', 'description']
    values = ['region', 'regtest86', '10.3.1.23', 'test region']
    create_csv(fieldnames, values)
    with mock_s3():
        conn = boto3.resource('s3', region_name='us-east-1')
        conn.create_bucket(Bucket=bkt)
        conn.Object(bkt, csv_name).upload_file(f'{csv_name}')

        data = manage_data

        rc = cc.lambda_handler(data['input'], None)

    assert rc == {'row_type': 'header', 'row_count': 2, 'header_row_number': 1, 'header': ['region', 'name', 'regionDNS', 'description'], 'row_content': None}

# Test consume-csv for region content data
def test_lambda_handler_region_content(manage_data):
    fieldnames = ['region', 'name', 'regionDNS', 'description']
    values = ['region', 'regtest86', '10.3.1.23', 'test region']
    create_csv(fieldnames, values)
    with mock_s3():
        conn = boto3.resource('s3', region_name='us-east-1')
        conn.create_bucket(Bucket=bkt)
        conn.Object(bkt, csv_name).upload_file(f'{csv_name}')

        data = manage_data
        data['input']['taskResult-consume-csv']['row_count'] = 2

        rc = cc.lambda_handler(data['input'], None)

    assert rc == {'row_type': 'content', 'row_count': 3, 'header_row_number': 1, 'header': ['region', 'name', 'regionDNS', 'description'], 'row_content': ['region', 'regtest86', '10.3.1.23', 'test region']}

# Test consume-csv for agency header data
def test_lambda_handler_agency_header(manage_data):
    fieldnames = ['agency', 'name', 'region', 'description', 'city', 'state', 'timezone', 'agencyCode', 'priority', 'agencyID']
    values = ['agency', 'agytest86', 'regtest86', 'test agency', 'Eugene', 'OR', 'Pacific', '111', 'High', '111']
    create_csv(fieldnames, values)
    with mock_s3():
        conn = boto3.resource('s3', region_name='us-east-1')
        conn.create_bucket(Bucket=bkt)
        conn.Object(bkt, csv_name).upload_file(f'{csv_name}')

        data = manage_data

        rc = cc.lambda_handler(data['input'], None)

    assert rc == {'row_type': 'header', 'row_count': 2, 'header_row_number': 1,
                  'header': ['agency', 'name', 'region', 'description', 'city', 'state', 'timezone', 'agencyCode', 'priority', 'agencyID'], 
                  'row_content': None}

# Test consume-csv for agency content data
def test_lambda_handler_agency_content(manage_data):
    fieldnames = ['agency', 'name', 'region', 'description', 'city', 'state', 'timezone', 'agencyCode', 'priority', 'agencyID']
    values = ['agency', 'agytest86', 'regtest86', 'test agency', 'Eugene', 'OR', 'Pacific', '111', 'High', '111']
    create_csv(fieldnames, values)
    with mock_s3():
        conn = boto3.resource('s3', region_name='us-east-1')
        conn.create_bucket(Bucket=bkt)
        conn.Object(bkt, csv_name).upload_file(f'{csv_name}')

        data = manage_data
        data['input']['taskResult-consume-csv']['row_count'] = 2

        rc = cc.lambda_handler(data['input'], None)

    assert rc == {'row_type': 'content', 'row_count': 3, 'header_row_number': 1,
                  'header': ['agency', 'name', 'region', 'description', 'city', 'state', 'timezone', 'agencyCode', 'priority', 'agencyID'],
                  'row_content': ['agency', 'agytest86', 'regtest86', 'test agency', 'Eugene', 'OR', 'Pacific', '111', 'High', '111']}

# Test consume-csv for vehicle header data
def test_lambda_handler_vehicle_header(manage_data):
    fieldnames = ['vehicle', 'deviceId', 'region', 'agency', 'description', 'gttSerial', 'addressMAC', 'addressLAN', 'addressWAN', 'IMEI', 'make', 'model', 'priority', 'class', 'VID']
    values = ['vehicle', 'veh86', 'regtest86', 'agytest86', 'test vehicle', '2100IO9803', '03:94:02:88:02:34', '10.2.2.111', '10.2.3.1', '358000000000000', 'Sierra Wireless', 'MP-70', 'High', '10', '1532']
    create_csv(fieldnames, values)
    with mock_s3():
        conn = boto3.resource('s3', region_name='us-east-1')
        conn.create_bucket(Bucket=bkt)
        conn.Object(bkt, csv_name).upload_file(f'{csv_name}')

        data = manage_data

        rc = cc.lambda_handler(data['input'], None)

    assert rc == {'row_type': 'header', 'row_count': 2, 'header_row_number': 1,
                  'header': ['vehicle', 'deviceId', 'region', 'agency', 'description', 'gttSerial', 'addressMAC', 'addressLAN', 'addressWAN', 'IMEI', 'make', 'model', 'priority', 'class', 'VID'],
                  'row_content': None}

# Test consume-csv for vehicle content data
def test_lambda_handler_vehicle_content(manage_data):
    fieldnames = ['vehicle', 'deviceId', 'region', 'agency', 'description', 'gttSerial', 'addressMAC', 'addressLAN', 'addressWAN', 'IMEI', 'make', 'model', 'priority', 'class', 'VID']
    values = ['vehicle', 'veh86', 'regtest86', 'agytest86', 'test vehicle', '2100IO9803', '03:94:02:88:02:34', '10.2.2.111', '10.2.3.1', '358000000000000', 'Sierra Wireless', 'MP-70', 'High', '10', '1532']
    create_csv(fieldnames, values)
    with mock_s3():
        conn = boto3.resource('s3', region_name='us-east-1')
        conn.create_bucket(Bucket=bkt)
        conn.Object(bkt, csv_name).upload_file(f'{csv_name}')

        data = manage_data
        data['input']['taskResult-consume-csv']['row_count'] = 2

        rc = cc.lambda_handler(data['input'], None)

    assert rc == {'row_type': 'content', 'row_count': 3, 'header_row_number': 1,
                  'header': ['vehicle', 'deviceId', 'region', 'agency', 'description', 'gttSerial', 'addressMAC', 'addressLAN', 'addressWAN', 'IMEI', 'make', 'model', 'priority', 'class', 'VID'],
                  'row_content': ['vehicle', 'veh86', 'regtest86', 'agytest86', 'test vehicle', '2100IO9803', '03:94:02:88:02:34', '10.2.2.111', '10.2.3.1', '358000000000000', 'Sierra Wireless', 'MP-70', 'High', '10', '1532']}

# Test consume-csv for vehicle header data
def test_lambda_handler_vehicleV2_header(manage_data):
    fieldnames = ['vehicleV2', 'deviceId', 'region', 'agency', 'description', 'gttSerial', 'addressMAC', 'addressLAN', 'addressWAN', 'IMEI', 'make', 'model', 'priority', 'class', 'VID']
    values = ['vehicleV2', 'veh86', 'regtest86', 'agytest86', 'test vehicle', '2100IO9803', '03:94:02:88:02:34', '10.2.2.111', '10.2.3.1', '358000000000000', 'Sierra Wireless', 'MP-70', 'High', '10', '1532']
    create_csv(fieldnames, values)
    with mock_s3():
        conn = boto3.resource('s3', region_name='us-east-1')
        conn.create_bucket(Bucket=bkt)
        conn.Object(bkt, csv_name).upload_file(f'{csv_name}')

        data = manage_data

        rc = cc.lambda_handler(data['input'], None)

    assert rc == {'row_type': 'header', 'row_count': 2, 'header_row_number': 1,
                  'header': ['vehicleV2', 'deviceId', 'region', 'agency', 'description', 'gttSerial', 'addressMAC', 'addressLAN', 'addressWAN', 'IMEI', 'make', 'model', 'priority', 'class', 'VID'],
                  'row_content': None}

# Test consume-csv for vehicle content data
def test_lambda_handler_vehicleV2_content(manage_data):
    fieldnames = ['vehicleV2', 'deviceId', 'region', 'agency', 'description', 'gttSerial', 'addressMAC', 'addressLAN', 'addressWAN', 'IMEI', 'make', 'model', 'priority', 'class', 'VID']
    values = ['vehicleV2', 'veh86', 'regtest86', 'agytest86', 'test vehicle', '2100IO9803', '03:94:02:88:02:34', '10.2.2.111', '10.2.3.1', '358000000000000', 'Sierra Wireless', 'MP-70', 'High', '10', '1532']
    create_csv(fieldnames, values)
    with mock_s3():
        conn = boto3.resource('s3', region_name='us-east-1')
        conn.create_bucket(Bucket=bkt)
        conn.Object(bkt, csv_name).upload_file(f'{csv_name}')

        data = manage_data
        data['input']['taskResult-consume-csv']['row_count'] = 2

        rc = cc.lambda_handler(data['input'], None)

    assert rc == {'row_type': 'content', 'row_count': 3, 'header_row_number': 1,
                  'header': ['vehicleV2', 'deviceId', 'region', 'agency', 'description', 'gttSerial', 'addressMAC', 'addressLAN', 'addressWAN', 'IMEI', 'make', 'model', 'priority', 'class', 'VID'],
                  'row_content': ['vehicleV2', 'veh86', 'regtest86', 'agytest86', 'test vehicle', '2100IO9803', '03:94:02:88:02:34', '10.2.2.111', '10.2.3.1', '358000000000000', 'Sierra Wireless', 'MP-70', 'High', '10', '1532']}


# Test consume-csv for communicator header data
def test_lambda_handler_communicator_header(manage_data):
    fieldnames = ['communicator', 'deviceId', 'region', 'agency', 'description', 'gttSerial', 'addressMAC', 'addressLAN', 'addressWAN', 'IMEI', 'make', 'model', 'priority', 'class', 'VID']
    values = ['communicator', 'comm86', 'regtest86', 'agytest86', 'test vehicle', '2100IO9803', '03:94:02:88:02:34', '10.2.2.111', '10.2.3.1', '358000000000000', 'Sierra Wireless', 'MP-70', 'High', '10', '1532']
    create_csv(fieldnames, values)
    with mock_s3():
        conn = boto3.resource('s3', region_name='us-east-1')
        conn.create_bucket(Bucket=bkt)
        conn.Object(bkt, csv_name).upload_file(f'{csv_name}')

        data = manage_data

        rc = cc.lambda_handler(data['input'], None)

    assert rc == {'row_type': 'header', 'row_count': 2, 'header_row_number': 1,
                  'header': ['communicator', 'deviceId', 'region', 'agency', 'description', 'gttSerial', 'addressMAC', 'addressLAN', 'addressWAN', 'IMEI', 'make', 'model', 'priority', 'class', 'VID'],
                  'row_content': None}

# Test consume-csv for communicator content data
def test_lambda_handler_communicator_content(manage_data):
    fieldnames = ['communicator', 'deviceId', 'region', 'agency', 'description', 'gttSerial', 'addressMAC', 'addressLAN', 'addressWAN', 'IMEI', 'make', 'model', 'priority', 'class', 'VID']
    values = ['communicator', 'comm86', 'regtest86', 'agytest86', 'test vehicle', '2100IO9803', '03:94:02:88:02:34', '10.2.2.111', '10.2.3.1', '358000000000000', 'Sierra Wireless', 'MP-70', 'High', '10', '1532']
    create_csv(fieldnames, values)
    with mock_s3():
        conn = boto3.resource('s3', region_name='us-east-1')
        conn.create_bucket(Bucket=bkt)
        conn.Object(bkt, csv_name).upload_file(f'{csv_name}')

        data = manage_data
        data['input']['taskResult-consume-csv']['row_count'] = 2

        rc = cc.lambda_handler(data['input'], None)

    assert rc == {'row_type': 'content', 'row_count': 3, 'header_row_number': 1,
                  'header': ['communicator', 'deviceId', 'region', 'agency', 'description', 'gttSerial', 'addressMAC', 'addressLAN', 'addressWAN', 'IMEI', 'make', 'model', 'priority', 'class', 'VID'],
                  'row_content': ['communicator', 'comm86', 'regtest86', 'agytest86', 'test vehicle', '2100IO9803', '03:94:02:88:02:34', '10.2.2.111', '10.2.3.1', '358000000000000', 'Sierra Wireless', 'MP-70', 'High', '10', '1532']}


# Test consume-csv for phaseselector header data
def test_lambda_handler_phaseselector_header(manage_data):
    fieldnames = ['phaseselector', 'deviceId', 'region', 'agency', 'description', 'gttSerial', 'addressMAC', 'addressLAN', 'addressWAN', 'IMEI', 'make', 'model', 'lat', 'long']
    values = ['phaseselector', 'ps86', 'regtest86', 'agytest86', 'test phaseselector', '7640uw1324', '03:94:02:88:02:34', '22.22.22.57', '10.2.3.1', '358000000000000', 'Sierra Wireless', 'MP-70', '47.0001', '-91']
    create_csv(fieldnames, values)
    with mock_s3():
        conn = boto3.resource('s3', region_name='us-east-1')
        conn.create_bucket(Bucket=bkt)
        conn.Object(bkt, csv_name).upload_file(f'{csv_name}')

        data = manage_data

        rc = cc.lambda_handler(data['input'], None)

    assert rc == {'row_type': 'header', 'row_count': 2, 'header_row_number': 1,
                  'header': ['phaseselector', 'deviceId', 'region', 'agency', 'description', 'gttSerial', 'addressMAC', 'addressLAN', 'addressWAN', 'IMEI', 'make', 'model', 'lat', 'long'],
                  'row_content': None}

# Test consume-csv for phaseselector content data
def test_lambda_handler_phaseselector_content(manage_data):
    fieldnames = ['phaseselector', 'deviceId', 'region', 'agency', 'description', 'gttSerial', 'addressMAC', 'addressLAN', 'addressWAN', 'IMEI', 'make', 'model', 'lat', 'long']
    values = ['phaseselector', 'ps86', 'regtest86', 'agytest86', 'test phaseselector', '7640uw1324', '03:94:02:88:02:34', '22.22.22.57', '10.2.3.1', '358000000000000', 'Sierra Wireless', 'MP-70', '47.0001', '-91']
    create_csv(fieldnames, values)
    with mock_s3():
        conn = boto3.resource('s3', region_name='us-east-1')
        conn.create_bucket(Bucket=bkt)
        conn.Object(bkt, csv_name).upload_file(f'{csv_name}')

        data = manage_data
        data['input']['taskResult-consume-csv']['row_count'] = 2

        rc = cc.lambda_handler(data['input'], None)

    assert rc == {'row_type': 'content', 'row_count': 3, 'header_row_number': 1,
                  'header': ['phaseselector', 'deviceId', 'region', 'agency', 'description', 'gttSerial', 'addressMAC', 'addressLAN', 'addressWAN', 'IMEI', 'make', 'model', 'lat', 'long'],
                  'row_content': ['phaseselector', 'ps86', 'regtest86', 'agytest86', 'test phaseselector', '7640uw1324', '03:94:02:88:02:34', '22.22.22.57', '10.2.3.1', '358000000000000', 'Sierra Wireless', 'MP-70', '47.0001', '-91']}

def test_lambda_handler_no_name_key(manage_data):
    # Missing name header and value
    fieldnames = ['agency', 'region', 'description', 'city', 'state', 'timezone', 'agencyCode', 'priority', 'agencyID']
    values = ['agency', 'agytest86', 'regtest86', 'test agency', 'Eugene', 'OR', 'Pacific', '111', 'High', '111']
    create_csv(fieldnames, values)
    with mock_s3():
        conn = boto3.resource('s3', region_name='us-east-1')
        conn.create_bucket(Bucket=bkt)
        conn.Object(bkt, csv_name).upload_file(f'{csv_name}')

        data = manage_data

        rc = cc.lambda_handler(data['input'], None)

    # without name in the header this is saved as a content row when it really isn't
    assert rc == {'row_type': 'content', 'row_count': 2, 'header_row_number': 1,
                  'header': ['agency', 'region', 'description', 'city', 'state', 'timezone', 'agencyCode', 'priority', 'agencyID'],
                  'row_content': ['agency', 'region', 'description', 'city', 'state', 'timezone', 'agencyCode', 'priority', 'agencyID']}

# Test consume-csv when given bad data
def test_lambda_handler_no_name_value(manage_data):
    # Missing value of name for name field in values dictionary
    fieldnames = ['agency', 'name', 'region', 'description', 'city', 'state', 'timezone', 'agencyCode', 'priority', 'agencyID']
    values = ['agency', '', 'regtest86', 'test agency', 'Eugene', 'OR', 'Pacific', '111', 'High', '111']
    create_csv(fieldnames, values)
    with mock_s3():
        conn = boto3.resource('s3', region_name='us-east-1')
        conn.create_bucket(Bucket=bkt)
        conn.Object(bkt, csv_name).upload_file(f'{csv_name}')

        data = manage_data
        data['input']['taskResult-consume-csv']['row_count'] = 2

        rc = cc.lambda_handler(data['input'], None)

    assert rc == {'row_type': 'content', 'row_count': 3, 'header_row_number': 1,
                  'header': ['agency', 'name', 'region', 'description', 'city', 'state', 'timezone', 'agencyCode', 'priority', 'agencyID'],
                  'row_content': ['agency', '', 'regtest86', 'test agency', 'Eugene', 'OR', 'Pacific', '111', 'High', '111']}

