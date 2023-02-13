import boto3
import requests
import json
import os
import time
from functools import reduce
from boto3.dynamodb.conditions import Attr
import pyodbc

########################################################################################
apiCNT = boto3.client("apigateway")
apiIDList = [
    item["id"]
    for item in apiCNT.get_rest_apis()["items"]
    if item["name"] == "VPSAUTOMATIONSTEST"
]
apiId = apiIDList[0]
########################################################################################
customerAgency = "GLOBALINFRA"
codeBuildDynamo = "codeBuildDeploy"
cdBuild = boto3.client("codebuild")
client = boto3.client("dynamodb")
clientDynamoRES = boto3.resource("dynamodb")
clientLambda = boto3.client("lambda")
clientSecretMan = boto3.client("secretsmanager")
clientAPI = f"https://{apiId}.execute-api.us-east-1.amazonaws.com/Prod"
cdbuild = boto3.client("codebuild", region_name="us-east-1")
########################################################################################


def retResponseHTTPS(fileName):
    """[summary]
    Function to call api and return the list which contains https status code and
     http text response
    Arguments:
        fileName {[string]} -- [file name with csv extension should be passed]

    Returns:
        [type] -- [http status code, http status]
    """
    os.getcwd()
    url = clientAPI + "/cms/devices/deviceConfig"
    headers = {"Content-type": "application/csv"}
    r = requests.post(
        url,
        headers=headers,
        data=open(
            (os.getcwd() + "/ImportCsvTestCases/" + fileName).replace(
                "/CodeCommitCopy", ""
            ),
            "rb",
        ).read(),
    )
    return [r.status_code, r.text]


#####################################
def get_cms_connection(customerName):
    """Takes the customerName and retrieves the CMS username, password and
    ip address from AWS Secrets Manager

    Arguments:
        customerName {String} -- The name of the customer to retrieve details for

    Returns:
        String -- username for the CMS database
        String -- password for the CMS database
        String -- ip address for the CMS database
    """
    driver = "{ODBC Driver 17 for SQL Server}"
    cms_credentials = json.loads(
        clientSecretMan.get_secret_value(SecretId=customerName)["SecretString"]
    )
    cnx = pyodbc.connect(
        f'DRIVER={driver};SERVER={cms_credentials["host"]};'
        f'DATABASE=OpticomManagement;UID={cms_credentials["username"]};'
        f'PWD={cms_credentials["password"]}'
    )
    return cnx


def test_emptyTables():
    cursor = get_cms_connection(customerAgency).cursor()
    cursor.execute("SELECT * FROM [OpticomManagement].[dbo].[Location];")
    assert 0 == len([row for row in cursor.fetchall()])
    cursor = get_cms_connection(customerAgency).cursor()
    cursor.execute("SELECT * FROM [OpticomManagement].[dbo].[Region];")
    assert 0 == len([row for row in cursor.fetchall()])
    cursor = get_cms_connection(customerAgency).cursor()
    cursor.execute("SELECT * FROM [OpticomManagement].[dbo].[CommunicationDevice];")
    assert 0 == len([row for row in cursor.fetchall()])


########################################################################################
codbcd = {
    "customerName": customerAgency,
    "dockerImage": "083011521439.dkr.ecr.us-east-1.amazonaws.com/smartcity",
    "serverProperties": {
        "securityGroup": ["sg-0097d643551a742de"],
        "subnetID": "subnet-3ae59214",
    },
    "serverRegion": "us-east-1",
    "ImageId": "ami-0f22545d00916181b",
}

# gttins = {
#     "customerName": "GTT",
#     "IamName": "VPSAPI1-RootInstanceProfile-VJGGDOVTU0HG",
#     "S3Location": [
#         "us-east-1##gtt-deploy-vps-us-east-1-3bc570635",
#         "us-east-2##gtt-deploy-vps-us-east-2-7f4ea148f",
#         "us-west-1##gtt-deploy-vps-us-west-1-293c87e34",
#         "us-west-2##gtt-deploy-vps-us-west-2-18ef93c58",
#     ],
# }


