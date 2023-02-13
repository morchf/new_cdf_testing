from pyspark.sql import SparkSession
from pyspark.sql import functions as f  # noqa: F401
from awsglue.utils import getResolvedOptions
import logging
import sys
import datetime
import boto3
from boto3.dynamodb.conditions import Attr
import RtradioCMSDecode as RTRADIOCMS  # noqa: F401
import Rtradio2100Decode as RTRADIO2100  # noqa: F401
import MP70Decode as MP70  # noqa: F401
import BCGPSDecode as BCGPS  # noqa: F401

# Script Arguments
args = getResolvedOptions(
    sys.argv,
    ["JOB_NAME", "sns_arn", "vehicle_data_s3", "dynamoDbTable", "customerName"],
)

# AWS Clients
customerName = args["customerName"]
productionIOTS3 = args["vehicle_data_s3"]
tableName = args["dynamoDbTable"].split("/")[-1]
tableRegion = args["dynamoDbTable"].split(":")[3]
s3_client = boto3.client("s3")
sns = boto3.client("sns", region_name=args["sns_arn"].split(":")[3])

# Build Spark Session
spark = SparkSession.builder.getOrCreate()
spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")
spark.conf.set("spark.sql.session.timeZone", "UTC")

# # Initialize and Query dynamoDb Table
dyanmoTable = boto3.resource("dynamodb", region_name=tableRegion).Table(tableName)
response = dyanmoTable.scan(FilterExpression=Attr("cutomerName").eq(customerName))


def repair_cvp_database_athena(dbName, tableName):
    # Repair Athena Tables for New Partitions
    client = boto3.client("athena", region_name="us-east-2")
    response = client.start_query_execution(
        QueryString="MSCK REPAIR TABLE " + tableName + " ;",
        QueryExecutionContext={"Database": dbName},
        ResultConfiguration={
            "OutputLocation": "s3://aws-glue-temporary-933020280538-us-east-2/"
        },
    )
    logging.info("Execution ID: " + response["QueryExecutionId"])
    logging.info(response)
    logging.info("partitons are updated in athena database")


def s3_path_exists(bucket, prefix):
    if (
        s3_client.list_objects_v2(Bucket=bucket, MaxKeys=1, Prefix=prefix).get(
            "Contents", None
        )
        is not None
    ):
        return True
    else:
        return False


def spark_any_path_exist(bucket, prefix, partitionName, partitionValues):
    anyExists = False
    for i in partitionValues:
        if s3_path_exists(bucket, f"{prefix.rstrip('/')}/{partitionName}={i}/"):
            anyExists = True
            break
    return anyExists


def update_dynamodb(dynamoTable, customerName, taskName):
    print("Updating Dynamo DB")
    dynamoTable.update_item(
        Key={"cutomerName": customerName, "taskName": taskName},
        UpdateExpression="SET lastSuccessfulTimestamp = :val1",
        ExpressionAttributeValues={
            ":val1": datetime.datetime.utcnow().strftime("%Y-%m-%d")
        },
    )
    print("Updated Dynamo DB")


for a in filter(lambda x: x["active"] == True, response["Items"]):  # noqa: E712
    taskImportFun = a["taskName"]
    lastsuccess = (
        datetime.datetime.today()
        - datetime.datetime.strptime(a["lastSuccessfulTimestamp"], "%Y-%m-%d")
    ).days
    dates_list = ",".join(
        map(
            str,
            [
                (datetime.datetime.now() - datetime.timedelta(days=x)).strftime(
                    "%Y/%m/%d"
                )
                for x in range(lastsuccess + 1)
            ],
        )
    )
    try:
        user_df = eval(
            "f.udf(lambda topic, encoded, utcTime: "
            + taskImportFun
            + ".decoders(topic, encoded, utcTime), "
            + taskImportFun
            + ".schemaFormat)"
        )
        df = spark.read.format("json").load(
            productionIOTS3 + "/" + a["taskName"] + "/" + "{" + dates_list + "}/*/"
        )
        decoded_df = eval(
            """df.select(user_df("topic", "buffer", "utcTime").alias("decoded"))\
                               .select(f.explode(f.col("decoded")).alias("decoded_exploded"))\
                               .select(f.col("decoded_exploded.*"))\
                               .withColumn("utcdate", f.to_date("""
            + taskImportFun
            + """.timeColumn, "yyyyMMdd"))\
                               .repartition(8)"""
        )

        df_dates = [
            i.utcdate.strftime("%Y-%m-%d")
            for i in decoded_df.select("utcdate").distinct().collect()
        ]
        bucket_name = productionIOTS3.replace("//", "//parquet-").split("/")[-2]
        prefix_names = f"{productionIOTS3.replace('//','//parquet-').split('/')[-1]}/{a['taskName']}"
        base_path = (
            productionIOTS3.replace("//", "//parquet-") + "/" + a["taskName"] + "/"
        )
        if spark_any_path_exist(bucket_name, prefix_names, "utcdate", df_dates):
            current_data = (
                spark.read.format("parquet")
                .option("basePath", base_path)
                .load(base_path + "utcdate={" + ",".join(df_dates) + "}/")
            )
            merged_data = (
                decoded_df.unionByName(current_data).dropDuplicates().repartition(8)
            )
            merged_data.write.format("parquet").mode("overwrite").partitionBy(
                "utcdate"
            ).save(base_path)
            update_dynamodb(dyanmoTable, a["cutomerName"], a["taskName"])
            repair_cvp_database_athena(a["database"], a["tableName"])
        else:
            decoded_df.write.format("parquet").mode("overwrite").partitionBy(
                "utcdate"
            ).save(base_path)
            update_dynamodb(dyanmoTable, a["cutomerName"], a["taskName"])
            repair_cvp_database_athena(a["database"], a["tableName"])
    except Exception as e:
        logging.error(e)
        sns.publish(
            TopicArn=args["sns_arn"], Message=(a["taskName"] + "-fail\n" + str(e))
        )
