import time
from os import getenv

import boto3

athena = boto3.client("athena")


def get_query_results(query_string):
    query_execution = athena.start_query_execution(
        QueryString=query_string,
        ResultConfiguration={
            "OutputLocation": f"s3://{getenv('ATHENA_OUTPUT_BUCKET')}"
        },
        WorkGroup=getenv("ATHENA_WORK_GROUP"),
    )

    while True:
        time.sleep(0.25)
        progress = athena.get_query_execution(
            QueryExecutionId=query_execution["QueryExecutionId"]
        )
        if progress["QueryExecution"]["Status"]["State"] in ["FAILED", "SUCCEEDED"]:
            break

    # todo: add error handling
    query_results = athena.get_query_results(
        QueryExecutionId=query_execution["QueryExecutionId"]
    )

    # modified code
    return_query_result = []
    while True:
        header = [
            data["VarCharValue"]
            for data in query_results["ResultSet"]["Rows"][0]["Data"]
        ]
        return_query_result += [
            {header[i]: data.get("VarCharValue") for i, data in enumerate(row["Data"])}
            for row in query_results["ResultSet"]["Rows"][1:]
        ]
        if not ("NextToken" in query_results):
            break
        query_results = athena.get_query_results(
            NextToken=query_results["NextToken"],
            QueryExecutionId=query_execution["QueryExecutionId"],
        )
    return return_query_result

    # existing code
    # header = [data["VarCharValue"] for data in query_results["ResultSet"]["Rows"][0]["Data"]]
    # return [{header[i]: data.get("VarCharValue") for i, data in enumerate(row["Data"])}
    #         for row in query_results["ResultSet"]["Rows"][1:]]
