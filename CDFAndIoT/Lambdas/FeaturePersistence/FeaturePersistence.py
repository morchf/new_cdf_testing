import json
import logging
import os
from argparse import ArgumentParser
from decimal import Decimal
from typing import Any, Literal, Optional, Union
from uuid import UUID

import boto3
from pydantic import (
    BaseModel,
    Field,
    ValidationError,
    parse_obj_as,
    root_validator,
    validator,
)

from gtt.data_model.feature_persistence import (
    AgencyFeatures,
    FeatureAgencies,
    FeatureNameEnum,
    FeaturePersistenceItem,
    GenericFeaturePersistenceItem,
)


class Request(BaseModel, allow_population_by_field_name=True):
    """The base request class to parse API Gateway proxy parameters

    This could be made general and imported by any API, but a better approach might be:
      - some sort of base class that defines an interface for API lambdas
        - source could be API Gateway or SNS, SQS etc.
        - would not need to resemble an http request to flatten params/body into a data
          variable that could be subclassed to specify its format
          (like GetDeleteQueryParameters)
      - use API Gateway mapping templates to flatten the request

    Returns:
        _type_: _description_
    """

    http_method: Literal["DELETE", "GET", "POST", "PUT", "PATCH"] = Field(
        alias="httpMethod"
    )
    # ToDo: parse query_parameters as dict or list of tuples
    query_parameters: Any = Field(alias="queryStringParameters")
    body: Any

    @root_validator(pre=True)
    def flatten_method_parameters(cls, values):
        """parse API Gateway parameters"""
        logging.debug(f"flatten_method_parameters: {values=}")
        # values.update(values.get("queryStringParameters", {}))
        # ToDo: figure out how multiValueQueryStringParameters works
        # values.update(values.get("multiValueQueryStringParameters", {}))
        return values

    @validator("body", pre=True)
    def parse_body_json(cls, v):
        """parse API Gateway body as json if possible, else leave it as is"""
        logging.debug(f"parse_body_json: {v=}")
        try:
            return json.loads(v)
        except (ValueError, TypeError):
            return v


def generate_response(statusCode, body, contentType="application/json") -> dict:
    """format the response for API Gateway to generate an HTTP response

    This could be replaced with a Response model similar to the Request model

    Returns:
        dict: statusCode, body, and headers
    """
    logging.info(f"Status Code: {statusCode} Body: {body} ")
    # convert body to json using pydantic json function if applicable
    json_body = (
        body.json(by_alias=True) if isinstance(body, BaseModel) else json.dumps(body)
    )
    return {
        "statusCode": statusCode,
        "body": json_body,
        "headers": {"Content-Type": contentType, "Access-Control-Allow-Origin": "*"},
    }


class GetDeleteQueryParameters(BaseModel, use_enum_values=True):
    """model for GET/DELETE query_parameters"""

    agency_id: Optional[UUID] = Field(alias="AgencyGUID")
    feature_name: Optional[Union[FeatureNameEnum, str]] = Field(alias="FeatureName")


class GetDeleteRequest(Request):
    """more specific Request model for GET/DELETE requests"""

    http_method: Literal["GET", "DELETE"] = Field(alias="httpMethod")
    query_parameters: GetDeleteQueryParameters = Field(alias="queryStringParameters")


class PostPutRequest(Request):
    """more specific Request model for POST/PUT requests"""

    http_method: Literal["POST", "PUT"] = Field(alias="httpMethod")
    body: Union[FeaturePersistenceItem, AgencyFeatures, FeatureAgencies]


class PatchRequest(Request):
    """more specific Request model for PATCH requests"""

    http_method: Literal["PATCH"] = Field(alias="httpMethod")
    body: GenericFeaturePersistenceItem


