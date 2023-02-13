import boto3
import requests
import json

########################################################################################
client = boto3.client("dynamodb", endpoint_url="http://172.16.123.1:8000/")
clientLambda = boto3.client("lambda", endpoint_url="http://127.0.0.1:3001/")
########################################################################################
codbcd = {
    "customerName": "GLOBALGTT",
    "dockerImage": "083011521439.dkr.ecr.us-east-1.amazonaws.com/smartcity",
    "lastInvokeVpscreate": "23/04/2020 19:35:05",
    "serverProperties": {
        "securityGroup": ["sg-0097d643551a742de"],
        "subnetID": "subnet-3ae59214",
    },
    "serverRegion": "us-east-1",
}

gttins = {
    "customerName": "GTT",
    "IamName": "VPSAPI1-RootInstanceProfile-VJGGDOVTU0HG",
    "S3Location": [
        "us-east-1##gtt-deploy-vps-us-east-1-3bc570635",
        "us-east-2##gtt-deploy-vps-us-east-2-7f4ea148f",
        "us-west-1##gtt-deploy-vps-us-west-1-293c87e34",
        "us-west-2##gtt-deploy-vps-us-west-2-18ef93c58",
    ],
}
########################################################################################


def test_dynamoBuild():
    client.create_table(
        AttributeDefinitions=[{"AttributeName": "primaryKey", "AttributeType": "N"}],
        TableName="globalMacVps",
        KeySchema=[{"AttributeName": "primaryKey", "KeyType": "HASH"}],
        ProvisionedThroughput={"ReadCapacityUnits": 50, "WriteCapacityUnits": 50},
    )
    print("\n globalMacVps table creation complete")

    client.create_table(
        AttributeDefinitions=[{"AttributeName": "customerName", "AttributeType": "S"}],
        TableName="codeBuildDeploy",
        KeySchema=[{"AttributeName": "customerName", "KeyType": "HASH"}],
        ProvisionedThroughput={"ReadCapacityUnits": 50, "WriteCapacityUnits": 50},
    )
    print("\n codeBuildDeploy table creation complete")


########################################################################################


def test_upddateDynamo():
    # insert to globalMacVps
    boto3.client("dynamodb", endpoint_url="http://172.16.123.1:8000/").put_item(
        TableName="globalMacVps",
        Item={
            "primaryKey": {"N": "11111"},
            "macCode": {"N": "224754297012224"},
            "VPS": {"S": "V764MH0000"},
        },
    )

    # insert to codeBuildDeploy
    boto3.resource("dynamodb", endpoint_url="http://172.16.123.1:8000/").Table(
        "codeBuildDeploy"
    ).put_item(Item=codbcd)

    boto3.resource("dynamodb", endpoint_url="http://172.16.123.1:8000/").Table(
        "codeBuildDeploy"
    ).put_item(Item=gttins)
    print("\n updating the two tables completed")


########################################################################################


def vpscreateINIT():
    event = {"body": '{"customer": "GLOBALGTT","deviceprefix": "V764","number": 100}'}
    invks = clientLambda.invoke(
        FunctionName="VPSCREATE",
        InvocationType="RequestResponse",
        Payload=bytes(json.dumps(event), encoding="utf8"),
    )
    lambdINKS = json.loads(invks["Payload"].read().decode("utf-8"))
    return lambdINKS


def removeLstInvke():
    boto3.resource("dynamodb", endpoint_url="http://172.16.123.1:8000/").Table(
        "codeBuildDeploy"
    ).update_item(
        Key={"customerName": "GLOBALGTT"}, UpdateExpression="REMOVE lastInvokeVpscreate"
    )


########################################################################################
#                        VPS create lambda and api testing
########################################################################################


def test_vpscreateLambda():
    removeLstInvke()
    lambdINKS = vpscreateINIT()
    assert lambdINKS["statusCode"] == 200
    print("\n TEST 1 RETURN MESSAGE " + lambdINKS["body"])
    print("\n LAMBDA SUCCESSFUL creating records in dynamoDB")
    lambdINKS = vpscreateINIT()
    assert lambdINKS["statusCode"] == 429
    print("\n TEST 2 RETURN MESSAGE " + lambdINKS["body"])
    print(
        "\n LAMBDA SUCCESSFUL in verifying too many requests. minimum of "
        "15 minutes required to invoke the lambda"
    )
    print("\n REMOVE last update to verify again")
    removeLstInvke()
    lambdINKS = vpscreateINIT()
    assert lambdINKS["statusCode"] == 200
    print("\n TEST 3 RETURN MESSAGE " + lambdINKS["body"])
    print("\n LAMBDA SUCCESSFUL again creating records in dynamoDB")
    event = {"body": '{"customer": "GLOBALGTT","deviceprefix": "V764","number": "100"}'}
    invks = clientLambda.invoke(
        FunctionName="VPSCREATE",
        InvocationType="RequestResponse",
        Payload=bytes(json.dumps(event), encoding="utf8"),
    )
    lambdINKS = json.loads(invks["Payload"].read().decode("utf-8"))
    assert lambdINKS["statusCode"] == 400
    print("\n TEST 4 RETURN MESSAGE " + lambdINKS["body"])
    print("\n LAMBDA SUCCESSFUL in validating the records")


