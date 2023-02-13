import glob
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from zipfile import BadZipFile, ZipFile

import pandas as pd
import pyarrow as pa

# Required to make `pa.csv` and `pa.parquet` calls work
import pyarrow.csv
import pyarrow.parquet
import requests
from botocore.exceptions import ClientError
from constants import GTFS_DATA_MODEL, NULL_STATIC_GTFS_VALUES, STATIC_GTFS_TABLES
from sqlalchemy import exc


class StaticGtfsDataService:
    # Path Constants
    ZIP_NAME = "static_gtfs.zip"
    S3_ROOT_PATH_FORMAT = "agency_guid={agency_id}"
    S3_BACKUP_PATH_FORMAT = S3_ROOT_PATH_FORMAT + "/utc_date={utc_date}"
    CURRENT_FILE_PATH = "current"
    NEW_FILE_PATH = "new"
    NEW_ZIP_NAME = "new_static_gtfs.zip"

    def __init__(self, sql_engine, s3_bucket, *, root_dir: str = "/tmp"):
        self._sql_engine = sql_engine
        self._s3_bucket = s3_bucket

        self._new_dir = None
        self._current_dir = None

        self.root_dir = root_dir

    @property
    def root_dir(self) -> str:
        return self._root_dir

    @root_dir.setter
    def root_dir(self, value: str):
        self._root_dir = value

        self._current_dir = Path(value) / StaticGtfsDataService.CURRENT_FILE_PATH
        self._new_dir = Path(value) / StaticGtfsDataService.NEW_FILE_PATH

        self._current_dir.mkdir(exist_ok=True, parents=True)
        self._new_dir.mkdir(exist_ok=True, parents=True)

    def load_latest(self, static_gtfs_url: str) -> str:
        """
        Gets the latest static GTFS zip file from the agency's Static GTFS endpoint and returns a zip file

        Args:
            static_gtfs_url - This is the endpoint which is to be used to get the agency's Static GTFS URL

        Returns:
            str - Path where latest files have been unzipped
        """

        # Makes the request to the Agency's Static GTFS Endpoint and gets the zip file
        # Stores it in local and extracts all the files into the agency's path
        # ToDo: Handle different response types from the URL
        response = requests.get(static_gtfs_url)

        if not response:
            raise Exception("Response object missing")

        # Write the downloaded zip file to local storage
        output_path = str(Path(self.root_dir) / StaticGtfsDataService.NEW_ZIP_NAME)

        zip_file = None
        with open(output_path, "wb") as response_zip_file:
            response_zip_file.write(response.content)
            logging.info("Latest GTFS is saved to local storage")
            zip_file = ZipFile(file=output_path)

        zip_file.extractall(path=str(self._new_dir))

        return str(self._new_dir)

    def load_current(self, agency_id: str) -> Optional[str]:
        """Downloads and unzips the current static GTFS zip file for the agency from S3

        Args:
            agency_id - str Agency ID

        Returns:
            str - Path where latest files have been unzipped
        """
        zip_file = None

        try:
            output_path = self._current_dir / StaticGtfsDataService.ZIP_NAME
            s3_partition = StaticGtfsDataService.S3_ROOT_PATH_FORMAT.format(
                agency_id=agency_id
            )
            s3_path = f"raw/{s3_partition}/{StaticGtfsDataService.ZIP_NAME}"

            with open(output_path, "wb") as current_static_gtfs_file:
                self._s3_bucket.download_fileobj(str(s3_path), current_static_gtfs_file)
                logging.info(f"File downloaded from S3 and written to: {output_path}")

                zip_file = ZipFile(output_path)

        except ClientError as e:
            error_code = e.response["Error"]["Code"]

            # No existing file
            if error_code == "404":
                logging.info("No existing static GTFS for agency")
                return None

            logging.error(f"{error_code=}, {e=}")
            raise e
        except BadZipFile as e:
            logging.error(f"Bad zip file: {e}")
            raise e

        zip_file.extractall(path=str(self._current_dir))

        return str(self._current_dir)

    def _delete_from_db(self, agency_id: str, table_name: str):
        query = """
            DELETE FROM {table_name}
            WHERE cms_id
            IN (
                SELECT cms_id
                FROM {table_name}
                WHERE cms_id='{cms_id}'
            );
            SELECT * FROM {table_name}
            WHERE cms_id='{cms_id}'
        """.format(
            cms_id=agency_id, table_name=table_name
        )
        logging.debug(f"{query=}")

        pd.read_sql_query(query, self._sql_engine)

    def _read_csv(
        self, agency_id: str, table_name: str, file_name: str
    ) -> Optional[pa.Table]:
        """Read static GTFS table from CVS file"""
        column_types = GTFS_DATA_MODEL[table_name]
        columns = list(column_types.keys())

        try:
            table = None
            with open(file_name, "rb") as f:
                table = pa.csv.read_csv(
                    f,
                    convert_options=pa.csv.ConvertOptions(
                        column_types=column_types,
                        include_columns=columns,
                        include_missing_columns=True,
                        null_values=NULL_STATIC_GTFS_VALUES,
                        strings_can_be_null=True,
                    ),
                )

            table = table.append_column(
                "cms_id", pa.array([agency_id] * len(table), pa.string())
            )
            table = table.append_column(
                "last_updated",
                pa.array(
                    [datetime.now().timestamp() * 1000] * len(table), pa.timestamp("ms")
                ),
            )

            return table

        except Exception as e:
            logging.error(f"Error while processing the file: {e}")
            raise e

    def _save_to_db(self, table: pa.Table, table_name: str):
        """Save static GTFS table to the database"""
        try:
            table.to_pandas().to_sql(
                table_name,
                self._sql_engine,
                if_exists="append",
                index=False,
            )
        except exc.NoReferencedColumnError as e:
            logging.error(f"UndefinedColumn error: {table_name}.txt: {e}")
        except exc.SQLAlchemyError as e:
            logging.error(f"Error while connecting the database: {e}")
            raise e
        except Exception as e:
            logging.error(
                f"Exception occureed while inserting the date. {table_name}.txt: {e}",
            )
            raise e
        finally:
            self._sql_engine.dispose()

    def _save_to_file(self, table: pa.Table, table_name: str):
        """Save static GTFS table to a local, compressed, parquet file"""
        # Save locally as Parquet file
        pa.parquet.write_table(
            table,
            f"{str(self._new_dir)}/{table_name}.snappy.parquet",
            compression="snappy",
        )

    def _update(
        self,
        agency_id: str,
        table_name: str,
        file_name: str,
    ):
        """Remove existing table data, upload new data, and save locally"""
        table = self._read_csv(agency_id, table_name, file_name)

        if table is None:
            raise ValueError(f"No data loaded from file: {file_name}")

        self._delete_from_db(agency_id, table_name)
        self._save_to_db(table, table_name)
        self._save_to_file(table, table_name)

    def update(self, agency_id: str):
        """Remove existing static GTFS data, upload new data, and save locally"""
        logging.info(f"Writing files for {agency_id} to aurora")
        all_files = glob.glob(f"{str(self._new_dir)}/*.txt")

        if len(all_files) == 0:
            raise Exception("No new static GTFS")

        for file_name in all_files:
            table_name = os.path.basename(file_name).split(".")[0]

            if table_name not in STATIC_GTFS_TABLES:
                continue

            logging.info(f"Updating '{table_name}'")
            try:
                self._update(agency_id, table_name, file_name)
            except Exception as e:
                logging.error(f"Failed to update table '{table_name}': {e}")

        logging.info("GTFS feed processed succesfully")

    def backup(self, agency_id: str):
        """
        Writes the validated GTFS Files to S3.


        Zip file: /raw/agency_guid={agency_guid}/static_gtfs.zip
        Parquet files: {static_gtfs_table_name}/agency_guid={agency_guid}/utc_date={YYYY-MM-DD}/{static-gtfs-file_name}.snappy.parquet

        Args:
            agency_id: Agency ID
        """
        new_static_gtfs_path = Path(self.root_dir) / StaticGtfsDataService.NEW_ZIP_NAME

        if not os.path.isfile(new_static_gtfs_path):
            raise Exception("No file to backup")

        logging.info("Backing up each table file")
        for f in self._new_dir.glob("*.parquet"):
            table_name = f.name[0 : f.name.index(".")]

            # Save to S3 bucket partitioned by agency ID and UTC date
            s3_partition = StaticGtfsDataService.S3_BACKUP_PATH_FORMAT.format(
                agency_id=agency_id,
                utc_date=datetime.now().strftime("%Y-%m-%d"),
            )
            s3_table_partition = f"{table_name}/{s3_partition}"

            # Delete existing
            self._s3_bucket.objects.filter(Prefix=s3_table_partition).delete()

            logging.info(f"Backing up to {s3_partition}")

            # Save update
            try:
                self._s3_bucket.upload_file(str(f), f"{s3_table_partition}/{f.name}")
            except Exception as e:
                logging.error(f"Failed to backup table '{table_name}': {e}")

        logging.info("Backing up zip file")
        s3_partition = StaticGtfsDataService.S3_ROOT_PATH_FORMAT.format(
            agency_id=agency_id
        )
        with open(new_static_gtfs_path, "rb") as f:
            self._s3_bucket.upload_fileobj(
                f,
                f"raw/{s3_partition}/{StaticGtfsDataService.ZIP_NAME}",
            )
