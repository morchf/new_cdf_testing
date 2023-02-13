#!/usr/bin/env python

import boto3
import json
from status import (
    DEVICE_STATUS_EXISTS,
    DEVICE_STATUS_DOES_NOT_EXIST,
)
from asset_lib import device_create, device_read, device_write, device_delete
from aws_cert_auth import del_dev

log = True


def check_content(rc_input, read_ps_content):
    rc = False
    if rc_input >= 200 and rc_input < 300:
        if read_ps_content:
            try:
                ps_content_json_obj = json.loads(read_ps_content)
                print(ps_content_json_obj)
                rc = True
            except:
                if log:
                    print(
                        f"check_content - rc_input = {rc}, read_ps_content = {read_ps_content}"
                    )
                pass
        elif log:
            print(
                f"check_content - rc_input = {rc}, read_ps_content= {read_ps_content}"
            )
    elif log:
        print(f"check_content - rc_input = {rc}, read_ps_content= {read_ps_content}")
    return rc


class Phaseselector:
    def __init__(self, region_name, agency_name, ps_name):
        self.region_name = region_name
        self.agency_name = agency_name
        self.ps_name = ps_name
        self.iot = boto3.client("iot")
        self.s3 = boto3.client("s3")
        self.refresh()

    def create(self, ps_json):
        if log:
            print(f"****** Phase Selector create = {self.ps_name} *****")
        self.refresh()
        if self.status == DEVICE_STATUS_DOES_NOT_EXIST:
            self.http_code, self.http_content = device_create(ps_json)
            self.refresh()

    def delete(self):
        if log:
            print(f"****** Phase Selector delete = {self.ps_name} *****")
        self.refresh()
        if self.status != DEVICE_STATUS_DOES_NOT_EXIST:
            self.http_response, self.http_content = device_delete(self.ps_name)
            self.refresh()
        if self.status == DEVICE_STATUS_DOES_NOT_EXIST:
            del_dev(self.agency_name, self.ps_name)
            self.refresh()

    def write(self, write_json):
        if log:
            print(f"****** Phase Selector write = {self.ps_name} *****")
        self.refresh()
        if self.status != DEVICE_STATUS_DOES_NOT_EXIST:
            self.http_response, self.http_content = device_write(
                self.ps_name, write_json
            )
            self.refresh()

    """
        Refresh ps json and status.  Refresh() is effectively a read function because
        the json is updated with latest values.
        If something goes wrong with the Agency() in which the ps is or will be a member of, then
        errors are propagated up.
        If ps does not exist in asset lib then json is None and
        status is DEVICE_STATUS_DOES_NOT_EXIST.
        If ps does exist in asset lib, then verification of device cert and cert policy are performend.
        Both device cert and policy are in IoT Core.
    """

    def refresh(self):
        if log:
            print(f"****** Phase Selector refresh = {self.ps_name} *****")
        rc, read_ps_content = device_read(self.ps_name)
        if check_content(rc, read_ps_content):

            ps_content_json_obj = json.loads(read_ps_content)
            ps_attributes_json_obj = ps_content_json_obj.get("attributes", None)

            if not ps_attributes_json_obj:
                if log:
                    print(
                        f"HTTP response no attributes. ps_attributes_json_obj = {ps_attributes_json_obj}"
                    )
                self.status = DEVICE_STATUS_DOES_NOT_EXIST

            else:
                self.status = DEVICE_STATUS_EXISTS
        else:
            if log:
                print(f"HTTP Error, rc = {rc}, read_ps_content = {read_ps_content}")
            self.status = DEVICE_STATUS_DOES_NOT_EXIST
