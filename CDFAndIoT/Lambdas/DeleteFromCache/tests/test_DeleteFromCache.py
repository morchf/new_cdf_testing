import sys
import os
import CDFAndIoT.Lambdas.DeleteFromCache.LambdaCode.DeleteFromCache as DeleteFromCache

sys.path.append("../LambdaCode")
sys.path.append(
    os.path.join(os.path.abspath(os.path.realpath(__file__) + 4 * "/.."), "CDFBackend")
)


def test_agency():
    with open("agency.json", "r") as file:
        data = file.read()
        event = {}
        event["Records"] = []
        temp_dict = {}
        temp_dict["body"] = data
        event["Records"].append(temp_dict)
        if event:
            status = DeleteFromCache.lambda_handler(event, "")
            assert status == 200


def test_communicator():
    with open("communicator.json", "r") as file:
        data = file.read()
        event = {}
        event["Records"] = []
        temp_dict = {}
        temp_dict["body"] = data
        event["Records"].append(temp_dict)

        if event:
            status = DeleteFromCache.lambda_handler(event, "")
            assert status == 200


def test_region():
    with open("region.json", "r") as file:
        data = file.read()
        event = {}
        event["Records"] = []
        temp_dict = {}
        temp_dict["body"] = data
        event["Records"].append(temp_dict)

        if event:
            status = DeleteFromCache.lambda_handler(event, "")
            assert status == 200


def test_vehicle():
    with open("vehicle.json", "r") as file:
        data = file.read()
        event = {}
        event["Records"] = []
        temp_dict = {}
        temp_dict["body"] = data
        event["Records"].append(temp_dict)

        if event:
            status = DeleteFromCache.lambda_handler(event, "")
            assert status == 200
