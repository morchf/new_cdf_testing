import requests
import json
import redis

# -----------CONSTANTS-----------
ASSET_LIBRARY_URL = "Enter URL for the CDF Asset Library API here"
REDIS_ENDPOINT_URL = ""
REDIS_PORT_NUMBER = 6379
# ---------------------------------

redis_client = redis.Redis(host=REDIS_ENDPOINT_URL, port=REDIS_PORT_NUMBER, db=0)

errorMessage = {
    "statusCode": 400,
    "body": "",
    "headers": {
        "Content-Type": "application/json",
    },
}
normalMessage = {
    "statusCode": 200,
    "body": "",
    "headers": {
        "Content-Type": "application/json",
    },
}

warningMessage = {
    "statusCode": 404,
    "body": "",
    "headers": {
        "Content-Type": "application/json",
    },
}


def lambda_handler(event, context):
    try:
        # get agency ID from the GET request to this lambda and make a call to get the gttSerialNumber of the particular agency
        if event:
            if event["agencyID"]:

                # API call to convert agencyID to gttSerial
                response = requests.get(ASSET_LIBRARY_URL)

                if response.status_code == 200:

                    # find the value of the gttSerial number returned in the response and save it
                    gttSerial = json.loads(response.text)

                    # with the gttSerial, make a call to Redis on Elasticache, which returns a JSON with the status of that intersection
                    statusData = redis_client.get(Key=gttSerial)

                    #  the returned JSON contains more data as well if needed. Data format of JSON is the same as phase selector test json files in CDFAndIoT>CDFBackend>TestFiles>{ps_*.json}. Just an additional key-value pair with status is appended to the original PS JSON
                    if statusData[gttSerial] == "normal":
                        normalMessage["body"] = statusData
                        return normalMessage
                    elif statusData[gttSerial] == "warning":
                        warningMessage["body"] = statusData
                        return warningMessage
                    elif statusData[gttSerial] == "error":
                        errorMessage["body"] = statusData
                        return errorMessage
                    else:
                        raise Exception(
                            f"Response from Redis could not be parsed. Response from call: {statusData}"
                        )
                elif response.status_code == 404:
                    raise Exception(
                        f"Lambda PostLiveStatusOfIntersectionsPerAgency failed as the corresponding gttSerial number could not be found for the AgencyID. Response:{response.text}"
                    )
                else:
                    raise Exception(
                        f"Call to Asset Library did not return a valid response. Response from call: {response.text}"
                    )

            else:
                raise Exception("No AgencyID in call to lambda function")

    except Exception as e:
        print(f"Error: {e}")
