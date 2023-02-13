import os
from typing import Optional, Union
from uuid import UUID

import boto3
import requests
from pydantic import parse_obj_as, parse_raw_as

from gtt.data_model.feature_persistence import (
    AgencyFeatureDict,
    AgencyFeatures,
    Feature,
    FeatureAgencies,
    FeatureName,
    FeatureNameFeatureDict,
    FeaturePersistenceItem,
    GenericFeaturePersistenceItem,
)


class FeaturePersistenceAPI:
    """A wrapper around the requests library to handle endpoints and encoding

    Upon initialization it gets the api endpoint using `boto3` if not provided in the
    constructor or the FEATURE_PERSISTENCE_API environment variable. When AWS
    authorization is added, it will use `boto3` and `requests_aws_sign` to add an
    AWSV4 signature to requests for role-based authentication

    Args:
        url (HttpUrl):
            url to feature_persistence_api. Required if env FEATURE_PERSISTENCE_URL not set
        region (str):
            region for boto3 queries. Defaults to `boto3.session.Session().region_name`
    """

    _cfn_stack_name = "CDFDeploymentPipelineStack-SAM"
    _cfn_url_output_name = "FeaturePersistenceURL"

    _headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    def __init__(self, url=None, region=None):
        self.url = (
            url or os.environ.get("FEATURE_PERSISTENCE_URL") or self._find_url(region)
        )

    def _find_url(self, region=None):
        """Internal function to find FeaturePersistenceAPI URL using boto3"""
        session = boto3.Session(region_name=region)

        # find using CloudFormation exports, ensuring unique
        # cfn_exports = session.client("cloudformation").list_exports()["Exports"]
        # url_exports = [e for e in cfn_exports if e["Name"] == self._cfn_url_output_name]
        # assert (
        #     len(url_exports) == 1
        # ), f"multiple {self._cfn_url_output_name} exports found, {url_exports}"
        # return url_exports[0]["Value"]

        # find using single CloudFormation stack output
        cfn_stack = session.resource("cloudformation").Stack(self._cfn_stack_name)
        for output in cfn_stack.outputs:
            if output["OutputKey"] == self._cfn_url_output_name:
                return output["OutputValue"]

        # if not found, raise an error
        raise ValueError(f"unable to find URL from stack '{self._cfn_stack_name}'")

    def create(
        self,
        item: Union[FeaturePersistenceItem, AgencyFeatures, FeatureAgencies],
        force=False,
    ):
        """Create FeaturePersistenceAPI Feature(s)

        This is a lower level function which requires item to be in the form needed by
        the FeaturePersistenceAPI.

        Args:
            item (Union[FeaturePersistenceItem, AgencyFeatures, FeatureAgencies]):
                a single Feature in the form of FeaturePersistenceItem, or a collection
                of features using either AgencyFeatures or FeatureAgencies
            force (bool, optional):
                overwrite existing features. Defaults to False.

        Raises:
            ValueError: Invalid response from API
        """
        method = "put" if force else "post"
        response = requests.request(method, self.url, data=item.json(by_alias=True))
        if not response.status_code == 200:
            raise ValueError(f"unable to create {item=}. {response.content=}")

    def update(
        self,
        item: Union[FeaturePersistenceItem, AgencyFeatures, FeatureAgencies],
    ):
        """A wrapper around create with force=True, analogous to PUT"""
        return self.create(item, force=True)

    def create_feature(
        self,
        agency_id: UUID,
        feature_name: FeatureName,
        feature: Feature,
        force: bool = False,
    ):
        """Create single FeaturePersistenceAPI Feature

        Args:
            agency_id (UUID):
                AgencyID from Asset Library
            feature_name (FeatureName):
                FeatureNameEnum or string for either validated or generic feature
            feature (Union[GTFSRealtimeFeature, TSPAnalyticsFeature, dict]):
                Feature to create using API
            force (bool, optional):
                overwrite existing features. Defaults to False.

        Raises:
            ValueError: Invalid response from API
        """
        return self.create(
            parse_obj_as(
                FeaturePersistenceItem,
                dict(agency_id=agency_id, feature_name=feature_name, feature=feature),
            ),
            force=force,
        )

    def update_feature(
        self,
        agency_id: UUID,
        feature_name: FeatureName,
        feature: Feature,
    ):
        """A wrapper around create_feature with force=True, analogous to PUT"""
        return self.create_feature(agency_id, feature_name, feature, force=True)

    def patch_feature(
        self,
        agency_id: UUID,
        feature_name: FeatureName,
        feature: Optional[dict] = None,
        **kwargs,
    ):
        """Modify a subset of the fields for a specific feature

        Args:
            agency_id (UUID):
                AgencyID from Asset Library
            feature_name (FeatureName):
                FeatureNameEnum or string for either validated or generic feature
            feature (dict, optional):
                Fields to update in dictionary form
            **kwargs:
                Fields to update as keyword arguments

        Raises:
            ValueError:
                - Invalid features
                - Invalid response from API
        """
        if kwargs and feature:
            raise ValueError("use only feature or keywords to provide feature fields")
        feature = feature or kwargs

        # create a generic item that bypasses feature validation
        patch_item = GenericFeaturePersistenceItem(
            agency_id=agency_id,
            feature_name=feature_name,
            feature=feature,
        )
        response = requests.patch(self.url, data=patch_item.json(by_alias=True))
        if not response.status_code == 200:
            raise ValueError(f"unable to patch feature. {response.content=}")

    def get(
        self,
        agency_id: Optional[UUID] = None,
        feature_name: Optional[FeatureName] = None,
        quiet: Optional[bool] = False,
    ) -> Union[FeaturePersistenceItem, AgencyFeatures, FeatureAgencies]:
        """Get FeaturePersistenceAPI Feature(s)

        This is a lower level function which requires agency_id/feature_name as expected
        by the FeaturePersistenceAPI.

        Args:
            agency_id (UUID, optional):
                AgencyID from Asset Library
            feature_name (FeatureName, optional):
                FeatureNameEnum or string for either validated or generic feature
            quiet (bool, optional):
                If True, returns None on invalid response instead of throwing an error

        Raises:
            ValueError:
                - At least one of agency_id/feature_name is required
                - Invalid response from API

        Returns:
            Union[FeaturePersistenceItem, AgencyFeatures, FeatureAgencies]
        """
        if not any([agency_id, feature_name]):
            raise ValueError("at least one of agency_id/feature_name is required")

        response = requests.get(
            self.url,
            params={"AgencyGUID": agency_id, "FeatureName": feature_name},
        )
        if not quiet and not response.status_code == 200:
            raise ValueError(f"unable to get feature. {response.content=}")

        return (
            parse_raw_as(
                Union[FeaturePersistenceItem, AgencyFeatures, FeatureAgencies],
                response.content,
            )
            if response.content
            else None
        )

    def get_feature(
        self,
        agency_id: UUID,
        feature_name: FeatureName,
        quiet: Optional[bool] = False,
    ) -> Feature:
        """Create single FeaturePersistenceAPI Feature

        Args:
            agency_id (UUID):
                AgencyID from Asset Library
            feature_name (FeatureName):
                FeatureNameEnum or string for either validated or generic feature
            quiet (bool, optional):
                If True, returns None on invalid response instead of throwing an error

        Raises:
            ValueError: Invalid response from API

        Returns:
            Feature
        """
        item = self.get(agency_id, feature_name, quiet)
        return item.feature if item else None

    def get_agency_features(
        self,
        agency_id: UUID,
        quiet: Optional[bool] = False,
    ) -> FeatureNameFeatureDict:
        """A wrapper around get with feature_name=None"""
        item = self.get(agency_id=agency_id, quiet=quiet)
        return item.features if item else None

    def get_feature_agencies(
        self,
        feature_name: FeatureName,
        quiet: Optional[bool] = False,
    ) -> AgencyFeatureDict:
        """A wrapper around get with agency_id=None"""
        item = self.get(feature_name=feature_name, quiet=quiet)
        return item.features if item else None

    def delete(
        self,
        agency_id: Optional[UUID] = None,
        feature_name: Optional[FeatureName] = None,
        quiet: Optional[bool] = False,
    ):
        """Delete FeaturePersistenceAPI Feature(s)

        This is a lower level function which requires agency_id/feature_name as expected
        by the FeaturePersistenceAPI.

        Args:
            agency_id (UUID, optional):
                AgencyID from Asset Library
            feature_name (FeatureName, optional):
                FeatureNameEnum or string for either validated or generic feature
            quiet (bool, optional):
                Ignore invalid response from API. Defaults to False.

        Raises:
            ValueError:
                - At least one of agency_id/feature_name is required
                - Invalid response from API
        """
        if not any([agency_id, feature_name]):
            raise ValueError("at least one of agency_id/feature_name is required")

        response = requests.delete(
            self.url,
            params={"AgencyGUID": agency_id, "FeatureName": feature_name},
        )
        if not quiet and not response.status_code == 200:
            raise ValueError(f"unable to delete feature. {response.content=}")

    def delete_feature(
        self,
        agency_id: UUID,
        feature_name: FeatureName,
        quiet: Optional[bool] = False,
    ):
        """Delete FeaturePersistenceAPI Feature(s)

        Args:
            agency_id (UUID):
                AgencyID from Asset Library
            feature_name (FeatureName):
                FeatureNameEnum or string for either validated or generic feature
            quiet (bool, optional):
                Ignore invalid response from API. Defaults to False.

        Raises:
            ValueError: Invalid response from API
        """
        return self.delete(agency_id, feature_name, quiet)
