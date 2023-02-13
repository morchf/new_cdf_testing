import os, sys, base64, datetime, re, binascii, datetime, json
from pyspark.sql.types import *
timeColumn='utcTime'
def decoders(topic, encoded, utcTime):
    decoded = json.loads(base64.b64decode(encoded).decode('utf-8'))
    key = list(decoded.keys())[0]
    return [{
        'vehSN': topic.split('/')[0],
        'utcTime': datetime.datetime.fromtimestamp(int(key)),
        'gspd': decoded[key].get('atp.gspd'),
        'gstt': decoded[key].get('atp.gstt'),
        'gpi': decoded[key].get('atp.gpi'),
        'gqal': decoded[key].get('atp.gqal'),
        'ghed': decoded[key].get('atp.ghed'),
        'gsat': decoded[key].get('atp.gsat'),
        'glon': decoded[key].get('atp.glon'),
        'glat': decoded[key].get('atp.glat')
    }]

schemaFormat = ArrayType(
    StructType([
        StructField("vehSN", StringType(), False),
        StructField("utcTime", TimestampType(), False),
        StructField("gspd", IntegerType(), True),
        StructField("gstt", IntegerType(), True),
        StructField("gpi", IntegerType(), True),
        StructField("gqal", IntegerType(), True),
        StructField("ghed", IntegerType(), True),
        StructField("gsat", IntegerType(), True),
        StructField("glon", DoubleType(), True),
        StructField("glat", DoubleType(), True)
    ])
)