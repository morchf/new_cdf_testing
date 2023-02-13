import os
import re
import pytest
import requests
import random
import json
import time
import conftest
import csv
import vps_deploy_lambda_trigger

def test_get_region():
    #list all region
    url = conftest.new_CDF_URL +'/regions'
    
    response = requests.get(url)
    data = response.text
   # data_json_str = json.dumps(data)
    data_json_object = json.loads(data)
       
    assert response.status_code == 200
    print("listing all regions in CDF")
    #print(response.text)
    for i in data_json_object:
        if i['name'] == 'tsptest':
            x = i['id']
            print(x)
            print(i['id'])
            print(i['name'])
        break
   # print(data_json_object["id"])


def test_get_printme():
    #list all region
    print("just display this value @@@@@@@@@@@@@@@@@@@@")

def test_get_region_data():
    #list all region
    url = conftest.new_CDF_URL +'/region?id=24f65442-af2d-476a-9c32-1148f6c7f2d8'
    
    response = requests.get(url)
    assert response.status_code == 200
    print("listing all region QA_Test_Automation data in CDF")
    print(response.text)
            
def test_read_region(read_Region):
    print("this is the region from conftest file ##########")
    print(read_Region)
    
def test_get_region_agencies(read_Region):
    #list all agency for selected region
    _region = read_Region
    print("this is the AgencyID from conftest")
    print(_region)
   # url = conftest.new_CDF_URL +'/agencies/region?id=f991e14b-2693-43aa-b6b1-3eaff2df6abe'
    url = conftest.new_CDF_URL +'/agencies/region?id=%[_region]'
    response = requests.get(url)
    assert response.status_code == 200
    print("&&&&&&&&&&&&&&&    listing agency of regions QA_Test_Automation in CDF")
    print(response.text)

def test_get_agency_data():

     #list all agency information
    url = conftest.new_CDF_URL +'/agency?id=e9851fb9-0973-4d9f-b430-36b59ccbf908'
    
    response = requests.get(url)
    assert response.status_code == 200
    print("listing all regions in CDF")
    print(response.text)

def test_get_vehicle_data():
    #list all devices for an agency
     
    url = conftest.new_CDF_URL +'/vehicles/agency?id=e9851fb9-0973-4d9f-b430-36b59ccbf908'
    
    response = requests.get(url)
    assert response.status_code == 200
    print("listing all Vehicles for agency GTT_TEST_AGENCY, region GTT_TEST_REGION")
    print(response.text)

def test_get_communicator_data():
    #list all devices for an agency
     
   # url = conftest.new_CDF_URL +'communicators/agency?id=e9851fb9-0973-4d9f-b430-36b59ccbf908'
    url = 'https://c6wn53rywi.execute-api.us-east-1.amazonaws.com/dev/communicators/agency?id=e9851fb9-0973-4d9f-b430-36b59ccbf908'
    response = requests.get(url)
    assert response.status_code == 200
    print("listing all Communicators for agency GTT_TEST_AGENCY, region GTT_TEST_REGION")
    print(response.text)

def test_region_creation():
     # create a new region in CDF
     with open('testdata/new_cdf_crreate_region.json') as f:
        data = json.load(f)
        data_json_str = json.dumps(data)
        f.close()
        url = conftest.new_CDF_URL  +'/region'
        r = requests.post(url, headers=conftest.HEADERS, data=data_json_str)
        print(r.text)
        print("\n API SUCCESSFUL creating records in dynamoDB")
        assert r.status_code == 200
    
   
def test_agency_creation():
     with open('testdata/new_cdf_create_agency.json') as f:
        data = json.load(f)
        data_json_str = json.dumps(data)
        f.close()
        url = conftest.new_CDF_URL  +'/agency'
        r = requests.post(url, headers=conftest.HEADERS, data=data_json_str)
    
        print(data_json_str)
        print("\n API SUCCESSFUL creating records in dynamoDB")
        assert r.status_code == 200
    


def test_vehicle_creation():
     with open('testdata/new_cdf_create_vehicle.json') as f:
        data = json.load(f)
        data_json_str = json.dumps(data)
        f.close()
        url = conftest.new_CDF_URL  +'/vehicle'
        r = requests.post(url, headers=conftest.HEADERS, data=data_json_str)
    
        print(data_json_str)
        print("\n API SUCCESSFUL creating records in dynamoDB")
        print(r.text)
        assert r.status_code == 200
         #include VPS, 2100, MP70 etc

