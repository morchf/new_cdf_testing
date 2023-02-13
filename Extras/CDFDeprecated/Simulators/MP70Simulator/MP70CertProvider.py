import boto3
import os
import shutil
import time
import uuid
import MP70CertProviderConfig
import requests
import zipfile
import ipaddress
from functools import wraps
import random
from requests_aws_sign import AWSV4Sign


def log(msg, logger=None):
    if logger:
        logger.warning(msg)
    else:
        print(msg)


def retry(exceptions, total_tries=4, initial_wait=0.5, backoff_factor=2, logger=None):
    """Calling the decorated function applying an exponential backoff.

    Args:
        exceptions (Exception): Exception(s) that trigger a retry, can be a tuple
        total_tries (int, optional): Total tries. Defaults to 4.
        initial_wait (float, optional): Time to first retry. Defaults to 0.5.
        backoff_factor (int, optional): Backoff multiplier (e.g. value of 2 will double the delay each retry). Defaults to 2.
        logger ([type], optional): Logger to be used, if none specified print. Defaults to None.
    """

    def retry_decorator(f):
        @wraps(f)
        def func_with_retries(*args, **kwargs):
            _tries, _delay = total_tries + 1, initial_wait
            while _tries > 1:
                try:
                    log(f"{total_tries + 2 - _tries}. try:", logger)
                    return f(*args, **kwargs)
                except exceptions as e:
                    _tries -= 1
                    print_args = args if args else "no args"
                    if _tries == 1:
                        msg = str(
                            f"Function: {f.__name__}\n"
                            f"Failed despite best efforts after {total_tries} tries.\n"
                            f"args: {print_args}, kwargs: {kwargs}"
                        )
                        log(msg, logger)
                        raise
                    msg = str(
                        f"Function: {f.__name__}\n"
                        f"Exception: {e}\n"
                        f"Retrying in {_delay} seconds!, args: {print_args}, kwargs: {kwargs}\n"
                    )
                    log(msg, logger)
                    time.sleep(_delay)
                    _delay *= backoff_factor

        return func_with_retries

    return retry_decorator


def changeMac(mac, offset):
    mac = mac.replace(":", "")
    mac = "{:012X}".format(int(mac, 16) + offset)
    return ":".join(mac[i] + mac[i + 1] for i in range(0, len(mac), 2))


def changeIp(ip, offset):
    return str(ipaddress.ip_address(ip) + offset)


def sendRequest(method, url, creds, headers={}, data={}):
    auth = AWSV4Sign(creds, "us-east-1", "execute-api")
    return requests.get(url, headers=headers, auth=auth)


def luhn_residue(digits):
    return (
        sum(sum(divmod(int(d) * (1 + i % 2), 10)) for i, d in enumerate(digits[::-1]))
        % 10
    )


def getValidIMEI():
    part = "".join(str(random.randrange(0, 9)) for _ in range(15 - 1))
    res = luhn_residue("{}{}".format(part, 0))
    return "{}{}".format(part, -res % 10)


