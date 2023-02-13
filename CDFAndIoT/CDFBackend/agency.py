#!/usr/bin/env python

import boto3
import json
from iot_core import register_thing, remove_thing
from status import (
    AGENCY_STATUS_EXISTS,
    AGENCY_STATUS_DOES_NOT_EXIST,
    AGENCY_STATUS_NO_CA_IN_ASSET_LIB,
    AGENCY_STATUS_NO_CA_IN_IOT_CORE,
    AGENCY_STATUS_NO_VPS_CERT,
    AGENCY_STATUS_NO_VPS_CERT_IN_ASSET_LIB,
    AGENCY_STATUS_NO_2100_CERT_IN_ASSET_LIB,
    AGENCY_STATUS_NO_VPS_CERT_IN_IOT_CORE,
)
from asset_lib import agency_create, agency_read, agency_write, agency_delete
from aws_cert_auth import new_sub_ca, del_sub_ca, new_dev, del_dev, get_cert_id

log = True


def check_content(rc_input, agency_content_json_obj):
    rc = False
    if type(agency_content_json_obj) == dict:
        if agency_content_json_obj.get("attributes", None):
            if rc_input >= 200 and rc_input < 300:
                rc = True
            elif log:
                print(
                    f"check_content - rc_input = {rc}, "
                    f"agency_content_json_obj = {agency_content_json_obj}"
                )
        elif log:
            print(
                f"check_content - rc_input = {rc}, "
                f"agency_content_json_obj = {agency_content_json_obj}"
            )
    elif log:
        print(
            f"check_content - rc_input = {rc}, "
            f"agency_content_json_obj = {agency_content_json_obj}"
        )
    return rc


"""
Class for an agency: create, delete, write, refresh.

All functions interfaced with asset library, IOT Core, and KMS.
"""


