import json
import os
import sys
import unittest
from io import BytesIO


sys.path.append("../LambdaCode")
sys.path.append(
    os.path.join(os.path.abspath(os.path.realpath(__file__) + 4 * "/.."), "CDFBackend")
)

from util.csv import read_csv, read_excel
from util.messages import create_messages


class TestCreateCDFEntitiesBatchAPI(unittest.TestCase):
    def __init__(self, *args):
        super().__init__(*args)
        self.maxDiff = sys.maxsize

    def _open_csv(file_name):
        if not os.path.exists(file_name):
            print(f"{file_name} not found.")
            return

        with open(f"{file_name}", "r") as f:
            csv_raw = f.read()
            return csv_raw

    def _open_excel(file_name):
        if not os.path.exists(file_name):
            print(f"{file_name} not found.")
            return

        with open(f"{file_name}", "rb") as f:
            fr = f.read()
            return BytesIO(fr)

    def test__read_csv(self):
        raw_csv = TestCreateCDFEntitiesBatchAPI._open_csv("input.csv")
        csv = read_csv(raw_csv, header=True)

        self.assertEqual(len(csv), 2)
        self.assertEqual(
            csv,
            [
                {
                    "description": "Test County",
                    "displayName": "TEST",
                    "name": "TEST",
                    "region": "region",
                },
                {
                    "agency": "agency",
                    "agencyCode": 2,
                    "city": "Location",
                    "description": "Location District",
                    "displayName": "AGCY",
                    "name": "AGCY",
                    "priority": "High",
                    "region": "TEST",
                    "state": "MO",
                    "timezone": "Central",
                },
            ],
        )

    def test__read_excel(self):
        raw_excel = TestCreateCDFEntitiesBatchAPI._open_excel("input.xlsx")
        excel = read_excel(raw_excel)

        self.assertEqual(len(excel), 10)
        self.assertEqual(
            json.dumps(excel),
            json.dumps(
                [
                    {
                        "region": "region",
                        "name": "TESTRGN",
                        "description": "Test Region",
                    },
                    {
                        "agency": "agency",
                        "region": "TESTRGN",
                        "name": "AGCY",
                        "description": "Test Agency",
                        "city": "Location",
                        "state": "MO",
                        "timezone": "Central",
                        "agencyCode": 121,
                        "priority": "High",
                    },
                    {
                        "agency": "agency",
                        "region": "TESTRGN",
                        "name": "OTHER",
                        "description": "Other Agency",
                        "city": "Location",
                        "state": "MO",
                        "timezone": "Central",
                        "agencyCode": 122,
                        "priority": "High",
                    },
                    {
                        "vehiclev2": "vehiclev2",
                        "region": "TESTRGN",
                        "agency": "AGCY",
                        "name": "RES1",
                        "description": "WFPDRES1",
                        "type": "Pumper",
                        "class": 2,
                        "VID": 2,
                        "priority": "High",
                    },
                    {
                        "vehiclev2": "vehiclev2",
                        "region": "TESTRGN",
                        "agency": "OTHER",
                        "name": "RES2",
                        "description": "WFPDRES2",
                        "type": "Pumper",
                        "class": 2,
                        "VID": 6,
                        "priority": "High",
                    },
                    {
                        "communicator": "communicator",
                        "region": "TESTRGN",
                        "agency": "AGCY",
                        "description": "OFPD9100",
                        "serial": "2100NI3094",
                        "gttSerial": "2100NI3094",
                        "addressLAN": "192.168.1.200",
                        "addressWAN": "107.90.54.21",
                        "make": "GTT",
                        "model": 2100,
                    },
                    {
                        "communicator": "communicator",
                        "region": "TESTRGN",
                        "agency": "OTHER",
                        "description": "OFPD9134",
                        "serial": "2100NH3124",
                        "gttSerial": "2100NH3124",
                        "addressLAN": "192.168.1.200",
                        "addressWAN": "107.90.54.255",
                        "make": "GTT",
                        "model": 2100,
                    },
                    {
                        "communicator": "communicator",
                        "region": "TESTRGN",
                        "agency": "AGCY",
                        "description": "WFPD9815",
                        "serial": "2100NH3121",
                        "gttSerial": "2100NH3121",
                        "addressLAN": "192.168.1.200",
                        "addressWAN": "107.90.55.2",
                        "make": "GTT",
                        "model": 2100,
                    },
                    {
                        "communicator": "communicator",
                        "region": "TESTRGN",
                        "agency": "AGCY",
                        "description": "CCFR9501",
                        "serial": "2100NF3143",
                        "gttSerial": "2100NF3143",
                        "addressLAN": "192.168.1.200",
                        "addressWAN": "107.90.55.30",
                        "make": "GTT",
                        "model": 2100,
                    },
                    {
                        "communicator": "communicator",
                        "region": "TESTRGN",
                        "agency": "OTHER",
                        "description": "CCFR9526",
                        "serial": "2100NF9128",
                        "gttSerial": "2100NF9128",
                        "addressLAN": "192.168.1.200",
                        "addressWAN": "107.90.55.10",
                        "make": "GTT",
                        "model": 2100,
                    },
                ]
            ),
        )

    def test__create_messages(self):
        raw_csv = TestCreateCDFEntitiesBatchAPI._open_csv("input.csv")
        csv = read_csv(raw_csv, header=True)
        messages = create_messages(csv)

        self.assertEqual(len(csv), 2)
        self.assertEqual(len(messages), 2)

        self.assertEqual(
            json.loads(messages[0]),
            {
                "attributes": {"caCertId": "NULL_CA", "regionGUID": "NULL_GUID"},
                "category": "group",
                "templateId": "region",
                "description": "Test County",
                "name": "TEST",
                "parentPath": "/",
                "groupPath": "/test",
            },
        )
        self.assertEqual(
            json.loads(messages[1]),
            {
                "description": "Location District",
                "attributes": {
                    "CMSId": "",
                    "city": "Location",
                    "state": "MO",
                    "timezone": "Central",
                    "agencyCode": 2,
                    "agencyID": "NULL_GUID",
                    "caCertId": "NULL_CA",
                    "vpsCertId": "NULL_CERT",
                    "priority": "High",
                },
                "category": "group",
                "templateId": "agency",
                "name": "AGCY",
                "groupPath": "/test/agcy",
                "parentPath": "/test",
            },
        )


if __name__ == "__main__":
    unittest.main()
