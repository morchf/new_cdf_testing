import time
import ast


def lambda_handler(event, context):
    msgVal = ast.literal_eval(event["Records"][0]["body"])
    print(msgVal)
    msgVal["Records"][0]["dynamodb"]["Keys"]["primaryKey"]["N"]
    try:
        newStatus = msgVal["Records"][0]["dynamodb"]["NewImage"]["deviceStatus"]["S"]
        oldStatus = msgVal["Records"][0]["dynamodb"]["OldImage"]["deviceStatus"]["S"]
    except Exception:
        newStatus = msgVal["Records"][0]["dynamodb"]["NewImage"]["markToDelete"]["S"]
        oldStatus = msgVal["Records"][0]["dynamodb"]["OldImage"]["markToDelete"]["S"]
    if newStatus != oldStatus:
        print(newStatus)
    time.sleep(5)