def delete_features(request: GetDeleteRequest, dynamo_table, secondary_index):
    """CRUD method to handle DELETE operations.

    If the request contains both agency_id and feature_name
        the specified item is deleted
    If the request contains only agency_id
        all features for specified agency are deleted
    If the request contains only feature_name
        all features for specified feature_name are deleted

    Args:
        request (GetDeleteRequest)
        dynamo_table (boto3.dynamodb.Table)

    Returns:
        dict: Response indicating success or failure
    """
    agency_id = request.query_parameters.agency_id
    feature_name = request.query_parameters.feature_name

    # delete single specified item
    if agency_id and feature_name:
        dynamo_table.delete_item(
            Key={
                "AgencyGUID": str(agency_id),
                "FeatureName": feature_name,
            }
        )
        return generate_response(200, f"Deleted {feature_name=} from {agency_id=}")

    # delete all agency items
    elif agency_id:
        # get list of feature_names
        feature_names = [
            item["FeatureName"]
            for item in dynamo_table.query(
                KeyConditionExpression="AgencyGUID = :guid",
                ExpressionAttributeValues={":guid": str(agency_id)},
                ProjectionExpression="FeatureName",
            )["Items"]
        ]
        if not feature_names:
            return generate_response(400, f"No features found for {agency_id=}")
        # delete each feature
        with dynamo_table.batch_writer() as batch_writer:
            for feature_name in feature_names:
                batch_writer.delete_item(
                    Key={
                        "AgencyGUID": str(agency_id),
                        "FeatureName": feature_name,
                    }
                )
        return generate_response(200, f"Deleted {feature_names=} from {agency_id=}")

    # delete all feature_name items
    elif feature_name:
        # get list of agency_ids
        agency_ids = [
            item["AgencyGUID"]
            for item in dynamo_table.query(
                IndexName=secondary_index,
                KeyConditionExpression="FeatureName = :feature_name",
                ExpressionAttributeValues={":feature_name": feature_name},
                ProjectionExpression="AgencyGUID",
            )["Items"]
        ]
        if not agency_ids:
            return generate_response(400, f"No features found for {feature_name=}")
        # delete each feature
        with dynamo_table.batch_writer() as batch_writer:
            for agency_id in agency_ids:
                batch_writer.delete_item(
                    Key={
                        "AgencyGUID": str(agency_id),
                        "FeatureName": feature_name,
                    }
                )
        return generate_response(200, f"Deleted {agency_ids=} from {feature_name=}")

    else:
        return generate_response(500, "AgencyGUID and/or FeatureName are required")


def get_features(request: GetDeleteRequest, dynamo_table, secondary_index):
    """CRUD method to handle GET operations.

    If the request contains both agency_id and feature_name
        a FeaturePersistenceItem is returned
    If the request contains only agency_id
        AgencyFeatures is returned with all features for specified agency
    If the request contains only feature_name
        FeatureAgencies is returned with all features for specified feature_name

    Args:
        request (GetDeleteRequest)
        dynamo_table (boto3.dynamodb.Table)

    Returns:
        dict: Response with requested data or failure status
    """
    agency_id = (
        str(request.query_parameters.agency_id)
        if request.query_parameters.agency_id
        else None
    )
    feature_name = request.query_parameters.feature_name

    # get single specified item
    if agency_id and feature_name:
        try:
            item = dynamo_table.get_item(
                Key={"AgencyGUID": str(agency_id), "FeatureName": feature_name}
            ).get("Item")
            return generate_response(200, parse_obj_as(FeaturePersistenceItem, item))
        except (ValueError, AttributeError) as e:
            logging.debug(f"{feature_name=} not found with {agency_id=}. {e=}")
            return generate_response(
                400, f"{feature_name=} not found with {agency_id=}"
            )

    # get all agency items
    elif agency_id:
        # get list of features
        features = [
            parse_obj_as(FeaturePersistenceItem, item)
            for item in dynamo_table.query(
                KeyConditionExpression="AgencyGUID = :guid",
                ExpressionAttributeValues={":guid": str(agency_id)},
            ).get("Items")
        ]
        if features:
            return generate_response(
                200,
                AgencyFeatures.parse_obj(
                    {
                        "agency_id": agency_id,
                        "features": {f.feature_name: f.feature for f in features},
                    }
                ),
            )
        else:
            return generate_response(400, f"No features found for {agency_id=}")

    # get all feature_name items
    elif feature_name:
        # get list of features
        features = [
            parse_obj_as(FeaturePersistenceItem, item)
            for item in dynamo_table.query(
                IndexName=secondary_index,
                KeyConditionExpression="FeatureName = :feature_name",
                ExpressionAttributeValues={":feature_name": feature_name},
            ).get("Items")
        ]
        if features:
            return generate_response(
                200,
                FeatureAgencies.parse_obj(
                    {
                        "feature_name": feature_name,
                        "features": {f.agency_id: f.feature for f in features},
                    }
                ),
            )
        else:
            return generate_response(400, f"No features found for {feature_name=}")

    # the default response that would be returned if someone put the URL in a browser
    else:
        # ToDo: have some sort of landing page to link to docs or something?
        return generate_response(500, f"{agency_id=} and {feature_name=} are empty")


