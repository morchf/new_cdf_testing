#!/usr/bin/env python

import boto3
import json
from status import (
    LOCATION_STATUS_EXISTS,
    LOCATION_STATUS_DOES_NOT_EXIST,
)
from asset_lib import location_create, location_read, location_write, location_delete

log = True


def check_content(rc_input, location_content_json_obj):
    rc = False
    print(
        f"check_content - rc_input = {rc}, location_content_json_obj = {location_content_json_obj}"
    )
    if type(location_content_json_obj) == dict:
        if location_content_json_obj.get("attributes", None):
            if rc_input >= 200 and rc_input < 300:
                rc = True
            elif log:
                print(
                    f"check_content - rc_input = {rc}, location_content_json_obj = {location_content_json_obj}"
                )
        elif log:
            print(
                f"check_content - rc_input = {rc}, location_content_json_obj = {location_content_json_obj}"
            )
    elif log:
        print(
            f"check_content - rc_input = {rc}, location_content_json_obj = {location_content_json_obj}"
        )
    return rc


"""
Class for an location: create, delete, write, refresh.

All functions interfaced with asset library, IOT Core, and KMS.
"""


class Location:
    def __init__(self, region_name, agency_name, location_name):
        self.region_name = region_name
        self.agency_name = agency_name
        self.location_name = location_name
        self.iot = boto3.client("iot")
        self.s3 = boto3.client("s3")
        self.refresh()

    def create(self, location_json):
        if log:
            print(f"****** Location create = {self.location_name} *****")
        self.refresh()
        if self.status == LOCATION_STATUS_DOES_NOT_EXIST:
            self.http_code, self.http_content = location_create(
                self.location_name, location_json
            )
            self.refresh()

    def delete(self):
        if log:
            print(f"****** Location delete = {self.location_name} *****")
        self.refresh()
        if self.status != LOCATION_STATUS_DOES_NOT_EXIST:
            self.http_response, self.http_content = location_delete(
                self.region_name, self.agency_name, self.location_name
            )
            self.refresh()
        if self.status == LOCATION_STATUS_DOES_NOT_EXIST:
            self.refresh()

    def write(self, write_json):
        if log:
            print(f"****** Location write = {self.location_name} *****")
        self.refresh()
        if self.status != LOCATION_STATUS_DOES_NOT_EXIST:
            self.http_response, self.http_content = location_write(
                self.region_name, self.agency_name, self.location_name, write_json
            )
            self.refresh()

    """
        Refresh location json and status.  Refresh() is effectively a read function because
        the json is updated with latest values.

        If agency does not exist in asset lib then json is None and
        status is LOCATION_STATUS_DOES_NOT_EXIST.
    """

    def refresh(self):
        if log:
            print(f"****** Location refresh = {self.location_name} *****")

        rc, read_location_content = location_read(
            self.region_name, self.agency_name, self.location_name
        )
        location_content_json_obj = json.loads(read_location_content)
        if check_content(rc, location_content_json_obj):
            location_attributes_json_obj = location_content_json_obj.get(
                "attributes", None
            )
            if not location_attributes_json_obj:
                if log:
                    print(
                        f"HTTP response no attributes. location_attributes_json_obj = {location_attributes_json_obj}"
                    )
                self.status = LOCATION_STATUS_DOES_NOT_EXIST
            else:
                self.status = LOCATION_STATUS_EXISTS
        else:
            if log:
                print(
                    f"HTTP Error, rc = {rc}, location_content_json_obj = {location_content_json_obj}"
                )
            self.status = LOCATION_STATUS_DOES_NOT_EXIST