class Agency:
    def __init__(self, region_name, agency_name):
        self.region_name = region_name
        self.agency_name = agency_name
        self.vps_name = "vps"
        self.vps_cert_name = f"{self.agency_name.upper()}_{self.vps_name.upper()}"
        self.name_2100 = "2100"
        self.cert_2100_name = f"{self.agency_name.upper()}_{self.name_2100}"
        self.name = f"{self.region_name.upper()}_{self.agency_name.upper()}_SUBCA"
        self.ca_present = False
        self.cert_present = False
        self.iot = boto3.client("iot")
        self.s3 = boto3.client("s3")
        self.refresh()

    def create(self, agency_json):
        prefix = self.region_name.upper() + "/AGENCIES/" + self.agency_name.upper()
        if log:
            print(f"****** Agency create = {self.agency_name} *****")
        self.refresh()
        if self.status == AGENCY_STATUS_DOES_NOT_EXIST:
            self.http_code, self.http_content = agency_create(
                self.agency_name, agency_json
            )
            self.refresh()
        if self.status == AGENCY_STATUS_NO_CA_IN_ASSET_LIB:
            rc = new_sub_ca(self.region_name, self.agency_name)
            if rc:
                caCertId = get_cert_id(self.name, prefix)
                if log:
                    print(f"\n Agency cert id = {caCertId}\n")
                write_cert_id_json = (
                    f'{{ "attributes": {{ "caCertId": "{caCertId}" }} }}'
                )
                self.write(write_cert_id_json)
            self.refresh()
        if self.status == AGENCY_STATUS_NO_VPS_CERT_IN_ASSET_LIB:
            rc = new_dev(self.region_name, self.agency_name, self.vps_name)
            prefix += "/DEVICES"
            if rc:
                vpsCertId = get_cert_id(self.vps_cert_name, prefix)
                write_cert_id_json = (
                    f'{{ "attributes": {{ "vpsCertId": "{vpsCertId}" }} }}'
                )
                self.write(write_cert_id_json)

                register_thing(self.vps_cert_name, vpsCertId)
            self.refresh()
        if self.status == AGENCY_STATUS_NO_2100_CERT_IN_ASSET_LIB:
            rc = new_dev(self.region_name, self.agency_name, self.name_2100)
            if rc:
                Cert2100Id = get_cert_id(self.cert_2100_name, prefix)
                write_cert_id_json = (
                    f'{{ "attributes": {{ "Cert2100Id": "{Cert2100Id}" }} }}'
                )
                self.write(write_cert_id_json)
                register_thing(self.cert_2100_name, Cert2100Id)
            self.refresh()

    def delete(self):
        prefix = (
            self.region_name.upper()
            + "/AGENCIES/"
            + self.agency_name.upper()
            + "/DEVICES"
        )
        if log:
            print(f"****** Agency delete = {self.agency_name} *****")
        self.refresh()
        if self.status != AGENCY_STATUS_DOES_NOT_EXIST:
            self.http_response, self.http_content = agency_delete(
                self.region_name, self.agency_name
            )
            self.refresh()
        if self.status == AGENCY_STATUS_DOES_NOT_EXIST:
            del_sub_ca(self.region_name, self.agency_name)
            self.refresh()
            vpsCertId = get_cert_id(self.vps_cert_name, prefix)
            # remove VPS cert, thing, and policy from IoT Core
            remove_thing(self.vps_cert_name, vpsCertId)
            # delete VPS cert
            del_dev(self.region_name, self.agency_name, self.vps_name)

            Cert2100Id = get_cert_id(self.cert_2100_name, prefix)
            # remove 2100 cert, thing, and policy from IoT Core
            remove_thing(self.cert_2100_name, Cert2100Id)
            del_dev(self.region_name, self.agency_name, self.name_2100)

    def write(self, write_json):
        if log:
            print(f"****** Agency write = {self.agency_name} *****")
        self.refresh()
        if self.status != AGENCY_STATUS_DOES_NOT_EXIST:
            self.http_response, self.http_content = agency_write(
                self.region_name, self.agency_name, write_json
            )
            self.refresh()

    """
        Refresh agency json and status. Refresh() is effectively a read function because
        the json is updated with latest values.

        If agency does not exist in asset lib then json is None and
        status is AGENCY_STATUS_DOES_NOT_EXIST.

        If agency does exist in asset lib, then verification of CA and
        private key are performed.
    """

    def refresh(self):
        if log:
            print(f"****** Agency refresh = {self.agency_name} *****")

        rc, read_agency_content = agency_read(self.region_name, self.agency_name)
        agency_content_json_obj = json.loads(read_agency_content)

        if not check_content(rc, agency_content_json_obj):
            if log:
                print(
                    f"HTTP Error, rc = {rc}, "
                    f"agency_content_json_obj = {agency_content_json_obj}"
                )
            self.status = AGENCY_STATUS_DOES_NOT_EXIST
            return

        agency_attributes_json_obj = agency_content_json_obj.get("attributes", None)

        if not agency_content_json_obj:
            if log:
                print(
                    f"HTTP response no attributes. "
                    f"agency_attributes_json_obj = {agency_attributes_json_obj}"
                )
            self.status = AGENCY_STATUS_DOES_NOT_EXIST
            return

        caCertId = agency_attributes_json_obj.get("caCertId", "NULL_CA")

        if caCertId == "NULL_CA":
            if log:
                print(
                    f"HTTP response no caCertId. caCertId = {caCertId}. "
                    f"agency_attributes_json_obj = {agency_attributes_json_obj}"
                )
            self.status = AGENCY_STATUS_NO_CA_IN_ASSET_LIB
            return

        if not self.ca_present:
            # self-signed CA cert id is written in asset lib but not IoT Core
            try:
                # Exception thrown if cert id not registered in IoT Core
                self.iot.describe_ca_certificate(certificateId=caCertId)
                self.ca_present = True
            except Exception as e:
                if log:
                    print(f"Cert id not in IoT Core. ca_cert_id = {caCertId}")
                    print(f"Exception = {str(e)}")
                self.ca_present = False
            if self.ca_present:
                self.status = AGENCY_STATUS_NO_VPS_CERT
            else:
                self.status = AGENCY_STATUS_NO_CA_IN_IOT_CORE
            return

        vpsCertId = agency_attributes_json_obj.get("vpsCertId", "NULL_CERT")

        if vpsCertId == "NULL_CERT":
            if log:
                print(
                    f"HTTP response no vpsCertId. vpsCertId = {vpsCertId}. "
                    f"agency_attributes_json_obj = {agency_attributes_json_obj}"
                )
            self.status = AGENCY_STATUS_NO_VPS_CERT_IN_ASSET_LIB
            return

        Cert2100Id = agency_attributes_json_obj.get("Cert2100Id", "NULL_CERT")
        if Cert2100Id == "NULL_CERT":
            if log:
                print(
                    f"HTTP response no Cert2100Id. Cert2100Id = {Cert2100Id}. "
                    f"agency_attributes_json_obj = {agency_attributes_json_obj}"
                )
            self.status = AGENCY_STATUS_NO_2100_CERT_IN_ASSET_LIB
            return

        if not self.cert_present:
            # vps cert id is written in asset lib but not IoT Core
            try:
                # Exception thrown if cert id not registered in IoT Core
                self.iot.describe_certificate(certificateId=vpsCertId)
                self.cert_present = True
            except Exception as e:
                if log:
                    print(f"VPS cert id not in IoT Core. vpsCertId = {vpsCertId}")
                    print(f"Exception = {str(e)}")
                self.cert_present = False
            if self.cert_present:
                self.status = AGENCY_STATUS_EXISTS
            else:
                self.status = AGENCY_STATUS_NO_VPS_CERT_IN_IOT_CORE

        return

    def old_refresh(self):
        if log:
            print(f"****** Agency refresh = {self.agency_name} *****")
        rc, read_agency_content = agency_read(self.region_name, self.agency_name)
        agency_content_json_obj = json.loads(read_agency_content)

        if check_content(rc, agency_content_json_obj):
            agency_attributes_json_obj = agency_content_json_obj.get("attributes", None)

            if agency_attributes_json_obj:

                # Agency of 'agency_name' exists
                caCertId = agency_attributes_json_obj.get("caCertId", "NULL_CA")
                if caCertId != "NULL_CA":

                    # self-signed CA cert id is written in asset lib
                    try:
                        # Exception thrown if cert id not registered in IoT Core
                        self.iot.describe_ca_certificate(certificateId=caCertId)
                        ca_present = True
                    except Exception as e:
                        if log:
                            print(f"Cert id not in IoT Core. ca_cert_id = {caCertId}")
                            print(f"Exception = {str(e)}")
                        ca_present = False
                    if ca_present:
                        self.status = AGENCY_STATUS_EXISTS
                    else:
                        self.status = AGENCY_STATUS_NO_CA_IN_IOT_CORE
                else:
                    if log:
                        print(
                            f"HTTP response no ca_cert_id. ca_cert_id = {caCertId}. "
                            f"agency_attributes_json_obj = {agency_attributes_json_obj}"
                        )
                    self.status = AGENCY_STATUS_NO_CA_IN_ASSET_LIB
            else:
                if log:
                    print(
                        f"HTTP response no attributes. "
                        f"agency_attributes_json_obj = {agency_attributes_json_obj}"
                    )
                self.status = AGENCY_STATUS_DOES_NOT_EXIST
        else:
            if log:
                print(
                    f"HTTP Error, rc = {rc}, "
                    f"agency_content_json_obj = {agency_content_json_obj}"
                )
            self.status = AGENCY_STATUS_DOES_NOT_EXIST