def test_upddateDynamo():
    # insert to globalMacVps
    boto3.client("dynamodb").put_item(
        TableName="globalMacVps",
        Item={
            "primaryKey": {"N": "11111"},
            "macCode": {"N": "224754297012224"},
            "VPS": {"S": "V764MH0000"},
        },
    )

    # insert to codeBuildDeploy
    boto3.resource("dynamodb").Table(codeBuildDynamo).put_item(Item=codbcd)

    # boto3.resource("dynamodb").Table("codeBuildDeploy").put_item(Item=gttins)
    print("\n updating the two tables completed")


########################################################################################
def vpscreateINIT():
    event = {"body": '{"customer": "GLOBALINFRA","deviceprefix": "V764","number": 100}'}
    invks = clientLambda.invoke(
        FunctionName="gttvpscreate",
        InvocationType="RequestResponse",
        Payload=bytes(json.dumps(event), encoding="utf8"),
    )
    lambdINKS = json.loads(invks["Payload"].read().decode("utf-8"))
    return lambdINKS


def removeLstInvke():
    boto3.resource("dynamodb").Table(codeBuildDynamo).update_item(
        Key={"customerName": customerAgency},
        UpdateExpression="REMOVE lastInvokeVpscreate",
    )


#             CHECKSIGN FOR THE EMPTY SQL SERVER TABLES
# Some other example server values are
# server = 'localhost\sqlexpress' # for a named instance
# server = 'myserver,port' # to specify an alternate port
driver = "{ODBC Driver 17 for SQL Server}"
server = "34.202.114.18"
database = "OpticomManagement"
username = "spark_user"
password = "spark_user123"
cnxn = pyodbc.connect(
    f"DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}"
)
cursor = cnxn.cursor()
cursor.execute("SELECT * FROM [OpticomManagement].[dbo].[Location];")
len([row for row in cursor.fetchall()])
cursor.execute("SELECT * FROM [OpticomManagement].[dbo].[Region];")
len([row for row in cursor.fetchall()])
cursor.execute("SELECT * FROM [OpticomManagement].[dbo].[CommunicationDevice];")
len([row for row in cursor.fetchall()])

########################################################################################
#                        VPS create lambda and api testing
########################################################################################
# because pytest executes faster, we have added the wait time to check the dynamo db
time.sleep(60)


def test_vpscreateLambda():
    removeLstInvke()
    lambdINKS = vpscreateINIT()
    assert lambdINKS["statusCode"] == 200
    print("\n TEST 1 RETURN MESSAGE " + lambdINKS["body"])
    print("\n LAMBDA SUCCESSFUL creating records in dynamoDB")
    lambdINKS = vpscreateINIT()
    assert lambdINKS["statusCode"] == 429
    print("\n TEST 2 RETURN MESSAGE " + lambdINKS["body"])
    print("\n REMOVE last update to verify again")
    removeLstInvke()
    lambdINKS = vpscreateINIT()
    assert lambdINKS["statusCode"] == 200
    print("\n TEST 3 RETURN MESSAGE " + lambdINKS["body"])
    print("\n LAMBDA SUCCESSFUL again creating records in dynamoDB")
    event = {
        "body": '{"customer": "GLOBALINFRA","deviceprefix": "V764","number": "100"}'
    }
    invks = clientLambda.invoke(
        FunctionName="gttvpscreate",
        InvocationType="RequestResponse",
        Payload=bytes(json.dumps(event), encoding="utf8"),
    )
    lambdINKS = json.loads(invks["Payload"].read().decode("utf-8"))
    assert lambdINKS["statusCode"] == 400
    print("\n TEST 4 RETURN MESSAGE " + lambdINKS["body"])
    print("\n LAMBDA SUCCESSFUL in validating the records")