def create_features(request: PostPutRequest, dynamo_table):
    """CRUD method to handle POST/PUT operations.

    POST returns an error if an item already exists. PUT overwrites.

    The request body should contain agency_id, feature_name, and feature. This can
    be one or more FeaturePersistenceItems or a single AgencyFeatures object.

    FeaturePersistenceItem:
        {
            AgencyGuid: <AgencyGUID>,
            FeatureName: <FeatureName>,
            Feature:  <Feature>
        }

    AgencyFeatures:
        {
            AgencyGUID: <AgencyGUID>
            Features: {
                <FeatureName>: <Feature>,
                ...
                <FeatureName>: <Feature>
            }
        }

    FeatureAgencies:
        {
            FeatureName: <FeatureName>
            Features: {
                <AgencyGUID>: <Feature>,
                ...
                <AgencyGUID>: <Feature>
            }
        }

    Args:
        request (PostPutRequest)
        dynamo_table (boto3.dynamodb.Table)

    Returns:
        dict: Response indicating success or failure
    """
    # coerce the features from the body into a list of FeaturePersistenceItems
    items = (
        # FeaturePersistenceItem
        [request.body]
        if isinstance(request.body, GenericFeaturePersistenceItem)
        # AgencyFeatures collection
        else [
            parse_obj_as(
                FeaturePersistenceItem,
                {
                    "agency_id": request.body.agency_id,
                    "feature_name": name,
                    "feature": (
                        feature.dict(by_alias=True)
                        if isinstance(feature, BaseModel)
                        else feature
                    ),
                },
            )
            for name, feature in request.body.features.items()
        ]
        if isinstance(request.body, AgencyFeatures)
        # FeatureAgencies collection
        else [
            parse_obj_as(
                FeaturePersistenceItem,
                {
                    "agency_id": agency_id,
                    "feature_name": request.body.feature_name,
                    "feature": (
                        feature.dict(by_alias=True)
                        if isinstance(feature, BaseModel)
                        else feature
                    ),
                },
            )
            for agency_id, feature in request.body.features.items()
        ]
    )

    # check if any items already exists for POST
    if request.http_method == "POST":
        logging.debug(f"checking {dynamo_table} for existing features {items}")
        existing_items = set(
            (item.agency_id, item.feature_name)
            for item in items
            if dynamo_table.get_item(
                Key={
                    "AgencyGUID": str(item.agency_id),
                    "FeatureName": item.feature_name,
                }
            ).get("Item")
        )
        logging.debug(f"{existing_items=}")
        if existing_items:
            return generate_response(
                409, f"{existing_items} features already exist, use PUT to update these"
            )

    # write each feature
    with dynamo_table.batch_writer() as batch_writer:
        for item in items:
            logging.debug(f"Creating feature: {item}")
            # convert to and from json to overcome boto3 limitations
            batch_writer.put_item(
                Item=json.loads(item.json(by_alias=True), parse_float=Decimal)
            )
    return generate_response(
        200,
        f"Features have been created/updated: {items}",
    )


