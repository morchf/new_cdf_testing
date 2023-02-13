import datetime
from enum import Enum
from typing import Any, Dict, Literal, Mapping, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl, PositiveFloat, root_validator, validator
from typing_extensions import Annotated


class FeatureNameEnum(str, Enum):
    """This represents the features that have an associated model to use for validation

    It primarily serves as a way to encapsulate hardcoded strings
    """

    gtfs_realtime = "gtfs-realtime"
    tsp_analytics = "tsp-analytics"


class GenericFeaturePersistenceItem(BaseModel):
    """Base class for an Item from the FeaturePersistence table

    primary key uses Partition/Sort field agency_id/feature_name
    """

    agency_id: UUID = Field(alias="AgencyGUID")
    feature_name: str = Field(alias="FeatureName")
    feature: Any = Field(alias="Feature")

    class Config:
        allow_population_by_field_name = True
        use_enum_values = True


class GTFSRealtimeFeature(BaseModel):
    """The necessary configuration options to connect to an agency's GTFS Realtime feeds

    Raises:
        ValidationError: At least one GTFS Realtime feed URL is required
    """

    vehicle_id_field: Literal["id", "label"] = "id"
    max_polling_rate: Optional[PositiveFloat] = 15
    subscribed_till: Optional[datetime.date]

    vehicle_positions_url: Optional[HttpUrl]
    trip_updates_url: Optional[HttpUrl]
    alerts_url: Optional[HttpUrl]

    vehicle_positions_headers: Optional[Dict[str, str]]
    trip_updates_headers: Optional[Dict[str, str]]
    alerts_headers: Optional[Dict[str, str]]

    @root_validator()
    def ensure_at_least_one_url(cls, values):
        if not any(
            values.get(key)
            for key in ("vehicle_positions_url", "trip_updates_url", "alerts_url")
        ):
            raise ValueError("At least one api endpoint is required")
        return values

    @validator("max_polling_rate")
    def set_max_polling_rate(cls, v, field):
        return v or field.default


class GTFSRealtimeItem(GenericFeaturePersistenceItem):
    """more specific FeaturePersistenceItem for GTFSRealtimeFeature"""

    feature_name: Literal[FeatureNameEnum.gtfs_realtime] = Field(alias="FeatureName")
    feature: GTFSRealtimeFeature = Field(alias="Feature")


class TimeRange(BaseModel):
    start_time: Optional[datetime.time]
    end_time: Optional[datetime.time]


class TSPAnalyticsFeature(BaseModel):
    early_schedule_deviation_limit: Optional[int] = -5
    late_schedule_deviation_limit: Optional[int] = 2
    peak_am_range: Optional[TimeRange]
    peak_pm_range: Optional[TimeRange]
    data_available_from: Optional[datetime.date]
    maximum_signal_delay: Optional[int] = 300
    geofencing_distance_meters: Optional[int] = 50

    @root_validator(pre=True)
    def ensure_tsp_analytics_feature(cls, values):
        """ensure at least one field set, not any generic dict"""
        if not any(values.get(key) for key in cls.__fields__.keys()):
            raise ValueError("At least one field is required")
        return values


class TSPAnalyticsItem(GenericFeaturePersistenceItem):
    """more specific FeaturePersistenceItem for TSPAnalyticsFeature"""

    feature_name: Literal[FeatureNameEnum.tsp_analytics] = Field(alias="FeatureName")
    feature: TSPAnalyticsFeature = Field(alias="Feature")


# A helper type for validated FeaturePersistenceItems
ValidatedFeaturePersistenceItem = Annotated[
    Union[GTFSRealtimeItem, TSPAnalyticsItem],
    Field(discriminator="feature_name"),  # noqa: F821
]

# A helper type for the specific and generic FeaturePersistenceItems
# Note that this can instantiate an item with parse_obj_as(FeaturePersistenceItem, data)
FeaturePersistenceItem = Union[
    ValidatedFeaturePersistenceItem,
    GenericFeaturePersistenceItem,
]

# a helper type for validated or generic FeatureName
FeatureName = Union[FeatureNameEnum, str]

# a helper type for any of the validated feature classes
ValidatedFeature = Union[GTFSRealtimeFeature, TSPAnalyticsFeature]

# a helper type for any of the validated feature classes or generic dict
Feature = Union[ValidatedFeature, dict]

# a helper type for a Mapping[feature_name, feature]
FeatureNameFeatureDict = Mapping[
    Union[
        Literal[FeatureNameEnum.gtfs_realtime],
        Literal[FeatureNameEnum.tsp_analytics],
        str,
    ],
    Union[GTFSRealtimeFeature, TSPAnalyticsFeature, dict],
]

# a helper type for a Mapping[agency_id, feature]
AgencyFeatureDict = Mapping[Union[UUID, str], Feature]


class AgencyFeatures(BaseModel, allow_population_by_field_name=True):
    """A collection of features under the same agency

    features are a dictionary that maps to feature_name:feature
    """

    agency_id: UUID = Field(alias="AgencyGUID")
    features: FeatureNameFeatureDict = Field(alias="Features")


class FeatureAgencies(BaseModel, allow_population_by_field_name=True):
    """A collection of all agency features with the same feature_name

    features are a dictionary that maps to agency_id:feature
    """

    feature_name: str = Field(alias="FeatureName")
    features: AgencyFeatureDict = Field(alias="Features")

    @validator("features")
    def convert_uuid_to_string(cls, v):
        """convert uuid to string so it can be used as json mapping key"""
        return {str(key): value for key, value in v.items()}
