import os
import boto3
import datetime
import pandas as pd
import io
import json
import sys
from botocore.awsrequest import AWSRequest
from botocore.endpoint import URLLib3Session
from botocore.auth import SigV4Auth
from awsglue.utils import getResolvedOptions

args = getResolvedOptions(
    sys.argv, ["s3DataVizBucket", "S3DataPipelineBucket", "DatasetName", "CDFEndpoint"]
)
s3 = boto3.client("s3")
dateprefix = datetime.datetime.now().strftime("%Y-%m-%d")

headers = {
    "Accept": "application/vnd.aws-cdf-v2.0+json",
    "Content-Type": "application/vnd.aws-cdf-v2.0+json",
}
cdf_endpoint = args["CDFEndpoint"]


def pd_read_s3_parquet(bucket, key, s3_client):
    obj = s3_client.get_object(Bucket=bucket, Key=key)
    return pd.read_parquet(io.BytesIO(obj["Body"].read()))


def pd_read_s3_multiple_parquets(bucket, filepath):
    filepath = f"{filepath.rstrip('/')}/"
    s3 = boto3.resource("s3")
    s3_client = boto3.client("s3")

    s3_keys = [
        item.key
        for item in s3.Bucket(bucket).objects.filter(Prefix=filepath)
        if item.key.endswith(".parquet")
    ]
    dfs = [pd_read_s3_parquet(bucket, key, s3_client) for key in s3_keys]
    return pd.concat(dfs, ignore_index=True)


def test_use_data():
    df = pd.read_csv(os.path.join(os.path.dirname(__file__), "MP70data.csv"))
    print(df)

    df = pd.read_csv(os.path.join(os.path.dirname(__file__), "2100data.csv"))
    print(df)


def sendRequest(method, url, creds, headers={}, data={}):
    request = AWSRequest(method=method, url=url, data={}, headers=headers)

    SigV4Auth(creds, "execute-api", "us-east-1").add_auth(request)

    return URLLib3Session().send(request.prepare())


def ushort(val):
    return int("".join([val[i : i + 2] for i in range(0, len(val), 2)][::-1]), 16)


def get2100Sn(mp70sn, creds):
    try:
        response = sendRequest(
            "GET", f"{cdf_endpoint}/devices/{mp70sn}", creds, headers
        )
        Sn2100 = int(
            "008"
            + json.loads(response.content)["attributes"]["addressMAC"]
            .replace(":", "")
            .zfill(5)[-5:],
            16,
        ).to_bytes(4, byteorder="little", signed=False)
        return ushort(Sn2100.hex())
    except Exception:
        return None


s3.put_object(
    Bucket=args["s3DataVizBucket"],
    Key="VISUALIZATIONS/VEHICLETROUBLESHOOTING/stepFunctionResult.json",
    Body=json.dumps(
        {
            "status": "SUCCESS",
            "resultTimestamp": datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
        }
    ),
)

final_df = pd.DataFrame(
    columns=["mp70SN", "mp70Timestamp", "2100SN", "2100Timestamp", "CMSTimestamp"]
)

# MP70
try:
    df = pd_read_s3_multiple_parquets(
        args["S3DataPipelineBucket"], f"SCPVehicleData/MP70/utcdate={dateprefix}"
    )
    creds = boto3.Session().get_credentials()
    df = (
        df.sort_values(by=["vehSN", "utcTime"], ascending=False)
        .drop_duplicates(subset=["vehSN"], keep="first")
        .reset_index(drop=True)
    )
    df["mp70SN"] = df["vehSN"]
    df["mp70Timestamp"] = df["utcTime"]
    df["2100SN"] = [
        get2100Sn(df["mp70SN"].iat[i], creds) for i in range(len(df["mp70SN"]))
    ]
    final_df = pd.merge(
        final_df[["2100SN", "2100Timestamp", "CMSTimestamp"]],
        df[["mp70SN", "mp70Timestamp", "2100SN"]],
        on="2100SN",
        how="outer",
    )
except Exception as e:
    print(f"Missing MP70 data for date {dateprefix}. {e}")

# 2100
try:
    df2 = pd_read_s3_multiple_parquets(
        args["S3DataPipelineBucket"], f"SCPVehicleData/RTRADIO2100/utcdate={dateprefix}"
    )
    df2 = (
        df2.sort_values(by=["vehSN", "utcTime"], ascending=False)
        .drop_duplicates(subset=["vehSN"], keep="first")
        .reset_index(drop=True)
    )
    df2["2100SN"] = df2["vehSN"]
    df2["2100Timestamp"] = df2["utcTime"]
    df2100 = df2[["2100SN", "2100Timestamp"]]
    final_df = pd.merge(
        final_df[["2100SN", "mp70SN", "mp70Timestamp", "CMSTimestamp"]],
        df2100,
        on="2100SN",
        how="outer",
    )
except Exception as e:
    print(f"Missing 2100 data for date {dateprefix}. {e}")

# CMS
try:
    df3 = pd_read_s3_multiple_parquets(
        args["S3DataPipelineBucket"], f"SCPVehicleData/RTRADIOCMS/utcdate={dateprefix}"
    )
    df3 = (
        df3.sort_values(by=["vehSN", "utcTime"], ascending=False)
        .drop_duplicates(subset=["vehSN"], keep="first")
        .reset_index(drop=True)
    )
    df3["2100SN"] = df3["vehSN"]
    df3["CMSTimestamp"] = df3["utcTime"]
    dfCMS = df3[["2100SN", "CMSTimestamp"]]
    final_df = pd.merge(
        final_df[["2100SN", "mp70SN", "mp70Timestamp", "2100Timestamp"]],
        dfCMS,
        on="2100SN",
        how="outer",
    )
except Exception as e:
    print(f"Missing CMS data for date {dateprefix}. {e}")

s = io.StringIO()
final_df = final_df.reindex(sorted(final_df.columns), axis=1)
final_df.to_csv(s, index=False)
s3.put_object(
    Bucket=args["s3DataVizBucket"],
    Key="VISUALIZATIONS/VEHICLETROUBLESHOOTING/vehicleResults.csv",
    Body=s.getvalue(),
)