def test_vpscreateAPI():
    removeLstInvke()
    jsnInps = {"customer": "GLOBALGTT", "deviceprefix": "V764", "number": 100}
    r = requests.post("http://127.0.0.1:3000/vps", data=json.dumps(jsnInps))
    assert r.status_code == 200
    print("\n TEST 1 SUCCESSFUL")
    print("\n API SUCCESSFUL creating records in dynamoDB")
    r = requests.post("http://127.0.0.1:3000/vps", data=json.dumps(jsnInps))
    assert r.status_code == 429
    print("\n TEST 2 SUCCESSFUL")
    print(
        "\n API SUCCESSFUL in verifying too many requests. minimum of "
        "15 minutes required to invoke the lambda"
    )
    removeLstInvke()
    r = requests.post("http://127.0.0.1:3000/vps", data=json.dumps(jsnInps))
    assert r.status_code == 200
    print("\n TEST 3 SUCCESSFUL")
    print("\n API SUCCESSFUL agian in creating records in dynamoDB")
    print("\n Passing invalid input Parameter")
    jsnInps = {"customer": "GLOBALGTT", "deviceprefix": "V764", "number": "100"}
    r = requests.post("http://127.0.0.1:3000/vps", data=json.dumps(jsnInps))
    assert r.status_code == 400
    print("\n TEST 4 SUCCESSFUL")
    print("\n API SUCCESSFUL in validating parameters")


def test_vpsreadLambda():
    event = {"queryStringParameters": {"customerName": "GLOBALGTT"}}
    invks = clientLambda.invoke(
        FunctionName="VPSREAD",
        InvocationType="RequestResponse",
        Payload=bytes(json.dumps(event), encoding="utf8"),
    )
    lambdINKS = json.loads(invks["Payload"].read().decode("utf-8"))
    assert lambdINKS["statusCode"] == 200
    print("\n TEST 1 SUCCESSFUL for existing agency")
    event = {"queryStringParameters": {"customerName": "GLOBALGTT1"}}
    invks = clientLambda.invoke(
        FunctionName="VPSREAD",
        InvocationType="RequestResponse",
        Payload=bytes(json.dumps(event), encoding="utf8"),
    )
    lambdINKS = json.loads(invks["Payload"].read().decode("utf-8"))
    assert lambdINKS["statusCode"] == 404
    print("\n TEST 2 SUCCESSFUL for NON EXISTING AGENCY")


def test_vpsReadAPI():
    r = requests.get("http://127.0.0.1:3000/vps", params={"customerName": "GLOBALGTT"})
    assert r.status_code == 200
    print("\n TEST 1 SUCCESSFUL for existing agency")
    r = requests.get("http://127.0.0.1:3000/vps", params={"customerName": "GLOBALGTT1"})
    assert r.status_code == 404
    print("\n TEST 2 SUCCESSFUL for existing agency")


def test_vpsUpdateLambda():
    vpsTstVariable = client.scan(TableName="globalMacVps")["Items"][0]
    event = {
        "body": '{"VPSName":"'
        + vpsTstVariable["VPS"]["S"]
        + '","dockerStatus": "INACTIVE"}'
    }
    invks = clientLambda.invoke(
        FunctionName="VPSUPDATE",
        InvocationType="RequestResponse",
        Payload=bytes(json.dumps(event), encoding="utf8"),
    )
    lambdINKS = json.loads(invks["Payload"].read().decode("utf-8"))
    assert lambdINKS["statusCode"] == 200
    print("\n TEST 1 SUCCESSFUL to update VPS docker status")
    testDBS = client.get_item(
        TableName="globalMacVps",
        Key={"primaryKey": {"N": vpsTstVariable["primaryKey"]["N"]}},
    )
    assert testDBS["Item"]["deviceStatus"]["S"] == "INACTIVE"
    print("\n TEST 2 SUCCESSFUL to update VPS docker status in the dynamoDB")
    event = {
        "body": '{"VPSName":"' + vpsTstVariable["VPS"]["S"] + '","dockerStatus": "YES"}'
    }
    invks = clientLambda.invoke(
        FunctionName="VPSUPDATE",
        InvocationType="RequestResponse",
        Payload=bytes(json.dumps(event), encoding="utf8"),
    )
    lambdINKS = json.loads(invks["Payload"].read().decode("utf-8"))
    assert lambdINKS["statusCode"] == 400
    print("\n TEST 3 SUCCESSFUL in validating invalid parameters")


