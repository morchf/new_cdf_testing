import json
import logging
import os
from argparse import ArgumentParser, Namespace
from time import sleep

import boto3
import sqlalchemy
from constants import FEATURE_NAME
from gtt.service.feature_persistence import FeaturePersistenceAPI
from helpers.event_bridge_trigger import EventBridgeTrigger
from services.static_gtfs_data_service import StaticGtfsDataService
from services.static_gtfs_service import StaticGtfsService
from sqlalchemy.pool import NullPool

logging.getLogger().setLevel(logging.INFO)


class StaticGtfsPoller:
    _static_gtfs_service: StaticGtfsService
    _feature_persistence_api: FeaturePersistenceAPI

    def __init__(
        self,
        feature_persistence_api: FeaturePersistenceAPI,
        static_gtfs_service: StaticGtfsService,
    ):
        self._static_gtfs_service = static_gtfs_service
        self._feature_persistence_api = feature_persistence_api
        self._listeners = []

    def poll(self):
        while True:
            feature_agencies = self._feature_persistence_api.get_feature_agencies(
                feature_name=str(FEATURE_NAME)
            )

            if not feature_agencies:
                logging.error(
                    "Unable to fetch ASM enabled agencies from Feature Persistence."
                )
                continue

            logging.info(f"Agencies using ASM: {feature_agencies}")

            for agency_id, feature in feature_agencies.items():
                agency = feature.get("agency_name")
                static_gtfs_url = feature.get("static_gtfs_url")

                # check to see if the agency_id has an associated Static GTFS URL
                if static_gtfs_url is None:
                    logging.error("No Static GTFS URL found")
                    continue

                logging.info(f"Polling {agency_id=}, {agency= }")

                try:
                    is_new = self._static_gtfs_service.update_static_gtfs(
                        agency_id, static_gtfs_url
                    )

                    if not is_new:
                        continue

                    # Notify subscribers
                    try:
                        for listener in self._listeners:
                            listener(agency_id)
                    except Exception as e:
                        logging.error(f"Failed to notify subscriber: {e}")

                except Exception as e:
                    logging.exception(f"Failed to load agency static GTFS: {e}")

            sleep(5)

    def subscribe(self, callback):
        self._listeners.append(callback)


def main(**kwargs):
    parser = ArgumentParser(
        description="Poll static GTFS endpoint and update on change"
    )
    parser.add_argument("--bucket-name", type=str, help="URL to Asset Library API")
    parser.add_argument(
        "--aurora-secret-name", type=str, help="Aurora connection secret name"
    )

    args, _ = parser.parse_known_args(namespace=Namespace(**kwargs))

    feature_persistence_api = FeaturePersistenceAPI()
    secretsmanager = boto3.client("secretsmanager")

    response = secretsmanager.get_secret_value(
        SecretId=args.aurora_secret_name or os.getenv("AURORA_SECRET_NAME")
    )
    secret_dict = json.loads(response["SecretString"])

    host = secret_dict["host"]
    username = secret_dict["username"]
    password = secret_dict["password"]
    port = secret_dict["port"]

    gtfs_conn = f"postgresql+psycopg2://{username}:{password}@{host}:{port}/gtfs"
    aurora_engine = sqlalchemy.create_engine(gtfs_conn, poolclass=NullPool)

    s3_bucket = boto3.resource("s3").Bucket(
        args.bucket_name or os.getenv("STATIC_GTFS_BUCKET_NAME")
    )
    events_client = boto3.client("events")

    event_bridge_trigger = EventBridgeTrigger(events_client)
    static_gtfs_data_service = StaticGtfsDataService(
        sql_engine=aurora_engine, s3_bucket=s3_bucket
    )

    static_gtfs_service = StaticGtfsService(data_service=static_gtfs_data_service)

    static_gtfs_manager = StaticGtfsPoller(feature_persistence_api, static_gtfs_service)
    static_gtfs_manager.subscribe(event_bridge_trigger.invalidate_static_gtfs)

    static_gtfs_manager.poll()


if __name__ == "__main__":
    main()