def patch_feature(request: PatchRequest, dynamo_table):
    """CRUD method to handle PATCH operations.

    The requests should contain an existing agency_id/feature_name with the feature
    fields to modify

    Args:
        request (PatchRequest)
        dynamo_table (boto3.dynamodb.Table)

    Returns:
        dict: Response indicating success or failure
    """
    agency_id = str(request.body.agency_id)
    feature_name = request.body.feature_name
    feature_patch = request.body.feature

    # get item to patch
    existing_item = dynamo_table.get_item(
        Key={
            "AgencyGUID": str(agency_id),
            "FeatureName": feature_name,
        }
    ).get("Item")
    if not existing_item:
        return generate_response(400, f"{feature_name=} not found for {agency_id=}")

    patch_item = parse_obj_as(FeaturePersistenceItem, existing_item)

    # modify as requested
    for field, value in feature_patch.items():
        setattr(patch_item.feature, field, value)

    # recreate feature to validate it
    try:
        patch_item.feature = (
            type(patch_item.feature)(**patch_item.feature.dict(by_alias=True))
            if isinstance(patch_item.feature, BaseModel)
            else patch_item.feature
        )
    except ValidationError as validation_error:
        logging.debug(f"PATCH {validation_error=}")
        return generate_response(400, str(validation_error))

    # update the table with the new feature value
    # convert to and from json to overcome boto3 limitations
    dynamo_table.put_item(
        Item=json.loads(patch_item.json(by_alias=True), parse_float=Decimal)
    )

    return generate_response(
        200, f"Patched {feature_name=} from {agency_id=} to be {patch_item.feature}"
    )


def lambda_handler(event, context):
    logging.info(f"Received {event=}, {context=}")

    table_name = os.environ.get("TABLE_NAME", "FeaturePersistence")
    secondary_index = os.environ.get("SECONDARY_INDEX", "FeatureName-index")
    dynamo_table = boto3.resource("dynamodb").Table(table_name)

    # parse request based on request type
    try:
        request = parse_obj_as(
            Union[PostPutRequest, GetDeleteRequest, PatchRequest],
            event,
        )
    except ValidationError as validation_error:
        logging.debug(f"{validation_error=}")
        return generate_response(400, str(validation_error))
    except ValueError as value_error:
        logging.debug(f"{value_error=}")
        return generate_response(500, str(value_error))

    # Route request to specific functions for GET, POST, PUT and DELETE
    try:
        if request.http_method in ("POST", "PUT"):
            logging.debug(f"POST/PUT called with {request=}")
            return create_features(request, dynamo_table)

        elif request.http_method == "GET":
            logging.debug(f"GET called with {request=}")
            return get_features(request, dynamo_table, secondary_index)

        elif request.http_method == "DELETE":
            logging.debug(f"DELETE called with {request=}")
            return delete_features(request, dynamo_table, secondary_index)

        elif request.http_method == "PATCH":
            logging.debug(f"PATCH called with {request=}")
            return patch_feature(request, dynamo_table)

    except Exception as genericException:
        logging.info(f"Exception occurred:- {genericException}")
        return generate_response(500, str(genericException))


if __name__ == "__main__":
    parser = ArgumentParser(description="Test lambda with specified event/context")
    parser.add_argument("--table-name", type=str, help="dynamodb table name")
    parser.add_argument("--secondary-index", type=str, help="dynamodb secondary index")
    parser.add_argument("--event", type=str, help="event passed to lambda_handler")
    parser.add_argument("--context", type=str, help="context passed to lambda_handler")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    if args.table_name:
        os.environ["TABLE_NAME"] = args.table_name
    if args.secondary_index:
        os.environ["SECONDARY_INDEX"] = args.secondary_index

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format="%(message)s")
    logging.getLogger().setLevel(log_level)

    # override to just print the response
    def generate_response(statusCode, body, _=None):  # noqa: F811
        logging.info(f"Status Code: {statusCode} Body: {body}")

    lambda_handler(json.loads(args.event or "null"), json.loads(args.context or "null"))