def test_vpscreateAPI():
    removeLstInvke()
    jsnInps = {"customer": customerAgency, "deviceprefix": "V764", "number": 100}
    r = requests.post(clientAPI + "/vps", data=json.dumps(jsnInps))
    assert r.status_code == 200
    print("\n TEST 1 SUCCESSFUL")
    print("\n API SUCCESSFUL creating records in dynamoDB")
    r = requests.post(clientAPI + "/vps", data=json.dumps(jsnInps))
    assert r.status_code == 429
    print("\n TEST 2 SUCCESSFUL")
    print(
        "\n API SUCCESSFUL in verifying too many requests. minimum of "
        "15 minutes required to invoke the lambda"
    )
    removeLstInvke()
    r = requests.post(clientAPI + "/vps", data=json.dumps(jsnInps))
    assert r.status_code == 200
    print("\n TEST 3 SUCCESSFUL")
    print("\n API SUCCESSFUL again in creating records in dynamoDB")
    print("\n Passing invalid input Parameter")
    jsnInps = {"customer": customerAgency, "deviceprefix": "V764", "number": "100"}
    r = requests.post(clientAPI + "/vps", data=json.dumps(jsnInps))
    assert r.status_code == 400
    print("\n TEST 4 SUCCESSFUL")
    print("\n API SUCCESSFUL in validating parameters")


def test_vpsreadLambda():
    event = {"queryStringParameters": {"customerName": customerAgency}}
    invks = clientLambda.invoke(
        FunctionName="gttvpsread",
        InvocationType="RequestResponse",
        Payload=bytes(json.dumps(event), encoding="utf8"),
    )
    lambdINKS = json.loads(invks["Payload"].read().decode("utf-8"))
    assert lambdINKS["statusCode"] == 200
    print("\n TEST 1 SUCCESSFUL for existing agency")
    event = {"queryStringParameters": {"customerName": "GLOBALINFRA1"}}
    invks = clientLambda.invoke(
        FunctionName="gttvpsread",
        InvocationType="RequestResponse",
        Payload=bytes(json.dumps(event), encoding="utf8"),
    )
    lambdINKS = json.loads(invks["Payload"].read().decode("utf-8"))
    assert lambdINKS["statusCode"] == 404
    print("\n TEST 2 SUCCESSFUL for NON EXISTING AGENCY")


def test_vpsReadAPI():
    r = requests.get(clientAPI + "/vps", params={"customerName": customerAgency})
    assert r.status_code == 200
    print("\n TEST 1 SUCCESSFUL for existing agency")
    r = requests.get(clientAPI + "/vps", params={"customerName": "GLOBALINFRA1"})
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
        FunctionName="gttvpsupdate",
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
        "body": '{"VPSName":"'
        + vpsTstVariable["VPS"]["S"]
        + '","dockerStatus": "UPDATE"}'
    }
    invks = clientLambda.invoke(
        FunctionName="gttvpsupdate",
        InvocationType="RequestResponse",
        Payload=bytes(json.dumps(event), encoding="utf8"),
    )
    lambdINKS = json.loads(invks["Payload"].read().decode("utf-8"))
    assert lambdINKS["statusCode"] == 400
    print("\n TEST 3 SUCCESSFUL in validating invalid parameters")


def test_vpsUpdateAPI():
    vpsTstVariable = client.scan(TableName="globalMacVps")["Items"][0]
    jsnInps = {"VPSName": vpsTstVariable["VPS"]["S"], "dockerStatus": "INACTIVE"}
    r = requests.put(clientAPI + "/vps", data=json.dumps(jsnInps))
    assert r.status_code == 200
    print("\n TEST 1 SUCCESSFUL to update VPS docker status")
    testDBS = client.get_item(
        TableName="globalMacVps",
        Key={"primaryKey": {"N": vpsTstVariable["primaryKey"]["N"]}},
    )
    assert testDBS["Item"]["deviceStatus"]["S"] == "INACTIVE"
    print("\n TEST 2 SUCCESSFUL to update VPS docker status in the dynamoDB")
    jsnInps = {"VPSName": vpsTstVariable["VPS"]["S"], "dockerStatus": "UPDATE"}
    r = requests.put(clientAPI + "/vps", data=json.dumps(jsnInps))
    assert r.status_code == 400
    print("\n TEST 3 SUCCESSFUL in validating invalid parameters")


