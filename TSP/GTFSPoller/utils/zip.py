import filecmp
import logging
from typing import List
from zipfile import ZipFile


def extract_zip_file(zip_file: ZipFile, unzipped_file_path: str):
    """
    Extracts the zip file provided to the path provided.

    Args:
        zip_file - The zip file to be unzipped. - This is to be the path to zipfile
    """
    try:
        zip_file.extractall(path=unzipped_file_path)
        logging.info(f"{zip_file} unzipped succesfully to {unzipped_file_path}.")
    except Exception as e:
        logging.exception(f"{zip_file} could not be unzipped: {e}")
        raise e


def differing_files(path1: str, path2: str) -> List[str]:
    differing_files = filecmp.dircmp(path1, path2).diff_files
    logging.info(f"Number of different files: {len(differing_files)}")
    return differing_files
