import json
import logging
import os
from typing import (
    Annotated,
    ClassVar,
    ForwardRef,
    List,
    Literal,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Union,
)

import boto3
import requests
from botocore.client import ClientError
from botocore.compat import quote
from pydantic import Field, HttpUrl, PrivateAttr, parse_obj_as, parse_raw_as
from requests_aws_sign import AWSV4Sign

import gtt.data_model.asset_library

__all__ = [
    "Region",
    "Agency",
    "Vehicle",
    "Communicator",
    "IntegrationCom",
    "AssetLibraryAPI",
]

# extend group/device classes to add bi-directionality
Region = ForwardRef("Region")
Agency = ForwardRef("Agency")
Vehicle = ForwardRef("Vehicle")
Communicator = ForwardRef("Communicator")
IntegrationCom = ForwardRef("IntegrationCom")
Group = ForwardRef("Group")
Device = ForwardRef("Device")


class URLNotFoundError(Exception):
    pass


class AssetLibraryAPI:
    """A wrapper around the requests library to handle endpoints and encoding

    Upon initialization it gets the api endpoint using `boto3` if not provided in the
    constructor or the ASSET_LIBRARY_API environment variable. When AWS
    authorization is added, it will use `boto3` and `requests_aws_sign` to add an
    AWSV4 signature to requests for role-based authentication

    Args:
        url (HttpUrl):
            url to asset_library_api. Required if env ASSET_LIBRARY_URL not set
        region (str):
            region for boto3 queries. Defaults to `boto3.session.Session().region_name`
    """

    _cfn_stack_name = "CDFDeploymentPipelineStack-SAM"
    _cfn_url_output_name = "AssetLibraryURL"

    _headers = {
        "Accept": "application/vnd.aws-cdf-v2.0+json",
        "Content-Type": "application/vnd.aws-cdf-v2.0+json",
    }

    def __init__(self, url: str = None, region: str = None):
        session = boto3.Session()
        self._region = region or session.region_name
        self._auth = AWSV4Sign(session.get_credentials(), self._region, "execute-api")
        self.url = (
            url or os.environ.get("ASSET_LIBRARY_URL") or self._find_url(self._region)
        )

        # set the _api class variable in the bidirectional models to use this instance
        Region._api = self
        Agency._api = self
        Vehicle._api = self
        Communicator._api = self
        IntegrationCom._api = self

    def _find_url(self, region: str):
        """Internal function to find AssetLibraryAPI URL using boto3"""
        api_id = self._find_api_id()
        return f"https://{api_id}.execute-api.{region}.amazonaws.com/Prod"

    def _find_api_id(self):
        api_gatway = boto3.client("apigateway")
        api_name = "cdf-assetlibrary-stage"
        try:
            paginator = api_gatway.get_paginator("get_rest_apis")
            for page in paginator.paginate():
                matches = [item for item in page["items"] if item["name"] == api_name]
                if matches:
                    api_id = matches[0]["id"]
                    logging.info(f"Found ID {api_id} for API {api_name}.")
                    return api_id
            raise URLNotFoundError
        except (ClientError, URLNotFoundError):
            logging.error(f"Couldn't find ID for API {api_name}.")
            raise

    def _send_request(
        self,
        url: HttpUrl,
        method: Literal["POST", "GET", "PUT", "PATCH", "DELETE"] = "GET",
        params: Union[Sequence[Tuple[str, str]], Mapping] = None,
        data: dict = None,
    ) -> bytes:
        """Internal function to handle requests to the Asset Library API"""
        # ToDo: handle TimeoutError
        response = requests.request(
            method,
            url,
            params=params,
            json=data,
            headers=self._headers,
            auth=self._auth,
        )

        if response.status_code >= 400:
            logging.debug(
                f"Invalid Asset Library response. url={response.url}, status_code={response.status_code}, headers={response.headers}, content={response.content}"
            )
        return response

    # returns instantiated agency/region
    def get_group(self, group_path: str) -> Group:
        """generate instantiated agency/region by querying asset library
        Args:
            group_path (str):
                asset library groupPath to directly access the group

        Note that the search api accepts other comparisons than equals, but this
        function forces equality to be used, and only works with strings. This could
        be expanded if needed.
        Returns:
            group: instantiated agency/region
        """

        # urlencode the group_path to handle /
        group_path = quote(group_path, safe="")
        group_url = f"{self.url}/groups/{group_path}"
        logging.debug(f"attempting to query using group_path: {group_url}")

        response = self._send_request(url=group_url)
        if response.status_code >= 400:
            raise ValueError(
                f"Invalid Asset Library response. {response.status_code=}, {response.content=}"
            )

        group_dict = json.loads(response.content)
        group_dict["api"] = self

        return parse_obj_as(Group, group_dict)

    def find_group_path(self, template_id: str, **search_params):
        """returns the group_path that could be passed to get_group
        Args:
            template_id (str):
                asset library id to directly access the associated template
            kwargs (dict):
                dictionary of attributes to use search api. [more on filter params](https://github.com/aws/aws-connected-device-framework/blob/main/source/packages/services/assetlibrary/docs/swagger.yml#L195)
        Note that the search api accepts other comparisons than equals, but this
        function forces equality to be used, and only works with strings. This could
        be expanded if needed.
        Returns:
            group_path: asset library groupPath to directly access the group
        """
        # convert to dictionary of attribute fields/values to 2-tuple
        # note that the keys and format of search_attributes is not checked
        params = [
            ("type", template_id),
            *[("eq", f"{k}:{v}") for k, v in search_params.items()],
        ]

        logging.debug(f"attempting to query using search: {search_params}")
        # manually parse to get the group_path
        search_url = f"{self.url}/search"
        response = self._send_request(url=search_url, params=params)
        if response.status_code >= 400:
            raise ValueError(
                f"Invalid Asset Library response. {response.status_code=}, {response.content=}"
            )
        search_dict = json.loads(response.content, strict=False)

        count = search_dict["pagination"]["count"]
        if count != 1:
            raise ValueError(
                f"provided search_attributes returned {'no' if count == 0 else 'multiple'} results"
            )

        # return the discovered group_path
        return search_dict["results"][0]["groupPath"]

    def get_region(self, region_name: str) -> Region:
        """generate instantiated region by querying asset library
        Args:
            region_name (str):
                string referring to desired region
        Returns:
            region: region associated with given region_name"""
        return self.get_group(f"/{region_name}")

    def get_agency(self, region_name: str, agency_name: str) -> Agency:
        """generate instantiated agency by querying asset library
        Args:
            region_name (str):
                string referring to desired region
            agency_name (str):
                string referring to desired agency
        Returns:
            region: region associated with given region_name"""
        return self.get_group(f"/{region_name}/{agency_name}")

    def get_agency_by_id(self, agency_id: str) -> Agency:
        """generate instantiated agency by querying asset library using unique_id
        Args:
            agency_id (UUID):
                agency's agencyID field
        Returns:
            agency: agency with given agency_id"""
        return self.get_group(self.find_group_path("agency", agencyID=agency_id))

    def get_device(self, device_id: str) -> Device:
        """generate instantiated device (vehicle/communicator/integrationcom) by
        querying asset library
        Args:
            device_id (str):
                asset library id to directly access the device

        Note that the search api accepts other comparisons than equals, but this
        function forces equality to be used, and only works with strings. This could
        be expanded if needed.
        Returns:
            device: instantiated device
        """
        # query using device_id
        device_url = f"{self.url}/devices/{device_id}"
        logging.debug(f"attempting to query using device_id: {device_url}")

        response = self._send_request(url=device_url)

        return parse_raw_as(Device, response.content)

    def find_device_id(self, template_id: str, **search_params):
        """returns the device_id that could be passed to get_device
        Args:
            template_id (str):
                asset library id to directly access the associated template
            kwargs (dict):
                dictionary of attributes to use search api. [more on filter params](https://github.com/aws/aws-connected-device-framework/blob/main/source/packages/services/assetlibrary/docs/swagger.yml#L195)
        Note that the search api accepts other comparisons than equals, but this
        function forces equality to be used, and only works with strings. This could
        be expanded if needed.
        Returns:
            device_id: asset library deviceID to directly access the device
        """
        # convert to dictionary of attribute fields/values to 2-tuple
        # note that the keys and format of search_attributes is not checked
        params = [
            ("type", template_id),
            *[("eq", f"{k}:{v}") for k, v in search_params.items()],
        ]

        logging.debug(f"attempting to query using search: {search_params}")
        # manually parse and re-query since groups/devices
        # are not included when using the search api
        search_url = f"{self.url}/search"
        response = self._send_request(url=search_url, params=params)
        if response.status_code >= 400:
            raise ValueError(
                f"Invalid Asset Library response. {response.status_code=}, {response.content=}"
            )
        search_dict = json.loads(response.content, strict=False)

        count = search_dict["pagination"]["count"]
        if count != 1:
            raise ValueError(
                f"provided search_attributes returned {'no' if count == 0 else 'multiple'} results"
            )

        # return the discovered device_id
        return search_dict["results"][0]["deviceId"]

    def get_vehicle(self, device_id: str):
        """generate instantiated vehicle by querying asset library
        Args:
            device_id (str):
                string referring to desired vehicle
        Returns:
            vehicle: vehicle associated with given device_id"""
        return self.get_device(device_id)

    def get_integration_com(self, device_id: str):
        """generate instantiated integration_com by querying asset library
        Args:
            device_id (str):
                string referring to desired integration_com
        Returns:
            integration_com: integration_com associated with given device_id"""
        return self.get_device(device_id)


