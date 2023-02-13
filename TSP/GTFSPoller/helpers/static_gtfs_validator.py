import logging
import os
from pathlib import Path


class StaticGtfsValidator:
    VALIDATOR_VERSION = "3.1.1"
    VALIDATOR_JAR = (
        Path(__file__).parent.absolute()
        / f"../include/gtfs-validator-{VALIDATOR_VERSION}-cli.jar"
    )

    @staticmethod
    def validate(gtfs_zip_file_path: str, *, output_path: str) -> None:
        """
        Validates the gtfs zip file and stores the result in the output_path

        Args:
            gtfs_zip_file_path - The path to the zip file that points to the Static GTFS file to be validated
            output_path - The path where you want the results of the validation to be stored
        """
        # Call validator with cmd: java -jar {gtfsValidtorName} -i {gtfs_zip_file_path} -o {output_path}
        # check to see if both the paths exist
        try:
            if not os.path.exists(gtfs_zip_file_path) or not os.path.exists(
                output_path
            ):
                raise Exception("Invalid path")

            validator_cmd_string = f"java -jar {StaticGtfsValidator.VALIDATOR_JAR} -i {gtfs_zip_file_path} -o {output_path} &> /dev/null"
            os.system(validator_cmd_string)

        except OSError as e:
            logging.error(f"OSError: {e}")
            raise e
        except Exception as e:
            logging.exception(f"Exception while validating zip file: {e}")
            raise e

        report_path = f"{output_path}/report.json"

        if not os.path.exists(output_path):
            return

        try:
            with open(report_path, "rb") as validation_output:
                return validation_output.read()
        except Exception as e:
            logging.error(e)
