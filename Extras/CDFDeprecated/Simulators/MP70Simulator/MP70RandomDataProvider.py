import random
import datetime


class MP70RandomDataProvider:
    HEX_VALUES = "0123456789ABCDEF"
    GPIO_VALUES = [9, 11, 13, 17, 19, 21]

    def __init__(self, duration, gpio=True):
        self.DeviceIdMapping = {}
        self.duration = duration
        self.gpio = gpio

    def get_record(self, deviceid):
        # Create Mac if deviceid is not registered
        if not self.DeviceIdMapping.get(deviceid, False):
            self.DeviceIdMapping[deviceid] = {
                "GLON": random.uniform(-180, 180),
                "GLAT": random.uniform(-90, 90),
                "GSPD": random.uniform(0, 100),
                "GHED": random.uniform(0, 360),
                "idx": 0,
                "GPIO": self.GPIO_VALUES[random.randint(0, 5)],
            }

        # Increment Sequence Number
        self.DeviceIdMapping[deviceid]["GLON"] += random.uniform(-0.00025, 0.00025)
        self.DeviceIdMapping[deviceid]["GLAT"] += random.uniform(-0.00025, 0.00025)
        self.DeviceIdMapping[deviceid]["GSPD"] += random.uniform(-10, 10)
        self.DeviceIdMapping[deviceid]["GHED"] += random.uniform(-45, 45)
        self.DeviceIdMapping[deviceid]["idx"] += 1

        if self.DeviceIdMapping[deviceid]["idx"] <= self.duration:
            if not self.gpio or self.DeviceIdMapping[deviceid]["idx"] % 5 != 0:
                return {
                    int(datetime.datetime.now().timestamp()): {
                        "atp.glon": self.DeviceIdMapping[deviceid]["GLON"],
                        "atp.glat": self.DeviceIdMapping[deviceid]["GLAT"],
                        "atp.gspd": self.DeviceIdMapping[deviceid]["GSPD"],
                        "atp.ghed": self.DeviceIdMapping[deviceid]["GHED"],
                    }
                }
            else:
                return {
                    int(datetime.datetime.now().timestamp()): {
                        "atp.glon": self.DeviceIdMapping[deviceid]["GLON"],
                        "atp.glat": self.DeviceIdMapping[deviceid]["GLAT"],
                        "atp.gspd": self.DeviceIdMapping[deviceid]["GSPD"],
                        "atp.ghed": self.DeviceIdMapping[deviceid]["GHED"],
                        "atp.gpi": self.DeviceIdMapping[deviceid]["GPIO"],
                    }
                }
        else:
            return None
