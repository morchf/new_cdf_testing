#!/usr/bin/env python

import json
from status import DEVICE_STATUS_EXISTS, DEVICE_STATUS_DOES_NOT_EXIST
from asset_lib import device_create, device_read, device_write, device_delete

log = True


def check_content(rc_input, read_vehicle_content):
    rc = False
    if rc_input >= 200 and rc_input < 300:
        if read_vehicle_content:
            try:
                json.loads(read_vehicle_content)
                rc = True
            except:
                if log:
                    print(
                        f"check_content - rc_input = {rc}, read_vehicle_content = {read_vehicle_content}"
                    )
                pass
        elif log:
            print(
                f"check_content - rc_input = {rc}, read_vehicle_content= {read_vehicle_content}"
            )
    elif log:
        print(
            f"check_content - rc_input = {rc}, read_vehicle_content= {read_vehicle_content}"
        )
    return rc


class Vehicle:
    def __init__(self, region_name, agency_name, vehicle_name):
        self.region_name = region_name
        self.agency_name = agency_name
        self.vehicle_name = vehicle_name
        self.refresh()

    def create(self, vehicle_json):
        if log:
            print(f"****** Vehicle create = {self.vehicle_name} *****")
        self.refresh()
        if self.status == DEVICE_STATUS_DOES_NOT_EXIST:
            self.http_code, self.http_content = device_create(vehicle_json)
            self.refresh()

    def delete(self):
        if log:
            print(f"****** Vehicle delete = {self.vehicle_name} *****")
        self.refresh()
        if self.status != DEVICE_STATUS_DOES_NOT_EXIST:
            self.http_response, self.http_content = device_delete(self.vehicle_name)
            self.refresh()

    def write(self, write_json):
        if log:
            print(f"****** Vehicle write = {self.vehicle_name} *****")
        self.refresh()
        if self.status != DEVICE_STATUS_DOES_NOT_EXIST:
            self.http_response, self.http_content = device_write(
                self.vehicle_name, write_json
            )
            self.refresh()

    """
        Refresh vehicle json and status.  Refresh() is effectively a read function because
        the json is updated with latest values.

        If something goes wrong with the Agency() in which the vehicle is or will be a member of, then
        errors are propagated up.

        If vehicle does not exist in asset lib then json is None and status is DEVICE_STATUS_DOES_NOT_EXIST.
    """

    def refresh(self):
        if log:
            print(f"****** Vehicle refresh = {self.vehicle_name} *****")
        rc, read_vehicle_content = device_read(self.vehicle_name)
        if check_content(rc, read_vehicle_content):

            vehicle_content_json_obj = json.loads(read_vehicle_content)
            vehicle_attributes_json_obj = vehicle_content_json_obj.get(
                "attributes", None
            )

            if vehicle_attributes_json_obj:
                self.status = DEVICE_STATUS_EXISTS
            else:
                if log:
                    print(
                        f"HTTP response no attributes. vehicle_attributes_json_obj = {vehicle_attributes_json_obj}"
                    )
                self.status = DEVICE_STATUS_DOES_NOT_EXIST
        else:
            if log:
                print(
                    f"HTTP Error, rc = {rc}, read_vehicle_content = {read_vehicle_content}"
                )
            self.status = DEVICE_STATUS_DOES_NOT_EXIST
