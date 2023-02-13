import os

# GENERAL CONFIGURATION
TEMP_FOLDER = os.path.join(os.path.expanduser("~"), "DeviceCertProviderTemp", "")
NUM_TRIES = 6
WAIT_SECONDS = 5
BACKOFF = 1.5

# AWS CONFIGURATION
AWS_REGION = ""
AWS_ACCESS_KEY = ""
AWS_SECRET_KEY = ""

# CDF CONFIGURATION
# CDF_ASSETLIB_ENDPOINT = os.environ["CDF_URL"]
CDF_ASSETLIB_ENDPOINT = "https://oo9fn5p38b.execute-api.us-east-1.amazonaws.com/Prod"
CDF_CSV_BUCKET = "create-cdf-entities-develop"
CDF_DELETE_BUCKET = "delete-cdf-entities-develop"
CDF_CERT_BUCKET = "cdf-cert-store-develop"
CDF_CERT_PAYLOAD_NAME = "filename.zip"
CDF_CERT_CERT_NAME = "cert.pem"
CDF_CERT_KEY_NAME = "key.key"
CDF_CERT_ROOTCA_NAME = "rootCA.pem"
CDF_BASE_CSV = f"DO NOT DELETE THIS ROW Entities to be created. Headers (rows in blue) must come before all entities of that type. If no entities of a type will be made remove that header. No blank rows{os.linesep}"
CDF_END_CSV = "Done,,,,,,,,,,,,"
CDF_ASSETLIB_HEADERS = {
    "Accept": "'Accept: application/vnd.aws-cdf-v2.0+json'",
    "Content-Type": "'Content-Type: application/vnd.aws-cdf-v2.0+json'",
}
CDF_CERT_HEADERS = {}

# SIMULATION CONFIGURATION
# region
REGION_NAME = "Texas"
REGION_DESCRIPTION = "MP70 Simulator Region"
REGION_DNS = "2.2.2.3"

# agency
AGENCY_NAME = "AUSTIN"
AGENCY_DESCRIPTION = "MP70 Simulator Agency"
AGENCY_CITY = "San Antonio"
AGENCY_STATE = "TX"
AGENCY_TIMEZONE = "Central"
AGENCY_CODE = 25
AGENCY_PRIORITY = "Low"
AGENCY_ID = "11D92280-971B-11EB-97BD-0E21FC0E2A15"

# vehicle
VEHICLE_DESCRIPTION = "MP70 Simulator Vehicle"
COMMUNICATOR_DESCRIPTION = "MP70 Simulator Communicator"
VEHICLE_MAC = "22:22:22:00:00:03"
VEHICLE_IP = "10.22.22.3"
VEHICLE_IMEI = "877355233748886"
VEHICLE_MAKE = "Sierra Wireless"
VEHICLE_MODEL = "MP-70"
VEHICLE_VID = "3"
