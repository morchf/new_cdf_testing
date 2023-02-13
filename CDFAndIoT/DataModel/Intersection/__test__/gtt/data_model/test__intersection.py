import json
from typing import List

from pydantic import BaseModel, Field

from gtt.data_model.intersection import ApproachMapEntry, Intersection, Thresholds


class TestIntersection:
    def test__intersection__minimal(self):
        Intersection(
            **{
                "intersectionName": "abc",
                "serialNumber": 123451246,
                "latitude": 37.343312,
                "longitude": 122.453532,
            }
        )

    def test__intersection__basic(self):
        intersection = Intersection(
            **{
                "intersectionId": 12347,
                "intersectionName": "abc",
                "serialNumber": 123451246,
                "latitude": 37.343312,
                "longitude": 122.453532,
                "lastCommunicated": "2022-07-10 12:01:01",
                "make": "GTT",
                "model": "v764",
                "timezone": "CST",
                "operationMode": "High",
                "status": "Normal",
                "firmwareVersion": 1.2,
            }
        )

        # Auto-converts to string
        assert intersection.intersection_id == "12347"
        assert intersection.serial_number == "123451246"
        assert intersection.firmware_version == "1.2"

        assert intersection.intersection_name == "abc"
        assert intersection.latitude == 37.343312
        assert intersection.longitude == 122.453532
        assert str(intersection.last_communicated) == "2022-07-10 12:01:01"
        assert intersection.make == "GTT"
        assert intersection.model == "v764"
        assert intersection.timezone == "CST"
        assert intersection.operation_mode == "High"
        assert intersection.status == "Normal"

        # Test JSON

        intersection_dict = json.loads(intersection.json(by_alias=True))

        assert intersection_dict["intersectionId"] == "12347"
        assert intersection_dict["serialNumber"] == "123451246"
        assert intersection_dict["firmwareVersion"] == "1.2"

        assert intersection_dict["intersectionName"] == "abc"
        assert intersection_dict["latitude"] == 37.343312
        assert intersection_dict["longitude"] == 122.453532
        assert intersection_dict["lastCommunicated"] == "2022-07-10T12:01:01"
        assert intersection_dict["make"] == "GTT"
        assert intersection_dict["model"] == "v764"
        assert intersection_dict["timezone"] == "CST"
        assert intersection_dict["operationMode"] == "High"
        assert intersection_dict["status"] == "Normal"

    def test__approach_map__basic(self):
        class ApproachMapResponse(BaseModel, allow_population_by_field_name=True):
            approach_map: List[ApproachMapEntry] = Field(alias="approachMap")

            thresholds: Thresholds

        request = ApproachMapResponse(
            approach_map=[
                {
                    "approach_name": "1",
                    "number_of_coordinates": 2,
                    "coordinates": [
                        {"latitude": -1643.0, "longitude": -15.0},
                        {"latitude": -11.0, "longitude": 1.0},
                    ],
                },
            ],
            thresholds={
                "low_priority": [
                    {
                        "channel_name": "0",
                        "channel": "0",
                        "call_hold_time": 100,
                        "max_call_time": 123,
                        "classes": [
                            {
                                "class": "1",
                                "name": "Regular Transit",
                                "active": True,
                                "eta": 0,
                                "distance": 0,
                            },
                            {
                                "class": "2",
                                "name": "Express Transit",
                                "active": True,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "3",
                                "name": "Paratransit",
                                "active": True,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "4",
                                "name": "Light Rail",
                                "active": True,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "5",
                                "name": "Trolley",
                                "active": True,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "6",
                                "name": "Snow Plows",
                                "active": True,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "7",
                                "name": "Supervisor",
                                "active": True,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "8",
                                "name": "Pavement Marking",
                                "active": True,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "9",
                                "name": "Installer/Set-up",
                                "active": True,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "10",
                                "name": "Bus Rapid Transit",
                                "active": False,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "10",
                                "name": "Not used",
                                "active": False,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "11",
                                "name": "Not used",
                                "active": False,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "12",
                                "name": "Not used",
                                "active": False,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "13",
                                "name": "Not used",
                                "active": False,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "14",
                                "name": "Not used",
                                "active": False,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "15",
                                "name": "Not used",
                                "active": False,
                                "eta": 30,
                                "distance": 3048,
                            },
                        ],
                    },
                    {
                        "channel_name": "1",
                        "channel": "1",
                        "call_hold_time": 100,
                        "max_call_time": 20,
                        "classes": [
                            {
                                "class": "1",
                                "name": "Regular Transit",
                                "active": True,
                                "eta": 0,
                                "distance": 0,
                            },
                            {
                                "class": "2",
                                "name": "Express Transit",
                                "active": True,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "3",
                                "name": "Paratransit",
                                "active": True,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "4",
                                "name": "Light Rail",
                                "active": True,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "5",
                                "name": "Trolley",
                                "active": True,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "6",
                                "name": "Snow Plows",
                                "active": True,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "7",
                                "name": "Supervisor",
                                "active": True,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "8",
                                "name": "Pavement Marking",
                                "active": True,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "9",
                                "name": "Installer/Set-up",
                                "active": True,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "10",
                                "name": "Bus Rapid Transit",
                                "active": False,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "10",
                                "name": "Not used",
                                "active": False,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "11",
                                "name": "Not used",
                                "active": False,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "12",
                                "name": "Not used",
                                "active": False,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "13",
                                "name": "Not used",
                                "active": False,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "14",
                                "name": "Not used",
                                "active": False,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "15",
                                "name": "Not used",
                                "active": False,
                                "eta": 30,
                                "distance": 3048,
                            },
                        ],
                    },
                    {
                        "channel_name": "2",
                        "channel": "2",
                        "call_hold_time": 100,
                        "max_call_time": 20,
                        "classes": [
                            {
                                "class": "1",
                                "name": "Regular Transit",
                                "active": True,
                                "eta": 0,
                                "distance": 0,
                            },
                            {
                                "class": "2",
                                "name": "Express Transit",
                                "active": True,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "3",
                                "name": "Paratransit",
                                "active": True,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "4",
                                "name": "Light Rail",
                                "active": True,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "5",
                                "name": "Trolley",
                                "active": True,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "6",
                                "name": "Snow Plows",
                                "active": True,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "7",
                                "name": "Supervisor",
                                "active": True,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "8",
                                "name": "Pavement Marking",
                                "active": True,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "9",
                                "name": "Installer/Set-up",
                                "active": True,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "10",
                                "name": "Bus Rapid Transit",
                                "active": False,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "10",
                                "name": "Not used",
                                "active": False,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "11",
                                "name": "Not used",
                                "active": False,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "12",
                                "name": "Not used",
                                "active": False,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "13",
                                "name": "Not used",
                                "active": False,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "14",
                                "name": "Not used",
                                "active": False,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "15",
                                "name": "Not used",
                                "active": False,
                                "eta": 30,
                                "distance": 3048,
                            },
                        ],
                    },
                ],
                "high_priority": [
                    {
                        "channel_name": "0",
                        "channel": "0",
                        "call_hold_time": 100,
                        "max_call_time": 20,
                        "classes": [
                            {
                                "class": "1",
                                "name": "Regular Transit",
                                "active": True,
                                "eta": 0,
                                "distance": 0,
                            },
                            {
                                "class": "2",
                                "name": "Express Transit",
                                "active": True,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "3",
                                "name": "Paratransit",
                                "active": True,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "4",
                                "name": "Light Rail",
                                "active": True,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "5",
                                "name": "Trolley",
                                "active": True,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "6",
                                "name": "Snow Plows",
                                "active": True,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "7",
                                "name": "Supervisor",
                                "active": True,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "8",
                                "name": "Pavement Marking",
                                "active": True,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "9",
                                "name": "Installer/Set-up",
                                "active": True,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "10",
                                "name": "Bus Rapid Transit",
                                "active": False,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "10",
                                "name": "Not used",
                                "active": False,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "11",
                                "name": "Not used",
                                "active": False,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "12",
                                "name": "Not used",
                                "active": False,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "13",
                                "name": "Not used",
                                "active": False,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "14",
                                "name": "Not used",
                                "active": False,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "15",
                                "name": "Not used",
                                "active": False,
                                "eta": 30,
                                "distance": 3048,
                            },
                        ],
                    },
                    {
                        "channel_name": "1",
                        "channel": "1",
                        "call_hold_time": 100,
                        "max_call_time": 20,
                        "classes": [
                            {
                                "class": "1",
                                "name": "Regular Transit",
                                "active": True,
                                "eta": 0,
                                "distance": 0,
                            },
                            {
                                "class": "2",
                                "name": "Express Transit",
                                "active": True,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "3",
                                "name": "Paratransit",
                                "active": True,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "4",
                                "name": "Light Rail",
                                "active": True,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "5",
                                "name": "Trolley",
                                "active": True,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "6",
                                "name": "Snow Plows",
                                "active": True,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "7",
                                "name": "Supervisor",
                                "active": True,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "8",
                                "name": "Pavement Marking",
                                "active": True,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "9",
                                "name": "Installer/Set-up",
                                "active": True,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "10",
                                "name": "Bus Rapid Transit",
                                "active": False,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "10",
                                "name": "Not used",
                                "active": False,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "11",
                                "name": "Not used",
                                "active": False,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "12",
                                "name": "Not used",
                                "active": False,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "13",
                                "name": "Not used",
                                "active": False,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "14",
                                "name": "Not used",
                                "active": False,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "15",
                                "name": "Not used",
                                "active": False,
                                "eta": 30,
                                "distance": 3048,
                            },
                        ],
                    },
                    {
                        "channel_name": "2",
                        "channel": "2",
                        "call_hold_time": 100,
                        "max_call_time": 20,
                        "classes": [
                            {
                                "class": "1",
                                "name": "Regular Transit",
                                "active": True,
                                "eta": 0,
                                "distance": 0,
                            },
                            {
                                "class": "2",
                                "name": "Express Transit",
                                "active": True,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "3",
                                "name": "Paratransit",
                                "active": True,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "4",
                                "name": "Light Rail",
                                "active": True,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "5",
                                "name": "Trolley",
                                "active": True,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "6",
                                "name": "Snow Plows",
                                "active": True,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "7",
                                "name": "Supervisor",
                                "active": True,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "8",
                                "name": "Pavement Marking",
                                "active": True,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "9",
                                "name": "Installer/Set-up",
                                "active": True,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "10",
                                "name": "Bus Rapid Transit",
                                "active": False,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "10",
                                "name": "Not used",
                                "active": False,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "11",
                                "name": "Not used",
                                "active": False,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "12",
                                "name": "Not used",
                                "active": False,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "13",
                                "name": "Not used",
                                "active": False,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "14",
                                "name": "Not used",
                                "active": False,
                                "eta": 30,
                                "distance": 3048,
                            },
                            {
                                "class": "15",
                                "name": "Not used",
                                "active": False,
                                "eta": 30,
                                "distance": 3048,
                            },
                        ],
                    },
                ],
            },
        )

        assert request.approach_map[0].coordinates[0].latitude == -1643.0
        assert request.thresholds.low_priority[0].max_call_time == 123

        assert request.thresholds.low_priority[0].classes[0].level == "1"
