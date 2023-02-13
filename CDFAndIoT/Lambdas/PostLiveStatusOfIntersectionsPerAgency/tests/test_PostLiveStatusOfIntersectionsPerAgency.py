import json
import CDFAndIoT.Lambdas.PostLiveStatusOfIntersectionsPerAgency as PostLiveStatusOfIntersectionsPerAgency


def test_lambda_handler_failure():

    with open("agencyIDmissing.json", "r") as file:
        event = json.load(file)
    message = PostLiveStatusOfIntersectionsPerAgency.lambda_handler(event, None)

    assert message == Exception("No AgencyID in call to lambda function")


def test_lambda_handler_normal_success():

    with open("agencyIDpresent.json", "r") as file:
        event = json.load(file)
    message = PostLiveStatusOfIntersectionsPerAgency.lambda_handler(event, None)

    with open("normalResponse.json", "r") as file:
        normalResponse = json.load(file)

    assert message["statusCode"] == normalResponse["statusCode"]


def test_lambda_handler_warning_success():

    with open("agencyIDpresent.json", "r") as file:
        event = json.load(file)
    message = PostLiveStatusOfIntersectionsPerAgency.lambda_handler(event, None)

    with open("warningResponse.json", "r") as file:
        warningResponse = json.load(file)

    assert message["statusCode"] == warningResponse["statusCode"]


def test_lambda_handler_error_success():

    with open("agencyIDpresent.json", "r") as file:
        event = json.load(file)
    message = PostLiveStatusOfIntersectionsPerAgency.lambda_handler(event, None)

    with open("errorResponse.json", "r") as file:
        errorResponse = json.load(file)

    assert message["statusCode"] == errorResponse["statusCode"]
