import os

os.environ["CDF_URL"] = "fake_url"
os.environ["AWS_REGION"] = "fake_aws_region"
os.environ["CERT_BKT"] = "fake_cert_bkt"
import ui_helper


def test_validate_IMEI():
    ui_helper.validate_IMEI("123456789012345")


def test_validate_IMEI_too_short():
    try:
        ui_helper.validate_IMEI("12345")
    except Exception as error:
        assert str(error) == "IMEI is not valid"


def test_validate_IMEI_too_long():
    try:
        ui_helper.validate_IMEI("12345678901234567890")
    except Exception as error:
        assert str(error) == "IMEI is not valid"


def test_validate_IMEI_not_numeric():
    try:
        ui_helper.validate_IMEI("12345abcde")
    except Exception as error:
        assert str(error) == "IMEI is not valid"


def test_validate_MAC_with_colons():
    ui_helper.validate_MAC("12:34:56:78:90:12")


def test_validate_MAC_with_dashes():
    ui_helper.validate_MAC("12-34-56-78-90-12")


def test_validate_MAC_with_no_separator():
    ui_helper.validate_MAC("123456789012")


def test_validate_MAC_alphanumeric_hex():
    ui_helper.validate_MAC("AB:CD:EF:68:90:12")


def test_validate_MAC_too_short():
    try:
        ui_helper.validate_MAC("12:34:5")
    except Exception as error:
        assert str(error) == "MAC address is not valid"


def test_validate_MAC_too_long():
    try:
        ui_helper.validate_MAC("12:34:56:78:90:11:00")
    except Exception as error:
        assert str(error) == "MAC address is not valid"


def test_validate_MAC_random_space():
    try:
        ui_helper.validate_MAC("12: 34:56:78:90:1A")
    except Exception as error:
        assert str(error) == "MAC address is not valid"


def test_validate_MAC_outside_hex_range():
    try:
        ui_helper.validate_MAC("12:34:56:78:90:1G")
    except Exception as error:
        assert str(error) == "MAC address is not valid"


def test_check_field_length():
    length_dict = {"description": 500, "name": 100, "deviceId": 100, "type": 100}
    data_dict = {
        "groups": {"ownedby": ["/zoe_reg/zoe_agy"]},
        "attributes": {
            "name": "veh123",
            "type": "Ladder Truck",
            "priority": "High",
            "class": 10,
            "VID": 234,
            "lat": 44.9512963,
            "long": -92.9453703,
            "heading": 3,
            "speed": 20,
            "fixStatus": 1,
            "numFixSat": 3,
            "lastGPSMsgTimestamp": "1576175734002",
            "auxiliaryIo": 0,
            "lastGPIOMsgTimestamp": "1576175734002",
            "uniqueId": "NULL_GUID",
        },
        "category": "device",
        "templateId": "vehiclev2",
        "description": "a vehicle",
        "state": "active",
        "deviceId": "zoe_veh",
    }
    templateId = "vehiclev2"
    try:
        ui_helper.check_field_length(length_dict, data_dict, templateId)
    except Exception as error:
        assert str(error) == ""


def test_check_field_length_description_too_long():
    length_dict = {"description": 500, "name": 100, "deviceId": 5, "type": 100}
    data_dict = {
        "groups": {"ownedby": ["/zoe_reg/zoe_agy"]},
        "attributes": {
            "name": "veh123",
            "type": "Ladder Truck",
            "priority": "High",
            "class": 10,
            "VID": 234,
            "lat": 44.9512963,
            "long": -92.9453703,
            "heading": 3,
            "speed": 20,
            "fixStatus": 1,
            "numFixSat": 3,
            "lastGPSMsgTimestamp": "1576175734002",
            "auxiliaryIo": 0,
            "lastGPIOMsgTimestamp": "1576175734002",
            "uniqueId": "NULL_GUID",
        },
        "category": "device",
        "templateId": "vehiclev2",
        "description": "a vehicle",
        "state": "active",
        "deviceId": "zoe_veh",
    }
    templateId = "vehiclev2"
    try:
        ui_helper.check_field_length(length_dict, data_dict, templateId)
    except Exception as error:
        assert (
            str(error)
            == "The field deviceId is 7 characters it must be less than 5 charactor(s)"
        )
