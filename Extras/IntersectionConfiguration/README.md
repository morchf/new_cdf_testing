# INTERSECTION CONFIGURATION CLI UTILITY

This tool allows you to configure Virtual Phase Selectors in the Smart City Platform.

## REQUIREMENTS
- Boto3 (With AWS CLI configured with the correct AWS account)

## ARGUMENTS
- customerName : The name of the customer as stored in CDF, VPS, etc
    - e.g. HOKAH
- intersections : None, an empty list, or a list of the intersections to configure
    - e.g. [] or None or ["V764HKMS0221", "V764HKMS0222"]
- deviceCert, deviceKey, and rootCA : The respective local file paths to
    the device certificate files
    - e.g. "Data/rootCA.crt"
- iotEndpoint : The name of the iot endpoint where the intersection should connect
    Can be found by navigating to the AWS IoT Core console and looking in Settings
    - e.g. "example-ats.iot.region-name.amazonaws.com"
- approachMaps : Boolean, Whether the tool should write Basic Approach Maps to the
    intersections
    - Must be either True or False