def test_vpsUpdateDeleteLambda():
    vpsTstVariable = client.scan(TableName="globalMacVps")["Items"][0]
    event = {
        "body": '{"VPSName":"' + vpsTstVariable["VPS"]["S"] + '","dockerStatus": "YES"}'
    }
    invks = clientLambda.invoke(
        FunctionName="gttvpsupdate",
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
        + '","dockerStatus": "UPDATE"}'
    }
    invks = clientLambda.invoke(
        FunctionName="gttvpsupdate",
        InvocationType="RequestResponse",
        Payload=bytes(json.dumps(event), encoding="utf8"),
    )
    lambdINKS = json.loads(invks["Payload"].read().decode("utf-8"))
    assert lambdINKS["statusCode"] == 400
    print("\n TEST 3 SUCCESSFUL in validating invalid parameters")


def test_vpsUpdateDeleteAPI():
    vpsTstVariable = client.scan(TableName="globalMacVps")["Items"][0]
    jsnInps = {"VPSName": vpsTstVariable["VPS"]["S"], "dockerStatus": "YES"}
    r = requests.put(clientAPI + "/vps", data=json.dumps(jsnInps))
    assert r.status_code == 200
    print("\n TEST 1 SUCCESSFUL to update VPS docker status")
    testDBS = client.get_item(
        TableName="globalMacVps",
        Key={"primaryKey": {"N": vpsTstVariable["primaryKey"]["N"]}},
    )
    assert testDBS["Item"]["markToDelete"]["S"] == "YES"
    print("\n TEST 2 SUCCESSFUL to update VPS docker status in the dynamoDB")
    jsnInps = {"VPSName": vpsTstVariable["VPS"]["S"], "dockerStatus": "UPDATE"}
    r = requests.put(clientAPI + "/vps", data=json.dumps(jsnInps))
    assert r.status_code == 400
    print("\n TEST 3 SUCCESSFUL in validating invalid parameters")


def test_deleteAllbuilds():
    bulidList = cdBuild.list_builds_for_project(projectName="CODECOMMITPROJECT")["ids"]
    for item in bulidList:
        try:
            cdBuild.stop_build(id=item)
        except Exception:
            pass
    try:
        cdBuild.batch_delete_builds(ids=bulidList)
    except Exception:
        pass
    assert True
    print("\n TEST 1 SUCCESSFUL Removing the existing builds")


# @pytest.mark.skip()
def test_uploadFiles():
    os.chdir("./CodeCommitCopy")
    os.getcwd()
    client = boto3.client("codecommit")
    commitID = None
    trckLst = []
    repo_name = "GTTVPSDEPLOYMENT"
    for item in [
        f
        for f in os.listdir(os.curdir)
        if os.path.isfile(f) and (".yml" in f or ".py" in f)
    ]:
        if not commitID:
            response = client.put_file(
                repositoryName=repo_name,
                branchName="master",
                fileContent=open(item, "r").read().encode(),
                filePath=item,
            )
            trckLst.append(response["commitId"])
        else:
            response = client.put_file(
                repositoryName=repo_name,
                branchName="master",
                fileContent=open(item, "r").read().encode(),
                filePath=item,
                parentCommitId=commitID,
            )
            trckLst.append(response["commitId"])
        commitID = response["commitId"]
    assert 3 == len(trckLst)
    print("\n TEST 1 SUCCESSFUL adding files to the code commit")


def test_codeBuild():
    serverProperties = client.scan(
        TableName=codeBuildDynamo,
        FilterExpression="customerName = :custNm",
        ExpressionAttributeValues={":custNm": {"S": customerAgency}},
    )["Items"]
    customer_region = serverProperties[0]["serverRegion"]["S"]
    GTTProperties = client.scan(
        TableName=codeBuildDynamo,
        FilterExpression="customerName = :custNm",
        ExpressionAttributeValues={":custNm": {"S": "GTT"}},
    )["Items"]
    S3Location = {
        item[0]: item[1]
        for item in [
            item.split("##")
            for item in [d["S"] for d in GTTProperties[0]["S3Location"]["L"]]
        ]
    }
    response = cdbuild.start_build(
        projectName="CODECOMMITPROJECT",
        environmentVariablesOverride=[
            {"name": "customerName", "value": customerAgency, "type": "PLAINTEXT"},
            {"name": "customerRegion", "value": customer_region, "type": "PLAINTEXT"},
            {
                "name": "S3Location",
                "value": S3Location[customer_region],
                "type": "PLAINTEXT",
            },
        ],
    )
    assert response["build"]["id"] is not None
    print("\n TEST 1 SUCCESSFUL started the build for the Agency")
    time.sleep(330)
    assert (
        cdbuild.batch_get_builds(ids=[response["build"]["id"]])["builds"][0][
            "buildStatus"
        ]
        == "SUCCEEDED"
    )
    print("\n TEST 2 SUCCESSFUL in creating EC2 servers for Agency")


