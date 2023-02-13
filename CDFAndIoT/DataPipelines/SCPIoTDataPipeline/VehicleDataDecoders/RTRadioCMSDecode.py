import base64
import datetime
from pyspark.sql.types import (
    StructType,
    ArrayType,
    IntegerType,
    DoubleType,
    StringType,
    StructField,
    TimestampType,
)

timeColumn = "utcTime"


def decoders(topic, encoded, utcTime):
    def decode_rtradio(string_call):
        m = string_call

        def ushort(val1, val2):
            if val2 > val1:
                return int(
                    "".join(
                        [
                            m[val1:val2][i : i + 2]
                            for i in range(0, len(m[val1:val2]), 2)
                        ][::-1]
                    ),
                    16,
                )

        def hex_to_signed(source):
            if not isinstance(source, str):
                raise ValueError("string type required")
            if 0 == len(source):
                print("Exception Raised: ", source)
                raise ValueError("string is empty")
            sign_bit_mask = 1 << (len(source) * 4 - 1)
            other_bits_mask = sign_bit_mask - 1
            value = int(source, 16)
            return -(value & sign_bit_mask) | (value & other_bits_mask)

        def lt_ln(x):
            lt = hex_to_signed(
                "".join(
                    [m[x : x + 8][i : i + 2] for i in range(0, len(m[x : x + 8]), 2)][
                        ::-1
                    ]
                )
            )
            if lt < 0:
                lt = lt * (-1)
                lat = int(lt / 1000000) + ((lt / 10000) % 100 / 60)
                lat = lat * (-1)
            else:
                lat = int(lt / 1000000) + ((lt / 10000) % 100 / 60)
            ln = hex_to_signed(
                "".join(
                    [
                        m[x + 8 : x + 16][i : i + 2]
                        for i in range(0, len(m[x + 8 : x + 16]), 2)
                    ][::-1]
                )
            )
            if ln < 0:
                ln = ln * (-1)
                lng = int(ln / 1000000) + ((ln / 10000) % 100 / 60)
                lng = lng * (-1)
            else:
                lng = int(ln / 1000000) + ((ln / 10000) % 100 / 60)
            return {"type": "Point", "latitude": lat, "longitude": lng}

        return {
            "vehSN": ushort(0, 8),
            "utcTime": datetime.datetime.strptime(utcTime, "%Y/%m/%d %H:%M:%S"),
            "vehRSSI": ushort(8, 12),
            "location": lt_ln(16),
            "vehGPSVel_mpsd5": ushort(32, 34),  # (Meters / 5) / second
            "vehGPSHdg_deg2": ushort(34, 36),  # Heading per two degrees rounded up
            "vehGPSCStat": ushort(36, 40),
            "vehGPSSatellites": ushort(40, 48),
            "vehVehID": ushort(48, 52),
            "vehCityID": ushort(52, 54),
            "vehModeOpTurn": ushort(54, 56),
            "vehClass": ushort(56, 58),
            "conditionalPriority": ushort(58, 60),
            "vehDiagValue": ushort(64, 72),
        }

    records = []
    encoded = base64.b64decode(encoded)
    encoded = encoded.hex()
    i = 0
    while i < len(encoded):
        try:
            records.append(decode_rtradio(encoded[i : i + 72]))
        except Exception:
            pass
        i += 72
    return records


schemaFormat = ArrayType(
    StructType(
        [
            StructField("vehSN", IntegerType(), False),
            StructField("utcTime", TimestampType(), False),
            StructField("vehRSSI", IntegerType(), False),
            StructField(
                "location",
                StructType(
                    [
                        StructField("type", StringType(), False),
                        StructField("latitude", DoubleType(), False),
                        StructField("longitude", DoubleType(), False),
                    ]
                ),
                False,
            ),
            StructField("vehGPSVel_mpsd5", IntegerType(), False),
            StructField("vehGPSHdg_deg2", IntegerType(), False),
            StructField("vehGPSCStat", IntegerType(), False),
            StructField("vehGPSSatellites", IntegerType(), False),
            StructField("vehVehID", IntegerType(), False),
            StructField("vehCityID", IntegerType(), False),
            StructField("vehModeOpTurn", IntegerType(), False),
            StructField("vehClass", IntegerType(), False),
            StructField("conditionalPriority", IntegerType(), False),
            StructField("vehDiagValue", IntegerType(), False),
        ]
    )
)