def test_vpsUpdateAPI():
    vpsTstVariable = client.scan(TableName="globalMacVps")["Items"][0]
    jsnInps = {"VPSName": vpsTstVariable["VPS"]["S"], "dockerStatus": "INACTIVE"}
    r = requests.put("http://127.0.0.1:3000/vps", data=json.dumps(jsnInps))
    assert r.status_code == 200
    print("\n TEST 1 SUCCESSFUL to update VPS docker status")
    testDBS = client.get_item(
        TableName="globalMacVps",
        Key={"primaryKey": {"N": vpsTstVariable["primaryKey"]["N"]}},
    )
    assert testDBS["Item"]["deviceStatus"]["S"] == "INACTIVE"
    print("\n TEST 2 SUCCESSFUL to update VPS docker status in the dynamoDB")
    jsnInps = {"VPSName": vpsTstVariable["VPS"]["S"], "dockerStatus": "YES"}
    r = requests.put("http://127.0.0.1:3000/vps", data=json.dumps(jsnInps))
    assert r.status_code == 400
    print("\n TEST 3 SUCCESSFUL in validating invalid parameters")


def test_vpsDeleteLambda():
    vpsTstVariable = client.scan(TableName="globalMacVps")["Items"][0]
    event = {
        "body": '{"VPSName":"' + vpsTstVariable["VPS"]["S"] + '","dockerDelete": "YES"}'
    }
    invks = clientLambda.invoke(
        FunctionName="VPSDELETE",
        InvocationType="RequestResponse",
        Payload=bytes(json.dumps(event), encoding="utf8"),
    )
    lambdINKS = json.loads(invks["Payload"].read().decode("utf-8"))
    assert lambdINKS["statusCode"] == 200
    print("\n TEST 1 SUCCESSFUL to update VPS docker status")
    testDBS = client.get_item(
        TableName="globalMacVps",
        Key={"primaryKey": {"N": vpsTstVariable["primaryKey"]["N"]}},
    )
    assert testDBS["Item"]["markToDelete"]["S"] == "YES"
    print("\n TEST 2 SUCCESSFUL to update VPS docker status in the dynamoDB")
    event = {
        "body": '{"VPSName":"'
        + vpsTstVariable["VPS"]["S"]
        + '","dockerDelete": "INACTIVE"}'
    }
    invks = clientLambda.invoke(
        FunctionName="VPSDELETE",
        InvocationType="RequestResponse",
        Payload=bytes(json.dumps(event), encoding="utf8"),
    )
    lambdINKS = json.loads(invks["Payload"].read().decode("utf-8"))
    assert lambdINKS["statusCode"] == 400
    print("\n TEST 3 SUCCESSFUL in validating invalid parameters")


def test_vpsDeleteAPI():
    vpsTstVariable = client.scan(TableName="globalMacVps")["Items"][0]
    jsnInps = {"VPSName": vpsTstVariable["VPS"]["S"], "dockerDelete": "YES"}
    r = requests.delete("http://127.0.0.1:3000/vps", data=json.dumps(jsnInps))
    assert r.status_code == 200
    print("\n TEST 1 SUCCESSFUL to update VPS docker status")
    testDBS = client.get_item(
        TableName="globalMacVps",
        Key={"primaryKey": {"N": vpsTstVariable["primaryKey"]["N"]}},
    )
    assert testDBS["Item"]["markToDelete"]["S"] == "YES"
    print("\n TEST 2 SUCCESSFUL to update VPS docker status in the dynamoDB")
    jsnInps = {"VPSName": vpsTstVariable["VPS"]["S"], "dockerDelete": "INACTIVE"}
    r = requests.delete("http://127.0.0.1:3000/vps", data=json.dumps(jsnInps))
    assert r.status_code == 400
    print("\n TEST 3 SUCCESSFUL in validating invalid parameters")
