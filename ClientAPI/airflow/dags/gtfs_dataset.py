import contextlib
import json
import logging
import re
import tempfile
import urllib.request
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Tuple

import pyarrow as pa

# Required to make `pa.csv` and `pa.parquet` calls work
import pyarrow.csv
import pyarrow.parquet
from airflow import DAG
from airflow.models import Variable
from airflow.operators.python import PythonOperator, ShortCircuitOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from common.common import check_connection, format_dict_values, on_failure
from common.constants import GTFS_TABLES
from common.init_dags import get_dags_to_load
from scrapy import Spider
from scrapy.crawler import CrawlerRunner
from services.dwh import StaticGtfsDwhService
from twisted.internet import reactor

LOGGER = logging.getLogger(__name__)

# See https://github.com/google/transit/blob/master/gtfs/spec/en/reference.md
GTFS_TYPES = {
    "agency.txt": {
        "agency_id": pa.string(),
        "agency_name": pa.string(),
        "agency_url": pa.string(),
        "agency_timezone": pa.string(),
        "agency_lang": pa.string(),
        "agency_phone": pa.string(),
        "agency_fare_url": pa.string(),
        "agency_email": pa.string(),
    },
    "calendar.txt": {
        "service_id": pa.string(),
        "monday": pa.int64(),
        "tuesday": pa.int64(),
        "wednesday": pa.int64(),
        "thursday": pa.int64(),
        "friday": pa.int64(),
        "saturday": pa.int64(),
        "sunday": pa.int64(),
        "start_date": pa.string(),
        "end_date": pa.string(),
    },
    "calendar_dates.txt": {
        "service_id": pa.string(),
        "date": pa.string(),
        "exception_type": pa.int64(),
    },
    "fare_attributes.txt": {
        "fare_id": pa.string(),
        "price": pa.float64(),
        "currency_type": pa.string(),
        "payment_method": pa.int64(),
        "transfers": pa.int64(),
        "agency_id": pa.string(),
        "transfer_duration": pa.int64(),
    },
    "fare_rules.txt": {
        "fare_id": pa.string(),
        "route_id": pa.string(),
        "origin_id": pa.string(),
        "destination_id": pa.string(),
        "contains_id": pa.string(),
    },
    "routes.txt": {
        "route_id": pa.string(),
        "agency_id": pa.string(),
        "route_short_name": pa.string(),
        "route_long_name": pa.string(),
        "route_desc": pa.string(),
        "route_type": pa.int64(),
        "route_url": pa.string(),
        "route_color": pa.string(),
        "route_text_color": pa.string(),
        "route_sort_order": pa.int64(),
        "continuous_pickup": pa.int64(),
        "continuous_drop_off": pa.int64(),
    },
    "shapes.txt": {
        "shape_id": pa.string(),
        "shape_pt_lat": pa.float64(),
        "shape_pt_lon": pa.float64(),
        "shape_pt_sequence": pa.int64(),
        "shape_dist_traveled": pa.float64(),
    },
    "stops.txt": {
        "stop_id": pa.string(),
        "stop_code": pa.string(),
        "stop_name": pa.string(),
        "tts_stop_name": pa.string(),
        "stop_desc": pa.string(),
        "stop_lat": pa.float64(),
        "stop_lon": pa.float64(),
        "zone_id": pa.string(),
        "stop_url": pa.string(),
        "location_type": pa.int64(),
        "parent_station": pa.string(),
        "stop_timezone": pa.string(),
        "wheelchair_boarding": pa.int64(),
        "level_id": pa.string(),
        "platform_code": pa.string(),
    },
    "stop_times.txt": {
        "trip_id": pa.string(),
        "arrival_time": pa.string(),
        "departure_time": pa.string(),
        "stop_id": pa.string(),
        "stop_sequence": pa.int64(),
        "stop_headsign": pa.string(),
        "pickup_type": pa.int64(),
        "drop_off_type": pa.int64(),
        "continuous_pickup": pa.int64(),
        "continuous_drop_off": pa.int64(),
        "shape_dist_traveled": pa.float64(),
        "timepoint": pa.int64(),
    },
    "trips.txt": {
        "route_id": pa.string(),
        "service_id": pa.string(),
        "trip_id": pa.string(),
        "trip_headsign": pa.string(),
        "trip_short_name": pa.string(),
        "direction_id": pa.int64(),
        "block_id": pa.string(),
        "shape_id": pa.string(),
        "wheelchair_accessible": pa.int64(),
        "bikes_allowed": pa.int64(),
    },
}