def test_deployDockers():
    serverProperties = client.scan(
        TableName=codeBuildDynamo,
        FilterExpression="customerName = :custNm",
        ExpressionAttributeValues={":custNm": {"S": customerAgency}},
    )["Items"]
    customer_region = serverProperties[0]["serverRegion"]["S"]
    ec2_client = boto3.client("ec2", region_name=customer_region)
    clientLambda.invoke(
        FunctionName="gttvpsdeploy",
        InvocationType="RequestResponse",
        Payload=bytes('{"customerName": "' + customerAgency + '"}', encoding="utf8"),
    )
    custom_filter = [
        {"Name": "tag:aws:cloudformation:stack-name", "Values": [customerAgency]},
        {"Name": "instance-state-name", "Values": ["running"]},
    ]
    agencyEc2 = [
        item["Instances"][0]["InstanceId"]
        for item in ec2_client.describe_instances(Filters=custom_filter)["Reservations"]
    ]
    ssmEC2List = reduce(
        lambda x, y: x + y,
        [
            ec2s["InstanceIds"]
            for ec2s in boto3.client("ssm", region_name="us-east-1").list_commands(
                Filters=[
                    {"key": "DocumentName", "value": "AWS-RunShellScript"},
                    {"key": "Status", "value": "InProgress"},
                ]
            )["Commands"]
        ],
    )
    assert ssmEC2List.sort() == agencyEc2.sort()
    print("\nSUCCESSFUL deploying the ssm sun commands")


def test_dockerUpdate():
    time.sleep(200)
    assert (
        len(
            clientDynamoRES.Table("globalMacVps").scan(
                FilterExpression=Attr("dockerStatus").eq("running")
            )["Items"]
        )
        > 25
    )
    print("\n SUCCESSFUL in updating the docker status")


