import logging
from tempfile import TemporaryDirectory

from helpers.static_gtfs_validator import StaticGtfsValidator
from utils.zip import differing_files


class StaticGtfsService:
    def __init__(self, data_service):

        self._data_service = data_service

    def update_static_gtfs(self, agency_id: str, static_gtfs_url: str) -> bool:
        """Update an agency's static GTFS if new one available

        Args:
            agency_id (str): Globally unique agency ID
            static_gtfs_url (str): Static GTFS URL

        Returns:
            bool - If the static GTFS needed updating
        """
        with TemporaryDirectory() as root_dir:
            self._data_service.root_dir = root_dir

            latest_static_gtfs_path = self._data_service.load_latest(static_gtfs_url)
            current_static_gtfs_path = self._data_service.load_current(agency_id)

            if current_static_gtfs_path is not None:
                # Check for any differing files
                is_different = (
                    len(
                        differing_files(
                            latest_static_gtfs_path, current_static_gtfs_path
                        )
                    )
                    > 0
                )

                # Return if no changes in static GTFS
                if not is_different:
                    return False

            logging.info("New Static GTFS data found. Validating the file")

            # Validate the Static GTFS using Google's Static GTFS validator and log out if any errors
            try:
                validation_output = StaticGtfsValidator.validate(
                    latest_static_gtfs_path, output_path=root_dir
                )
                assert validation_output
            except Exception as e:
                logging.error(f"Invalid static GTFS: {e}")
                # Do not stop execution even if the Static GTFS is invalid. Log it out and continue to write it to S3 and Aurora

            # Writes the latest data to aurora
            self._data_service.update(agency_id)

            # Write latest data to S3 as a zip file
            try:
                self._data_service.backup(agency_id)
            except Exception as e:
                logging.exception(f"Unable to backup: {e}")

            return True
