import requests
from urllib.parse import urlencode
from typing import Optional, Dict
import csv
from time import sleep
from datetime import timedelta
import tempfile
from pathlib import Path
import logging

from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook


class GMapsApi:
    API_ENDPOINT = "https://maps.googleapis.com/maps/api"
    GEOCODE_ROUTE = "geocode/json"

    def __init__(self, api_key):
        self.api_key = api_key

    def _send_request(self, route: str, params: Optional[Dict[str, str]]):
        params = {"key": self.api_key, **(params or {})}

        return requests.get(f"{self.API_ENDPOINT}/{route}", params=params)

    def _get_street_address_geocode(self, location: Dict[str, str]):
        """
        Args:
            street_address: { "city": "CITY", "state": "STATE", "street": "STREET" }
        """
        street_address = urlencode(location)

        response = self._send_request(
            route=self.GEOCODE_ROUTE, params={"address": street_address}
        ).json()

        logging.info(response)

        results = response["results"][0]
        status = response["status"]

        if not status == "OK":
            raise Exception(f"Invalid response for address: {street_address}")

        address = results["formatted_address"]
        geometry = results["geometry"]

        latitude, longitude = [geometry["location"][k] for k in ["lat", "lng"]]

        if latitude is None or longitude is None:
            raise Exception(f"Invalid coordinates for address: {street_address}")

        return {
            **location,
            "address": address,
            "latitude": latitude,
            "longitude": longitude,
        }

    def get_street_address_geocodes(self, locations):
        geocodes = []

        for location in locations:
            try:
                geocode = self._get_street_address_geocode(location)
                geocodes.append(geocode)
            except Exception as e:
                logging.error(f"{e}: {urlencode(location)}")

            sleep(1)

        return geocodes


class GMapsService:
    def __init__(self, api_key):
        self.gmaps_api = GMapsApi(api_key=api_key)

        # AWS resources
        self.s3 = S3Hook().get_client_type("s3")

    def _ingest_street_address_geocodes(self, s3_bucket: str, s3_partition: str):
        with tempfile.TemporaryDirectory() as tmp:
            intersections_file_path = Path(tmp) / "intersections.tsv"
            locations_file_path = Path(tmp) / "locations.tsv"

            # Load intersections from partitioned bucket
            with open(intersections_file_path, mode="w") as intersections_file:
                logging.info(
                    f"s3://{s3_bucket}/intersections/{s3_partition}/intersections.tsv"
                )

                self.s3.download_file(
                    s3_bucket,
                    f"intersections/{s3_partition}/intersections.tsv",
                    intersections_file.name,
                )

            # Read intersections
            with open(intersections_file_path, mode="r") as intersections_file:
                logging.info("Reading intersections")
                intersections_reader = csv.DictReader(
                    intersections_file, delimiter="\t"
                )
                intersections = [intersection for intersection in intersections_reader]
                logging.info(f"Read {len(intersections)} intersections")

            if not intersections or len(intersections) == 0:
                return

            # Convert intersections to locations
            logging.info("Retrieving geocodes)")
            geocodes = self.gmaps_api.get_street_address_geocodes(
                list(
                    map(
                        lambda x: {
                            "city": x["Municipality"],
                            "state": x["State"],
                            "street": x["Signal Location"],
                        },
                        intersections,
                    )
                )
            )
            logging.info(f"Retrieved {len(geocodes)} geocodes")

            if not geocodes or len(geocodes) == 0:
                return

            # Write results to csv
            with open(locations_file_path, mode="w") as locations_file:
                logging.info("Writing results to TSV")
                location_writer = csv.writer(locations_file, delimiter="\t")
                location_writer.writerow(geocodes[0].keys())
                for geocode in geocodes:
                    location_writer.writerow(geocode.values())

            # Upload locations to partitioned bucket
            with open(locations_file_path, mode="r") as locations_file:
                logging.info(f"s3://{s3_bucket}/locations/{s3_partition}")
                self.s3.upload_file(
                    locations_file.name,
                    s3_bucket,
                    f"locations/{s3_partition}/locations.tsv",
                )

    def ingest_street_address_geocodes(
        self, s3_bucket: str, s3_partition: str, **kwargs
    ):
        return PythonOperator(
            python_callable=self._ingest_street_address_geocodes,
            execution_timeout=timedelta(minutes=30),
            op_kwargs={"s3_bucket": s3_bucket, "s3_partition": s3_partition},
            **kwargs,
        )