def test_communicator_creation():
    with open('testdata/new_cdf_create_comm.json') as f:
        data = json.load(f)
        data_json_str = json.dumps(data)
        f.close()
    
    url = conftest.new_CDF_URL  +'/communicator'
    r = requests.post(url, headers=conftest.HEADERS, data=data_json_str)
    
    print(data_json_str)
    print("\n API SUCCESSFUL creating records in dynamoDB")
    assert r.status_code == 200
    #include VPS, 2100, MP70 etc

def test_update_region():
    #update region information
   with open('testdata/new_cdf_update_region.json') as f:
        data = json.load(f)
        data_json_str = json.dumps(data)
        f.close()
        url = conftest.new_CDF_URL  +'/region'
        r = requests.put(url, headers=conftest.HEADERS, data=data_json_str)
        assert r.status_code == 200


def test_update_agency():
    #update agency information
    with open('testdata/new_cdf_update_agency.json') as f:
        data = json.load(f)
        data_json_str = json.dumps(data)
        f.close()
        url = conftest.new_CDF_URL  +'/agency'
        r = requests.put(url, headers=conftest.HEADERS, data=data_json_str)
        assert r.status_code == 200

def test_update_vehicle():
    #update agency information
    with open('testdata/new_cdf_update_vehicle.json') as f:
        data = json.load(f)
        data_json_str = json.dumps(data)
        f.close()
        url = conftest.new_CDF_URL  +'/vehicle'
        r = requests.put(url, headers=conftest.HEADERS, data=data_json_str)
        assert r.status_code == 200

def test_update_Comm():
    #update agency information
    with open('testdata/new_cdf_update_comm.json') as f:
        data = json.load(f)
        data_json_str = json.dumps(data)
        f.close()
        url = conftest.new_CDF_URL  +'/communicator'
        r = requests.put(url, headers=conftest.HEADERS, data=data_json_str)
        assert r.status_code == 200

def test_Associate_Device():
    #update agency information
    with open('testdata/new_cdf_Associate_Device.json') as f:
        data = json.load(f)
        data_json_str = json.dumps(data)
        f.close()
        url = conftest.new_CDF_URL  +'/associatedcommunicator/communicator'
        r = requests.put(url, headers=conftest.HEADERS, data=data_json_str)
        assert r.status_code == 200

def test_Dissociate_Device():
    #update agency information
    with open('testdata/new_cdf_Dissociate_Device.json') as f:
        data = json.load(f)
        data_json_str = json.dumps(data)
        f.close()
        url = conftest.new_CDF_URL  +'/dissociatecommunicator'
        r = requests.put(url, headers=conftest.HEADERS, data=data_json_str)
        assert r.status_code == 200

def test_deletion_region():
     with open('testdata/new_cdf_delete_region.json') as f:
        data = json.load(f)
        data_json_str = json.dumps(data)
        f.close()

        url = conftest.new_CDF_URL  +'/region' 
        r = requests.delete(url, headers=conftest.HEADERS, data=data_json_str)
                     
     print(r.content)
     assert r.status_code == 200

def test_deletion_agency():
     with open('testdata/new_cdf_delete_agency.json') as f:
        data = json.load(f)
        data_json_str = json.dumps(data)
        f.close()

        url = conftest.new_CDF_URL  +'/agency' 
        r = requests.delete(url, headers=conftest.HEADERS, data=data_json_str)
                     
        print(r.content)
        assert r.status_code == 200


def test_deletion_vehicle():
     with open('testdata/new_cdf_delete_vehicle.json') as f:
        data = json.load(f)
        data_json_str = json.dumps(data)
        f.close()

        url = conftest.new_CDF_URL  +'/vehicle' 
        r = requests.delete(url, headers=conftest.HEADERS, data=data_json_str)
                     
        print(r.content)
        assert r.status_code == 200


def test_deletion_comm():
     with open('testdata/new_cdf_delete_comm.json') as f:
        data = json.load(f)
        data_json_str = json.dumps(data)
        f.close()

     url = conftest.new_CDF_URL  +'/communicator' 
     r = requests.delete(url, headers=conftest.HEADERS, data=data_json_str)
                     
     print(r.content)
     assert r.status_code == 200


def test_agency_has_caCert():
    {

    }
def test_agency_has_certs():
    {

    }

def test_agency_has_vpsCerts():
    {

    }

   

 # get list of VPS for all existing selected customer