class MP70CertProvider:
    def __init__(self, logging=False):
        super()

        self.logging = logging

        self.csvs = []
        self.uploaded_csvs = []
        self.devices = []

        self.device_index = 100
        self.device_mac = "22:22:22:00:00:00"
        self.device_ip = "10.22.22.0"

        try:
            if (
                MP70CertProviderConfig.AWS_ACCESS_KEY == ""
                or MP70CertProviderConfig.AWS_SECRET_KEY == ""
            ):
                raise ValueError(
                    "Missing AWS Crendentials in Settings.  Assuming AWS CLI is configured correctly"
                )
            region = (
                MP70CertProviderConfig.AWS_REGION
                if MP70CertProviderConfig.AWS_REGION != ""
                else "us-east-1"
            )
            session = boto3.Session(
                aws_access_key_id=MP70CertProviderConfig.AWS_ACCESS_KEY,
                aws_secret_access_key=MP70CertProviderConfig.AWS_SECRET_KEY,
                region_name=region,
            )
            self.s3 = session.client("s3")
            self.creds = session.get_credentials()
            if self.logging:
                print("Using AWS Credentials from config file...")
        except:
            self.s3 = boto3.client("s3")
            self.creds = boto3.Session().get_credentials()
            if self.logging:
                print("Using AWS Credentials from AWS CLI...")

    def close(self):
        self.__remove_all_cdf__()
        try:
            shutil.rmtree(MP70CertProviderConfig.TEMP_FOLDER)
        except FileNotFoundError:
            pass

    def __add_region__(self):
        if self.__does_region_exist_cdf__(MP70CertProviderConfig.REGION_NAME):
            if self.logging:
                print(
                    f'Region "{MP70CertProviderConfig.REGION_NAME}" already exists in CDF, skipping create...'
                )
            return ""

        csvString = f"region,name,description{os.linesep}region,{MP70CertProviderConfig.REGION_NAME},{MP70CertProviderConfig.REGION_DESCRIPTION}{os.linesep}"
        if self.logging:
            print(
                f'Adding new region "{MP70CertProviderConfig.REGION_NAME}" to create in CDF...'
            )
        return csvString

    def __add_agency__(self):
        if self.__does_agency_exist_cdf__(
            MP70CertProviderConfig.REGION_NAME, MP70CertProviderConfig.AGENCY_NAME
        ):
            if self.logging:
                print(
                    f'Agency "{MP70CertProviderConfig.AGENCY_NAME}" already exists in CDF, skipping create...'
                )
            return ""

        csvString = f"agency,name,region,description,city,state,timezone,agencyCode,priority{os.linesep}agency,{MP70CertProviderConfig.AGENCY_NAME},{MP70CertProviderConfig.REGION_NAME},{MP70CertProviderConfig.AGENCY_DESCRIPTION},{MP70CertProviderConfig.AGENCY_CITY},{MP70CertProviderConfig.AGENCY_STATE},{MP70CertProviderConfig.AGENCY_TIMEZONE},{MP70CertProviderConfig.AGENCY_CODE},{MP70CertProviderConfig.AGENCY_PRIORITY}{os.linesep}"
        if self.logging:
            print(
                f'Adding new agency "{MP70CertProviderConfig.AGENCY_NAME}" to create in CDF...'
            )
        return csvString

    def __add_device_header__(self):
        return f"vehicleV2,deviceId,region,agency,name,description,type,priority,class,VID{os.linesep}"

    def __add_communicator_header__(self):
        return f"communicator,deviceId,region,agency,vehicle,description,gttSerial,IMEI,addressLAN,addressWAN,addressMAC,make,model{os.linesep}"

    def __add_device__(self, vehicleConfigs):
        deviceid = f"SimDevice{self.device_index:04d}"
        if self.__does_vehicle_exist_cdf__(deviceid):
            return False, False

        csvString = f"vehicleV2,{deviceid},{MP70CertProviderConfig.REGION_NAME},{MP70CertProviderConfig.AGENCY_NAME},{deviceid},{MP70CertProviderConfig.VEHICLE_DESCRIPTION},Ladder Truck,{vehicleConfigs[self.added_devices]['priority']},{vehicleConfigs[self.added_devices]['class']},{self.device_index:04d}{os.linesep}"
        if self.logging:
            print(f'Adding new vehicle "{deviceid}" to create in CDF...')

        return deviceid, csvString

    def __add_communicator__(self):
        self.device_mac = changeMac(self.device_mac, 1)
        self.device_ip = changeIp(self.device_ip, 1)

        vehicleid = f"SimDevice{self.device_index:04d}"
        deviceid = f"SimDevice{self.device_index:04d}Com"
        if self.__does_vehicle_exist_cdf__(deviceid):
            return False, False

        csvString = f"communicator,{deviceid},{MP70CertProviderConfig.REGION_NAME},{MP70CertProviderConfig.AGENCY_NAME},{vehicleid},{MP70CertProviderConfig.COMMUNICATOR_DESCRIPTION},{deviceid},{getValidIMEI()},{self.device_ip},{self.device_ip},{self.device_mac},{MP70CertProviderConfig.VEHICLE_MAKE},{MP70CertProviderConfig.VEHICLE_MODEL}{os.linesep}"

        if self.logging:
            print(f'Adding new communicator "{deviceid}" to create in CDF...')

        return deviceid, csvString

    def __add_vehicle_and_communicator__(self, vehicleConfigs):
        self.device_index += 1
        _, csvDevice = self.__add_device__(vehicleConfigs)
        idCom, csvCom = self.__add_communicator__()

        if csvDevice and csvCom:
            self.devices.append(
                {
                    "RegionName": MP70CertProviderConfig.REGION_NAME,
                    "AgencyName": MP70CertProviderConfig.AGENCY_NAME,
                    "DeviceName": idCom,
                }
            )

        return csvDevice, csvCom

    def __does_region_exist_cdf__(self, region_name):
        url = f"{MP70CertProviderConfig.CDF_ASSETLIB_ENDPOINT}/groups/%2f{region_name}"
        response = sendRequest(
            "GET", url, self.creds, headers=MP70CertProviderConfig.CDF_ASSETLIB_HEADERS
        )
        if response.status_code == 404:
            return False
        elif response.status_code > 199 and response.status_code < 400:
            return True
        else:
            raise ConnectionError(
                f"Unable to read data from CDF: Status Code [{response.status_code}]"
            )

    def __does_agency_exist_cdf__(self, region_name, agency_name):
        url = f"{MP70CertProviderConfig.CDF_ASSETLIB_ENDPOINT}/groups/%2f{region_name}%2f{agency_name}"
        response = sendRequest(
            "GET", url, self.creds, headers=MP70CertProviderConfig.CDF_ASSETLIB_HEADERS
        )
        if response.status_code == 404:
            return False
        elif response.status_code > 199 and response.status_code < 400:
            return True
        else:
            raise ConnectionError(
                f"Unable to read data from CDF: Status Code [{response.status_code}]"
            )

    def __does_vehicle_exist_cdf__(self, vehicle_name):
        url = f"{MP70CertProviderConfig.CDF_ASSETLIB_ENDPOINT}/devices/{vehicle_name}"
        response = sendRequest(
            "GET", url, self.creds, headers=MP70CertProviderConfig.CDF_ASSETLIB_HEADERS
        )
        if response.status_code == 404:
            return False
        elif response.status_code > 199 and response.status_code < 400:
            return True
        else:
            raise ConnectionError(
                f"Unable to read data from CDF: Status Code [{response.status_code}]"
            )

    def __remove_all_cdf__(self):
        if self.logging:
            print(
                "Deleting any regions, agencies or devices that were created in CDF..."
            )
        for i in self.csvs:
            self.__upload_csv__(MP70CertProviderConfig.CDF_DELETE_BUCKET, i)

        # Need to wait until the last CSV file uploaded has been deleted
        time.sleep(30)

        if self.logging:
            print("Removing uploaded csv files from S3...")
        for i in self.uploaded_csvs:
            self.__delete_csv__(i[0], i[1])

    def __save_file__(self, vehicleid, filename, contents):
        file_path = os.path.join(
            MP70CertProviderConfig.TEMP_FOLDER, f"{vehicleid}_{filename}"
        )
        with open(file_path, "w") as f:
            f.write(contents)

        return file_path

    @retry(ConnectionError)
    def __delete_csv__(self, bucket, key):
        self.s3.delete_object(Bucket=bucket, Key=key)

    @retry(ConnectionError)
    def __upload_csv__(self, bucket, csv_string):
        key = f"{str(uuid.uuid4())}-DeviceSimulatorCsvUpload.csv"
        self.s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=csv_string.encode("UTF-8"),
        )
        self.uploaded_csvs.append([bucket, key])

    def __extract_file__(self, zip, vehicleid, filename):
        file_path = os.path.join(
            MP70CertProviderConfig.TEMP_FOLDER, f"{vehicleid}_{filename}"
        )
        with zip.open(filename, "r") as f:
            with open(file_path, "wb") as out_file:
                out_file.write(f.read())

        return file_path

    def __download_certs__(self, vehicleId):
        os.makedirs(MP70CertProviderConfig.TEMP_FOLDER, exist_ok=True)
        vehicleName = vehicleId.split("_")[-1]
        if self.logging:
            print(f'Downloading certificates for vehicle "{vehicleName}"...')
        returnVal = {
            "status": True,
            "cafile_filename": None,
            "cert_filename": None,
            "key_filename": None,
            "device_id": vehicleId,
            "device_name": vehicleName,
        }

        # Setup directory and file paths
        try:
            payload_temp_folder = os.path.join(
                MP70CertProviderConfig.TEMP_FOLDER, f"{vehicleName}"
            )
            payload_temp_file = os.path.join(
                payload_temp_folder,
                f"{vehicleName}_{MP70CertProviderConfig.CDF_CERT_PAYLOAD_NAME}",
            )
            if not os.path.exists(payload_temp_folder):
                os.makedirs(payload_temp_folder)
        except Exception as e:
            returnVal["status"] = False
            returnVal["message"] = repr(e)
            return returnVal

        # Download the certificates
        wait = MP70CertProviderConfig.WAIT_SECONDS
        for _ in range(MP70CertProviderConfig.NUM_TRIES):
            try:
                result = self.s3.get_object(
                    Bucket=MP70CertProviderConfig.CDF_CERT_BUCKET,
                    Key=f"{vehicleName.upper()}/{MP70CertProviderConfig.CDF_CERT_PAYLOAD_NAME}",
                )
                returnVal["status"] = True
                break
            except Exception as e:
                time.sleep(wait)
                returnVal["status"] = False
                returnVal["message"] = repr(e)
                wait *= MP70CertProviderConfig.BACKOFF
        if not returnVal["status"]:
            if self.logging:
                print(
                    f"Unable to download certificates for vehicle \"{vehicleName}\".  Exception: {returnVal['message']}"
                )
            return returnVal

        # Extract and write the certificate files
        try:
            with open(payload_temp_file, "wb") as f:
                f.write(result["Body"].read())

            with zipfile.ZipFile(payload_temp_file, "r") as zip:
                returnVal["cert_filename"] = self.__extract_file__(
                    zip, vehicleName, MP70CertProviderConfig.CDF_CERT_CERT_NAME
                )
                returnVal["key_filename"] = self.__extract_file__(
                    zip, vehicleName, MP70CertProviderConfig.CDF_CERT_KEY_NAME
                )
                returnVal["cafile_filename"] = self.__extract_file__(
                    zip, vehicleName, MP70CertProviderConfig.CDF_CERT_ROOTCA_NAME
                )

            if (
                returnVal["cert_filename"] is None
                or returnVal["key_filename"] is None
                or returnVal["cafile_filename"] is None
            ):
                returnVal["status"] = False
        except Exception as e:
            if self.logging:
                print(
                    f'Corrupted certificate zip file format for vehicle "{vehicleName}".  Exception: {e}'
                )
            returnVal["status"] = False
            returnVal["message"] = repr(e)
            return returnVal

        return returnVal

    def __create_cdf_csv__(self, num, vehicleConfigs):
        cdf_csv = MP70CertProviderConfig.CDF_BASE_CSV
        cdf_csv += self.__add_region__()
        cdf_csv += self.__add_agency__()
        cdf_csv += self.__add_device_header__()

        cdf_csv_part2 = self.__add_communicator_header__()

        while self.added_devices != num:
            vehResult, comResult = self.__add_vehicle_and_communicator__(vehicleConfigs)
            if vehResult and comResult:
                cdf_csv += vehResult
                cdf_csv_part2 += comResult
                self.added_devices += 1

        cdf_csv += cdf_csv_part2
        cdf_csv += MP70CertProviderConfig.CDF_END_CSV

        return cdf_csv

    def get_certs(self, num, vehicleConfigs):
        self.added_devices = 0

        cdf_csv = self.__create_cdf_csv__(num, vehicleConfigs)

        self.csvs.append(cdf_csv)
        self.__upload_csv__(MP70CertProviderConfig.CDF_CSV_BUCKET, cdf_csv)

        certs = []
        for i in range(len(self.devices) - num, len(self.devices)):
            certs.append(
                self.__download_certs__(
                    f"{self.devices[i]['AgencyName']}_{self.devices[i]['DeviceName']}"
                )
            )

        return certs