def test_importCSV():
    # Testing duplicate location ID
    rid = retResponseHTTPS("DuplicateLocationId.csv")
    assert 400 == rid[0]
    print("\n SUCCESSFUL in validating the http status code for duplicate location id")
    assert 401 == json.loads(rid[1])["errorNumber"]
    print(
        "\n SUCCESSFUL in validating the error message number for "
        "duplicate location nid"
    )
    assert "location id" in json.loads(rid[1])["errorMessage"]
    print("\n SUCCESSFUL in validating the duplicate location id")
    # Testing duplicate location name
    rname = retResponseHTTPS("DuplicateLocationName.csv")
    assert 400 == rname[0]
    print(
        "\n SUCCESSFUL in validating the http status code for duplicate location name"
    )
    assert 401 == json.loads(rname[1])["errorNumber"]
    print(
        "\n SUCCESSFUL in validating the error message number for "
        "duplicate location name"
    )
    assert "location name" in json.loads(rname[1])["errorMessage"]
    print("\n SUCCESSFUL in validating the duplicate location name")
    # Testing request more VPS
    rmore = retResponseHTTPS("RequestMore.csv")
    assert 500 == rmore[0]
    print("\n SUCCESSFUL in validating the http status code for more VPS ")
    assert 506 == json.loads(rmore[1])["errorNumber"], "unable to connect to sqlserver"
    print("\n SUCCESSFUL in validating the error message number for more VPS")
    # Testing invalid jurisdiction
    rjusrid = retResponseHTTPS("InvalidJurisdiction.csv")
    assert 400 == rjusrid[0]
    print("\n SUCCESSFUL in validating the http status code for invalid Jurisdiction")
    assert 401 == json.loads(rjusrid[1])["errorNumber"]
    print(
        "\n SUCCESSFUL in validating the error message number for invalid Jurisdiction"
    )
    assert "jurisdiction name" in json.loads(rjusrid[1])["errorMessage"]
    print("\n SUCCESSFUL in validating the inavlid Jurisdiction")
    # Testing non constant value jurisdiction
    rjusrid = retResponseHTTPS("NonConstantValueJurisdiction.csv")
    assert 400 == rjusrid[0]
    print(
        "\n SUCCESSFUL in validating the http status code for non constant Jurisdiction"
    )
    assert 401 == json.loads(rjusrid[1])["errorNumber"]
    print(
        "\n SUCCESSFUL in validating the error message number for "
        "non constant Jurisdiction"
    )
    assert "not contain constant values" in json.loads(rjusrid[1])["errorMessage"]
    print("\n SUCCESSFUL in validating the non constant Jurisdiction")
    # Testing inavlid long
    rlong = retResponseHTTPS("InvalidLong.csv")
    assert 400 == rlong[0]
    print("\n SUCCESSFUL in validating the http status code for Longitude")
    assert 401 == json.loads(rlong[1])["errorNumber"]
    print("\n SUCCESSFUL in validating the error message number for Longitude")
    assert "longitude" in json.loads(rlong[1])["errorMessage"]
    print("\n SUCCESSFUL in validating the Longitude")
    # Testing inavlid latitude
    rlat = retResponseHTTPS("InvalidLat.csv")
    assert 400 == rlat[0]
    print("\n SUCCESSFUL in validating the http status code for Latitude")
    assert 401 == json.loads(rlat[1])["errorNumber"]
    print("\n SUCCESSFUL in validating the error message number for Latitude")
    assert "latitude" in json.loads(rlat[1])["errorMessage"]
    print("\n SUCCESSFUL in validating the Longitude")
    # Testing inavlid comm device type
    rcomdev = retResponseHTTPS("InvalidCommDevice.csv")
    assert 400 == rlat[0]
    print("\n SUCCESSFUL in validating the http status code for invalid comm device")
    assert 401 == json.loads(rcomdev[1])["errorNumber"]
    print(
        "\n SUCCESSFUL in validating the error message number for invalid comm device"
    )
    assert "comm device type" in json.loads(rcomdev[1])["errorMessage"]
    print("\n SUCCESSFUL in validating the Longitude")
    # Testing for jurisdiction secret manager
    rcred = retResponseHTTPS("GetCredentials.csv")
    assert 500 == rcred[0]
    print(
        "\n SUCCESSFUL in validating the http status code for "
        "invalid jurisdiction secret manager"
    )
    assert 502 == json.loads(rcred[1])["errorNumber"]
    print(
        "\n SUCCESSFUL in validating the error message number for "
        "invalid jurisdiction secret manager"
    )
    assert "Unable to access cms credentials" in json.loads(rcred[1])["errorMessage"]
    print("\n SUCCESSFUL in validating the jurisdiction secret manager")
    rsuccess = retResponseHTTPS("PostmansTest.csv")
    assert 200 == rsuccess[0]
    print("\n SUCCESSFUL in importing the csv files")


def test_loadedSQlTables():
    time.sleep(30)  # wait until the step function gets executed
    cursor = get_cms_connection(customerAgency).cursor()
    cursor.execute("SELECT * FROM [OpticomManagement].[dbo].[Location];")
    assert 20 == len([row for row in cursor.fetchall()])
    cursor = get_cms_connection(customerAgency).cursor()
    cursor.execute("SELECT * FROM [OpticomManagement].[dbo].[Region];")
    assert 1 == len([row for row in cursor.fetchall()])
    cursor = get_cms_connection(customerAgency).cursor()
    cursor.execute("SELECT * FROM [OpticomManagement].[dbo].[CommunicationDevice];")
    assert 20 == len([row for row in cursor.fetchall()])
