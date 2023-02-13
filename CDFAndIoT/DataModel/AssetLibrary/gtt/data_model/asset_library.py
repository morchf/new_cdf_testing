import abc
import logging
from enum import Enum
from ipaddress import IPv4Address
from typing import ForwardRef, List, Literal, Optional

from pydantic import BaseModel, Field, root_validator, validator
from pydantic.types import conint

__all__ = [
    "Region",
    "Agency",
    "Vehicle",
    "IntegrationCom",
    "Communicator",
]

Region = ForwardRef("Region")
Agency = ForwardRef("Agency")
Vehicle = ForwardRef("Vehicle")
Communicator = ForwardRef("Communicator")
IntegrationCom = ForwardRef("IntegrationCom")


class Template(str, Enum):
    Region = "region"
    Agency = "agency"
    Vehicle = "vehiclev2"
    Communicator = "communicator"
    IntegrationCom = "integrationcom"


class AssetLibraryBaseModel(BaseModel):
    """pydantic data model for the Asset Library"""

    @validator("template_id", pre=True, check_fields=False)
    def template_id_in_templates(cls, v) -> Template:
        return Template(v)

    class Config:
        underscore_attrs_are_private = True

    @root_validator(pre=True)
    def flatten_attributes(cls, values):
        logging.debug(f"{values=}")
        # flatten attributes
        if "attributes" in values:
            values.update(values["attributes"])
        return values


class GroupBaseModel(AssetLibraryBaseModel, abc.ABC):
    """pydantic data model for a Group"""

    description: str = None
    category: Literal["group"]
    name: str
    group_path: str = Field(alias="groupPath")
    parent_path: str = Field(alias="parentPath")


class DeviceBaseModel(AssetLibraryBaseModel, abc.ABC):
    """pydantic data model for a Device"""

    description: str = None
    category: Literal["device"]
    state: Literal["active"]
    device_id: str = Field(alias="deviceId")
    # owned_by groups
    region_name: str
    agency_name: str

    @root_validator(pre=True)
    def validate_region_agency(cls, values):
        # get the path to the agency group to parse region/agency
        # when using postman, there is no intermediate field for out/in, handle both
        if "region_name" not in values and "agency_name" not in values:
            owned_by = (values["groups"].get("out") or values["groups"]).get("ownedby")
            # device should only belong to one agency
            assert len(owned_by) == 1
            values["region_name"] = owned_by[0].split("/")[1]
            values["agency_name"] = owned_by[0].split("/")[2]
        return values


class Region(GroupBaseModel):
    """pydantic data model for a Region"""

    template_id: Literal[Template.Region] = Field(alias="templateId")
    # attributes
    ca_cert_id: str = Field(alias="caCertId")
    unique_id: str = Field(alias="regionGUID")  # note name change
    display_name: str = Field(alias="displayName", default=None)


class Agency(GroupBaseModel):
    """pydantic data model for an Agency"""

    template_id: Literal[Template.Agency] = Field(alias="templateId")
    # attributes
    city: str
    state: str
    timezone: Literal["Central", "Mountain", "Eastern", "Pacific", "Arizona"]
    agency_code: conint(ge=1, le=254) = Field(alias="agencyCode")
    unique_id: str = Field(alias="agencyID")  # note name change
    vps_cert_id: str = Field(alias="vpsCertId")
    cert2100_id: str = Field(alias="Cert2100Id", default=None)
    priority: Literal["High", "Low"]
    cms_id: str = Field(alias="CMSId", default=None)
    ca_cert_id: str = Field(alias="caCertId")
    display_name: str = Field(alias="displayName", default=None)
    # groups
    region_name: str
    # member devices requires querying

    @root_validator(pre=True)
    def validate_agency_region_name(cls, values):
        # get parentPath to parse region
        values["region_name"] = values["parentPath"].split("/")[-1]
        return values


class Vehicle(DeviceBaseModel):
    """pydantic data model for a Vehicle"""

    template_id: Literal[Template.Vehicle] = Field(alias="templateId")
    # attributes
    VID: conint(ge=1, le=9999)
    name: str = None
    priority: Literal["High", "Low"]
    type_: str = Field(alias="type", default=None)
    class_: str = Field(alias="class")
    unique_id: str = Field(alias="uniqueId")
    # devices
    installed_device_ids: List[str]

    @root_validator(pre=True)
    def validate_installed_devices(cls, values):
        # when using postman, there is no intermediate field for out/in, handle both
        installed_at = (
            (values["devices"].get("out") or values["devices"]).get("installedat")
            if "devices" in values
            else []
        )
        values["installed_device_ids"] = installed_at
        return values


class Communicator(DeviceBaseModel):
    """pydantic data model for a Communicator"""

    template_id: Literal[Template.Communicator] = Field(alias="templateId")
    # attributes
    serial: str
    gtt_serial: str = Field(alias="gttSerial")
    address_mac: str = Field(alias="addressMAC")
    # ToDo: Figure out string validation for IMEI
    imei: str = Field(alias="IMEI")  # noqa: F722
    address_lan: IPv4Address = Field(alias="addressLAN")
    address_wan: IPv4Address = Field(alias="addressWAN")
    dev_cert_id: Optional[str] = Field(alias="devCertId")
    make: Literal["GTT", "Sierra Wireless", "Cradlepoint"]
    model: Literal[
        "MP-70", "2100", "2101", "2150", "2151", "IBR900", "IBR1700", "R1900"
    ]
    unique_id: str = Field(alias="uniqueId")
    # devices
    vehicle_id: str = None

    @root_validator(pre=True)
    def validate_communicator_installed_at_vehicle(cls, values):
        # when using postman, there is no intermediate field for out/in, handle both
        installed_at = (
            (values["devices"].get("in") or values["devices"]).get("installedat")
            if "devices" in values
            else []
        )
        # device should only be installed at one vehicle
        assert len(installed_at) <= 1
        if installed_at:
            values["vehicle_id"] = installed_at[0]
        return values


class IntegrationCom(DeviceBaseModel):
    """pydantic data model for an IntegrationCom"""

    template_id: Literal[Template.IntegrationCom] = Field(alias="templateId")
    # attributes
    serial: str
    gtt_serial: str = Field(alias="gttSerial")
    address_mac: str = Field(alias="addressMAC")
    unique_id: str = Field(alias="uniqueId")
    license: Literal[
        "pending", "inactive", "active", "decommissioned", "transferred"
    ] = Field(alias="preemptionLicense")
    integration: Literal["Whelen", "Teletrac", "gtfs-realtime", "Misc."]
    # devices
    vehicle_id: str = None

    @root_validator(pre=True)
    def validate_integration_com_installed_at_vehicle(cls, values):
        # when using postman, there is no intermediate field for out/in, handle both
        installed_at = (
            (values["devices"].get("in") or values["devices"]).get("installedat")
            if "devices" in values
            else []
        )
        # device should only be installed at one vehicle
        assert len(installed_at) <= 1
        if installed_at:
            values["vehicle_id"] = installed_at[0]
        return values
