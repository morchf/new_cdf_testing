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

def test_vps_ls():
    # get list of VPS for selected customer
    print("test1")


# get list of VPS for existing selected customer
def test_list_vps():
    url = conftest.VPS_URL +'/vps?customerName=SFMTA'
    
    response = requests.get(url)
    assert response.status_code == 200
    print("listing all vps for customer xxx......")
    print(response.text)

# get list of VPS for none existing selected customer
def test_list_vps_none_customer():
    url = conftest.VPS_URL +'/vps?customerName=NoneCustomer'
    
    response = requests.get(url)
    assert response.status_code == 404
    print("listing all vps for customer xxx......")
    print(response.text)

 # get list of VPS for all existing selected customer
def test_list_vps_all():
    url = conftest.VPS_URL +'/vps?customerName=""'
    response = requests.get(url)
    assert response.status_code == 404
    

# create 5 VPS instance for a selected customer (End_To_End_Automation)
#@pytest.mark.skip
def test_create_vps():
    with open('testdata/CreateVPSEndToEndAuto.json') as f:
        data = json.load(f)
        data_json_str = json.dumps(data)
        f.close()
    
    url = conftest.VPS_URL +'/vps'
    r = requests.post(url, headers=conftest.HEADERS, data=data_json_str)
    
    print(data_json_str)
    print("\n API SUCCESSFUL creating records in dynamoDB")
    assert r.status_code == 200

# Attempt to create VPS instance for a none existing customer
def test_create_vps_customer_blank():
    with open('testdata/CreateCustomerBlank.json') as f:
        data = json.load(f)
        data_json_str = json.dumps(data)
        f.close()
    
    url = conftest.VPS_URL +'/vps'
    r = requests.post(url, headers=conftest.HEADERS, data=data_json_str)
    
    print(data_json_str)
    print("\n API SUCCESSFUL creating records in dynamoDB")
    assert r.status_code == 502

# Attempt to create zero VPS instance for an existing customer
def test_create_vps_zero():
    with open('testdata/CreateVPSNumberZero.json') as f:
        data = json.load(f)
        data_json_str = json.dumps(data)
        f.close()
    
    url = conftest.VPS_URL +'/vps'
    r = requests.post(url, headers=conftest.HEADERS, data=data_json_str)
    
    print(data_json_str)
    print("\n API SUCCESSFUL creating records in dynamoDB")
    assert r.status_code == 429


#update a selected vps by changing "deviceStatus": fron "ACTIVE" to Inactive
def test_update_vps():
    with open('testdata/UpdateVPSEndToEnd.json') as f:
        data = json.load(f)
        data_json_str = json.dumps(data)
        f.close()

    url = conftest.VPS_URL +'/vps'    
    r = requests.put(url, headers=conftest.HEADERS, data=data_json_str)
                        
    print(r.content)
    assert r.status_code == 200
                         
#Delete vps by setting the value "markToDelete": "YES"
def test_delete():
    with open('testdata/DeleteVPSEndToEnd.json') as f:
        data = json.load(f)
        data_json_str = json.dumps(data)
        f.close()

    url = conftest.VPS_URL +'/vps'    
    r = requests.put(url, headers=conftest.HEADERS, data=data_json_str)
                     
    print(r.content)
    assert r.status_code == 200

def test_cms_config():
    url = "https://rhbam9tilc.execute-api.us-east-1.amazonaws.com/Prod/cms/devices/deviceConfig"
    payload = "jurisdiction name,location name,location id,comm device type,latitude,longitude\r\nAUSTIN,Intersection13071,2081,TCP/IP,1.012445,-1.987554\r\nAUSTIN,Intersection13072,2082,TCP/IP,1.012545,-1.987454\r\nAUSTIN,Intersection13073,2083,TCP/IP,1.012645,-1.987354\r\nAUSTIN,Intersection13074,2084,TCP/IP,1.012745,-1.987254\r\nAUSTIN,Intersection13075,2085,TCP/IP,1.012845,-1.987154"
    headers = {
    'Content-Type': 'application/csv'
    }

    response = requests.request("POST", url, headers=headers, data = payload)

    print(response.text.encode('utf8'))

    assert response.status_code == 200

def test_deployVPS():
    time.sleep(10)
    vps_deploy_lambda_trigger