class Region(gtt.data_model.asset_library.Region):
    """A service class for the Region data model, facilitates queries
    to the Asset Library for the agencies associated with the Region"""

    api: AssetLibraryAPI

    _url: str = None
    _agencies: List[Agency] = None

    @property
    def url(self) -> str:
        if not self._url:
            self._url = f"{self.api.url}/groups/{quote(self.group_path, safe='')}"
        return self._url

    @property
    def agencies(self) -> List[Agency]:
        """returns a list of agencies associated with the Region"""
        if not self._agencies:
            members_url = f"{self.url}/members/groups"
            members = json.loads(self.api._send_request(url=members_url), strict=False)
            self._agencies = [
                self._api.get_group(group["groupPath"]) for group in members["results"]
            ]
        return self._agencies

    class Config:
        arbitrary_types_allowed = True


class Agency(gtt.data_model.asset_library.Agency):
    """A service class for the Agency data model, facilitates queries
    to the Asset Library for the region or devices associated with
    the Agency"""

    api: AssetLibraryAPI

    _url: str = None
    _region: Region = None
    _devices: List[Device] = None

    @property
    def url(self) -> str:
        if not self._url:
            self._url = f"{self.api.url}/groups/{quote(self.group_path, safe='')}"
        return self._url

    @property
    def region(self) -> Region:
        """returns the Region associated with the Agency"""
        if not self._region:
            self._region = self.api.get_group(self.parent_path)
        return self._region

    @property
    def devices(self) -> List[Device]:
        """returns a list of devices (Vehicles, Communicators, and/or IntegrationComs
        associated with the Agency"""
        if not self._devices:
            member_devices_url = f"{self.url}/members/devices"
            member_devices = json.loads(
                self.api._send_request(url=member_devices_url).content,
                strict=False,
            )
            self._devices = [
                self.api.get_device(device["deviceId"])
                for device in member_devices["results"]
            ]
        return self._devices

    class Config:
        arbitrary_types_allowed = True


