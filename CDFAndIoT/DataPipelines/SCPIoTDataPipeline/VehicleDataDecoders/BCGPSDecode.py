import base64
import datetime
from pyspark.sql.types import (
    StructType,
    ArrayType,
    DoubleType,
    StringType,
    StructField,
    TimestampType,
)

timeColumn = "utcTime"


def decoders(topic, encoded, utcTime):
    serialNumber = topic.split("/")[-1]

    def decode_bcgps(string_call):
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
            "serialNumber": serialNumber,
            "utcTime": datetime.datetime.fromtimestamp(
                ushort(0, 8), datetime.timezone.utc
            ),
            "location": lt_ln(8),
            "speed": ushort(28, 32) / 100 * 0.514444,
            "heading": ushort(24, 28) / 100,
            "valid": "log error" + str(ushort(32, 36))
            if ushort(32, 34) != 0 and ushort(32, 34) != 1
            else ushort(32, 34),
        }

    records = []
    encoded = base64.b64decode(encoded)
    encoded = encoded.hex()
    i = 0
    while i < len(encoded):
        try:
            records.append(decode_bcgps(encoded[i : i + 40]))
        except Exception:
            pass
        i += 40
    return records


schemaFormat = ArrayType(
    StructType(
        [
            StructField("serialNumber", StringType(), False),
            StructField("utcTime", TimestampType(), False),
            StructField(
                "Location",
                StructType(
                    [
                        StructField("type", StringType(), False),
                        StructField("latitude", DoubleType(), False),
                        StructField("longitude", DoubleType(), False),
                    ]
                ),
                False,
            ),
            StructField("Speed", DoubleType(), False),
            StructField("Heading", DoubleType(), False),
            StructField("Valid", StringType(), False),
        ]
    )
)
