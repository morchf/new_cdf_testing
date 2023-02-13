"""
Status values for the Region:
    REGION_STATUS_EXISTS: Region exists in asset lib and self-signed CA is correct
    REGION_STATUS_DOES_NOT_EXIST: Region does not exist in asset lib
    REGION_STATUS_NO_CA_IN_ASSET_LIB: Region exists in asset lib, \
        but CA not in asset lib
    REGION_STATUS_NO_CA_IN_IOT_CORE: Region exists in asset lib, \
        but CA not registered in IoT core
"""
REGION_STATUS_EXISTS = "REGION_STATUS_EXISTS"
REGION_STATUS_DOES_NOT_EXIST = "REGION_STATUS_DOES_NOT_EXIST"
REGION_STATUS_NO_CA_IN_ASSET_LIB = "REGION_STATUS_NO_CA_IN_ASSET_LIB"
REGION_STATUS_NO_CA_IN_IOT_CORE = "REGION_STATUS_NO_CA_IN_IOT_CORE"

"""
Status values for the Agency:
    AGENCY_STATUS_EXISTS: Agency exists in asset lib and self-signed CA is correct
    AGENCY_STATUS_DOES_NOT_EXIST: Agency does not exist in asset lib
    AGENCY_STATUS_NO_CA_IN_ASSET_LIB: Agency exists in asset lib, \
        but CA not in asset lib
    AGENCY_STATUS_NO_CA_IN_IOT_CORE: Agency exists in asset lib, \
        but CA not registered in IoT core
    AGENCY_STATUS_NO_VPS_CERT: Agency exists in asset lib, \
        but VPS cert not created
    AGENCY_STATUS_NO_VPS_CERT_IN_ASSET_LIB: Agency exists in asset lib \
        and IoT but VPS cert not in asset lib
    AGENCY_STATUS_NO_VPS_CERT_IN_IOT_CORE: Agency exists in asset lib and \
        IoT but VPS cert not registered in IoT COre
"""
AGENCY_STATUS_EXISTS = "AGENCY_STATUS_EXISTS"
AGENCY_STATUS_DOES_NOT_EXIST = "AGENCY_STATUS_DOES_NOT_EXIST"
AGENCY_STATUS_NO_CA_IN_ASSET_LIB = "AGENCY_STATUS_NO_CA_IN_ASSET_LIB"
AGENCY_STATUS_NO_CA_IN_IOT_CORE = "AGENCY_STATUS_NO_CA_IN_IOT_CORE"
AGENCY_STATUS_NO_VPS_CERT = "AGENCY_STATUS_NO_VPS_CERT"
AGENCY_STATUS_NO_VPS_CERT_IN_ASSET_LIB = "AGENCY_STATUS_NO_VPS_CERT_IN_ASSET_LIB"
AGENCY_STATUS_NO_2100_CERT_IN_ASSET_LIB = "AGENCY_STATUS_NO_2100_CERT_IN_ASSET_LIB"
AGENCY_STATUS_NO_VPS_CERT_IN_IOT_CORE = "AGENCY_STATUS_NO_VPS_CERT_IN_IOT_CORE"

"""
Status values for the device, which is either a vehicle or traffic:
    DEVICE_STATUS_EXISTS: Vehicle device exists in asset lib,
    it is connected with parent vehicle and self-signed CA is correct
    DEVICE_STATUS_DOES_NOT_EXIST: Vehicle device does not exist in asset lib
    DEVICE_STATUS_NO_CERT_IN_ASSET_LIB: Vehicle device exists in asset lib, \
        but asset lib does not have the cert id
    DEVICE_STATUS_NO_DEVICE_IN_ASSET_LIB: Vehicle device exists in asset lib, \
        but it is not connected with parent vehicle in the asset lib
    DEVICE_STATUS_NO_CERT_IN_IOT_CORE: Vehicle device exists in asset lib, \
        but iot core does not have the cert id
"""
DEVICE_STATUS_EXISTS = "DEVICE_STATUS_EXISTS"
DEVICE_STATUS_DOES_NOT_EXIST = "DEVICE_STATUS_DOES_NOT_EXIST"
DEVICE_STATUS_NO_CERT_IN_ASSET_LIB = "DEVICE_STATUS_NO_CERT_IN_ASSET_LIB"
DEVICE_STATUS_NO_DEVICE_IN_ASSET_LIB = "DEVICE_STATUS_NO_DEVICE_IN_ASSET_LIB"
DEVICE_STATUS_NO_CERT_IN_IOT_CORE = "DEVICE_STATUS_NO_CERT_IN_IOT_CORE"

"""
Status values for the device, which is either a vehicle or traffic:
    LOCATION_STATUS_EXISTS: Location exists in asset lib,
    LOCATION_STATUS_DOES_NOT_EXIST: Location does not exist in asset lib
"""
LOCATION_STATUS_EXISTS = "LOCATION_STATUS_EXISTS"
LOCATION_STATUS_DOES_NOT_EXIST = "LOCATION_STATUS_DOES_NOT_EXIST"
LOCATION_STATUS_NO_CA_IN_ASSET_LIB = "LOCATION_STATUS_NO_CA_IN_ASSET_LIB"
LOCATION_STATUS_NO_CA_IN_IOT_CORE = "LOCATION_STATUS_NO_CA_IN_IOT_CORE"
