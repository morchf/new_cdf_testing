from Utils import ConvertToDD
import datetime
import random


class MP70FileDataProvider:
    def __init__(self, file, gpio=9, start="begining"):
        self.values = []

        idx = 0
        lines = open(file, "r").readlines()
        for line in lines:
            idx += 1
            if line.startswith("$GPRMC"):
                items = line.split(",")
                self.values.append(
                    {
                        "atp.glat": ConvertToDD(items[3], items[4]),
                        "atp.glon": ConvertToDD(items[5], items[6]),
                        "atp.gspd": float(items[7]) * 3.6,
                        "atp.ghed": float(items[8]),
                        "atp.gpi": gpio,
                    }
                )

        if start == "random":
            self.startidx = random.randint(0, len(self.values) // 2)
        elif start == "short":
            self.startidx = random.randint(
                len(self.values) * 3 // 4, len(self.values) - 1
            )
        else:
            try:
                self.startidx = int(start)
                if self.startidx >= len(self.values):
                    raise ValueError(
                        "Cannot set start to a value past the end of the file"
                    )
            except:
                self.startidx = 0

    def get_record(self, device_id):
        try:
            return {
                int(datetime.datetime.now().timestamp()): self.values.pop(self.startidx)
            }
        except:
            return None