class Vehicle(gtt.data_model.asset_library.Vehicle):
    """A service class for the Vehicle data model, facilitates queries
    to the Asset Library for the installed devices associated with
    the Vehicle"""

    _api: ClassVar = None
    _installed_devices: List[Device] = None

    @property
    def installed_devices(self) -> List[Union[Communicator, IntegrationCom]]:
        """returns a list of the installed devices (Communicators, IntegrationComs)
        associated with the Vehicle"""
        if not self._api:
            Vehicle._api = AssetLibraryAPI()
        self._installed_devices = self._installed_devices or [
            self._api.get_device(device_id) for device_id in self.installed_device_ids
        ]
        return self._installed_devices


class Communicator(gtt.data_model.asset_library.Communicator):
    """A service class for the Communicator data model, facilitates queries
    to the Asset Library for the vehicle associated with the Communicator"""

    _api: ClassVar = None
    _vehicle: Optional[Vehicle] = PrivateAttr(default=None)

    @property
    def vehicle(self) -> Vehicle:
        """returns the vehicle associated with the Communicator"""
        if not self._api:
            Communicator._api = AssetLibraryAPI()
        # handle case where communicator not yet associated to a vehicle
        if not self.vehicle_id:
            return None
        self._vehicle = self._vehicle or self._api.get_device(self.vehicle_id)
        return self._vehicle


class IntegrationCom(gtt.data_model.asset_library.IntegrationCom):
    """A service class for the IntegrationCom data model, facilitates queries
    to the Asset Library for the vehicle associated with the IntegrationCom"""

    _api: ClassVar = None
    _vehicle: Optional[Vehicle] = PrivateAttr(default=None)

    @property
    def vehicle(self) -> Vehicle:
        """returns the vehicle associated with the IntegrationCom"""
        if not self._api:
            IntegrationCom._api = AssetLibraryAPI()
        # handle case where integration_com not yet associated to a vehicle
        if not self.vehicle_id:
            return None
        self._vehicle = self._vehicle or self._api.get_device(self.vehicle_id)
        return self._vehicle


Group = Annotated[
    Union[Region, Agency], Field(discriminator="template_id")  # noqa F821
]

Device = Annotated[
    Union[Vehicle, Communicator, IntegrationCom],
    Field(discriminator="template_id"),  # noqa F821
]