class OpenmobilitydataOrg(Spider):
    agency = None
    allowed_domains = [
        "openmobilitydata.org",
        "openmobilitydata-data.s3-us-west-1.amazonaws.com",
    ]
    name = "openmobilitydata.org"
    start_date = None
    start_urls = []
    """
    GTFS feed (i.e. agency) main pages to start the crawl from.

    **Example**: ::

        CrawlerProcess().crawl(
            OpenmobilitydataOrg,
            start_urls=[
                "https://openmobilitydata.org/p/blue-gold-fleet/824",
                "https://openmobilitydata.org/p/sfmta/60",
            ],
        )
    """

    def parse(self, response, **kwargs):
        for a in response.css(".pagination a"):
            yield response.follow(a, self.parse)
        for a in response.css("table a:contains('Download')"):
            yield response.follow(a, self.parse_zip_url, method="HEAD")

    def parse_zip_url(self, response):
        zip_url = re.search(
            # E.g.
            # https://openmobilitydata-data.s3-us-west-1.amazonaws.com/public/feeds/sfmta/60/20210217-4/gtfs.zip
            r"(?P<url>https://openmobilitydata-data.+/(?P<agency>.+?)/\d+/(?P<date>\d+)(?P<date_postfix>.*)/gtfs.zip)",
            response.url,
        ).groupdict()
        zip_url["agency"] = self.agency
        zip_url["date"] = self.convert_to_iso_date(zip_url["date"])
        if not self.start_date or zip_url["date"] >= self.start_date:
            return zip_url

    @staticmethod
    def convert_to_iso_date(string):
        with contextlib.suppress(ValueError):
            # E.g. "20210217":
            return f"{datetime.strptime(string, '%Y%m%d'):%F}"
        with contextlib.suppress(ValueError):
            # E.g. "1382444184" (POSIX timestamp):
            return f"{datetime.fromtimestamp(float(string)):%F}"
        raise ValueError(f"failed to parse date {string!r}")


class GTFSFactory:
    def __init__(self):
        self.s3 = S3Hook().get_client_type("s3")

    @staticmethod
    def get_name() -> str:
        return "gtfs-dataset"

    def fetch_zip_urls(
        self, agency_id=None, agency=None, start_date=None, start_urls=None
    ):
        agency_id = agency_id if agency_id else agency

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "zip_urls.json"
            process = CrawlerRunner(
                settings={
                    "FEEDS": {
                        output: {
                            "encoding": "utf8",
                            "format": "json",
                            "overwrite": True,
                        }
                    }
                },
            )

            process.crawl(
                OpenmobilitydataOrg,
                agency=agency,
                start_date=start_date,
                start_urls=start_urls,
            )

            processes = process.join()
            processes.addBoth(lambda _: reactor.stop())
            reactor.run()

            with output.open() as f:
                return json.dumps(
                    list(
                        {
                            (x["agency"], x["date"]): {**x, "agency": agency_id}
                            for x in sorted(
                                json.load(f),
                                key=lambda x: (
                                    x["agency"],
                                    x["date"],
                                    x["date_postfix"],
                                ),
                            )
                        }.values()
                    )
                )

    def check_if_new_zip_urls(self, new_zip_urls):
        """
        > It evaluates a condition and short-circuits the workflow if the condition is False.
        > If the condition is True, downstream tasks proceed as normal.
        """
        return not new_zip_urls == "[]"

    def detect_new_zip_urls(self, zip_urls, output_bucket_name):
        zip_urls = json.loads(zip_urls)
        if not zip_urls:
            return []

        existing = {
            (m["agency"], m["date"])
            for agency in {zip_url["agency"] for zip_url in zip_urls}
            for key in (
                self.s3.get_paginator("list_objects_v2")
                .paginate(
                    Bucket=output_bucket_name, Prefix=f"gtfs/routes/agency={agency}/"
                )
                .search("Contents[].Key || `[]`")
            )
            for m in re.finditer(r"/agency=(?P<agency>.+?)/date=(?P<date>.+?)/", key)
        }

        return json.dumps(
            [
                zip_url
                for zip_url in zip_urls
                if (zip_url["agency"], zip_url["date"]) not in existing
            ]
        )

    def new_zip_url_dates(self, zip_urls):
        zip_urls = json.loads(zip_urls)
        if not zip_urls:
            return json.dumps([])

        return json.dumps([zip_url["date"] for zip_url in zip_urls])

    def ingest_new_zip_urls(self, new_zip_urls, output_bucket_name):
        new_zip_urls = json.loads(new_zip_urls)
        null_values = {" "} | {
            # https://github.com/apache/arrow/blob/630d85c4fa9af234fe148e881bf5f9b003563767/cpp/src/arrow/csv/options.cc#L41-L43
            "",
            "#N/A",
            "#N/A N/A",
            "#NA",
            "-1.#IND",
            "-1.#QNAN",
            "-NaN",
            "-nan",
            "1.#IND",
            "1.#QNAN",
            "N/A",
            "NA",
            "NULL",
            "NaN",
            "n/a",
            "nan",
            "null",
        }

        with tempfile.TemporaryDirectory() as tmp:
            for i, zip_url in enumerate(new_zip_urls, 1):
                print(f"{i:03}/{len(new_zip_urls):03}. Downloading {zip_url['url']!r}")
                urllib.request.urlretrieve(zip_url["url"], f"{tmp}/gtfs.zip")
                with zipfile.ZipFile(f"{tmp}/gtfs.zip") as gtfs_zip:
                    for name in gtfs_zip.namelist():
                        if name not in GTFS_TYPES:
                            continue
                        with gtfs_zip.open(name) as f:
                            try:
                                pa.parquet.write_table(
                                    pa.csv.read_csv(
                                        f,
                                        convert_options=pa.csv.ConvertOptions(
                                            column_types=GTFS_TYPES[name],
                                            include_columns=list(
                                                GTFS_TYPES[name].keys()
                                            ),
                                            include_missing_columns=True,
                                            null_values=null_values,
                                            strings_can_be_null=True,
                                        ),
                                    ),
                                    f"{tmp}/data.snappy.parquet",
                                    compression="snappy",
                                )

                                self.s3.upload_file(
                                    f"{tmp}/data.snappy.parquet",
                                    output_bucket_name,
                                    str(
                                        Path("gtfs")
                                        / Path(name).stem
                                        / f"agency={zip_url['agency']}"
                                        / f"date={zip_url['date']}"
                                        / Path(name).with_suffix(".snappy.parquet")
                                    ),
                                )
                            except Exception as e:
                                print("There is an exception with the file ", name)
                                print("Exception:", e)

    def __call__(self, agency: str, *args, **kwargs) -> Tuple[str, DAG]:
        config = Variable.get(f"{agency}_config", deserialize_json=True)
        gtfs_config = config[self.get_name()]
        schedule_interval = gtfs_config.get("schedule_interval", "@daily")
        env = config["env"]
        dag_id = f"{self.get_name()}-{agency}"

        output_bucket_name = S3Hook.parse_s3_url(f"s3a://client-api-etl-{env}")[0]

        with DAG(
            catchup=False,
            dag_id=dag_id,
            default_args={"depends_on_past": False, "on_failure_callback": on_failure},
            description=f"Ingest https://openmobilitydata.org/ GTFS feeds for {agency!r} into `s3://{output_bucket_name}/gtfs/`",
            tags=[self.get_name(), agency],
            max_active_runs=1,
            schedule_interval=schedule_interval,
            start_date=datetime.strptime(gtfs_config["start_date"], "%Y-%m-%d")
            if "start_date" in gtfs_config
            else datetime(2018, 5, 2),
            user_defined_macros={
                "json": json,
            },
        ) as dag:
            fetch_zip_urls = PythonOperator(
                op_kwargs={
                    "agency": gtfs_config["OpenmobilitydataOrg"].get("agency", agency),
                    "agency_id": agency,
                    "start_date": gtfs_config["OpenmobilitydataOrg"]["start_date"],
                    "start_urls": gtfs_config["OpenmobilitydataOrg"]["start_urls"],
                },
                python_callable=self.fetch_zip_urls,
                task_id="fetch-zip-urls",
                execution_timeout=timedelta(minutes=30),
            )

            detect_new_zip_urls = PythonOperator(
                op_kwargs={
                    "zip_urls": "{{ ti.xcom_pull(task_ids='fetch-zip-urls') }}",
                    "output_bucket_name": output_bucket_name,
                },
                python_callable=self.detect_new_zip_urls,
                task_id="detect-new-zip-urls",
                execution_timeout=timedelta(minutes=30),
            )

            check_if_new_zip_urls = ShortCircuitOperator(
                op_kwargs={
                    "new_zip_urls": "{{ ti.xcom_pull(task_ids='detect-new-zip-urls') }}"
                },
                python_callable=self.check_if_new_zip_urls,
                task_id="check_if_new_zip_urls",
                execution_timeout=timedelta(minutes=30),
            )

            ingest_new_zip_urls = PythonOperator(
                op_kwargs={
                    "new_zip_urls": "{{ ti.xcom_pull(task_ids='detect-new-zip-urls') }}",
                    "output_bucket_name": output_bucket_name,
                },
                python_callable=self.ingest_new_zip_urls,
                task_id="ingest-new-zip-urls",
                execution_timeout=timedelta(hours=1),
            )

            (
                fetch_zip_urls
                >> detect_new_zip_urls
                >> check_if_new_zip_urls
                >> ingest_new_zip_urls
            )

            format_dates = PythonOperator(
                task_id="new_zip_url_dates",
                python_callable=self.new_zip_url_dates,
                op_kwargs={
                    "zip_urls": "{{ ti.xcom_pull(task_ids='detect-new-zip-urls') }}",
                },
            )

            redshift_conn_id = (
                f"redshift_{agency}"
                if check_connection(f"redshift_{agency}")
                else "redshift_default"
            )
            dwh_service = StaticGtfsDwhService(
                conn_id=redshift_conn_id,
                partitions={
                    "agency": [agency],
                    "date": "{{ ti.xcom_pull(task_ids='new_zip_url_dates') }}",
                },
            )

            (
                ingest_new_zip_urls
                >> format_dates
                >> dwh_service.prepare()
                >> dwh_service.sync_tables(
                    tables=map(lambda x: format_dict_values(x, env=env), GTFS_TABLES),
                )
            )

            return dag_id, dag


for dag_id, dag in get_dags_to_load(GTFSFactory()):
    globals()[dag_id] = dag
