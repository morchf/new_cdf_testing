# pip3 install jinja2
import boto3
import argparse
from boto3.dynamodb.conditions import Attr
from collections import Counter
from jinja2 import Template
from botocore.config import Config


########################################################################################
# collect parameters from the commandline
parser = argparse.ArgumentParser(
    description="Extracting parameters for cloudformation deployments"
)
parser.add_argument(
    "--customerName",
    required=True,
    help="provide the customer name (this will the cloudformation name)",
)
args = parser.parse_args()
# customers name
ecs_names = args.customerName
########################################################################################
dyanmoTable = boto3.resource("dynamodb", region_name="us-east-1").Table("globalMacVps")
response = dyanmoTable.scan(FilterExpression=Attr("customerName").eq(ecs_names))[
    "Items"
]
dynamo_ec2_grp_lst = sorted(
    list(
        Counter(
            token["serverName"] for token in response if token["markToDelete"] != "YES"
        ).items()
    )
)

serverProperties = (
    boto3.resource("dynamodb", region_name="us-east-1")
    .Table("codeBuildDeploy")
    .scan(FilterExpression=Attr("customerName").eq(ecs_names))["Items"]
)
# customer region
customer_region = serverProperties[0]["serverRegion"]
ecsSubnet = serverProperties[0]["serverProperties"]["subnetID"]
ecsSG = serverProperties[0]["serverProperties"]["securityGroup"]
ImageId = serverProperties[0]["ImageId"]
GTTProperties = (
    boto3.resource("dynamodb", region_name="us-east-1")
    .Table("codeBuildDeploy")
    .scan(FilterExpression=Attr("customerName").eq("GTT"))["Items"]
)
instanceProfile = GTTProperties[0]["IamName"]
config = Config(region_name=customer_region)


def retList(subID, requestIP):
    ipList = []
    ipAdd = boto3.resource("ec2", config=config).Subnet(subID).cidr_block.split("/")[0]
    startAdd = int(ipAdd.split(".")[-1]) + 6
    for n in range(startAdd, startAdd + requestIP):
        ipList.append(ipAdd.rsplit(".", 1)[0] + "." + str(n))
    return sorted(ipList)


newLST = [
    x[0] + (x[1],)
    for x in list(zip(dynamo_ec2_grp_lst, retList(ecsSubnet, len(dynamo_ec2_grp_lst))))
]
# #####################################################################################################################
try:
    if (
        boto3.client("ssm", region_name=customer_region).get_parameter(Name=ecs_names)[
            "Parameter"
        ]["Name"]
        == ecs_names
    ):
        True
except BaseException:
    keypair = boto3.client("ec2", region_name=customer_region).create_key_pair(
        KeyName=ecs_names
    )
    boto3.client("ssm", region_name=customer_region).put_parameter(
        Name=ecs_names,
        Value=keypair["KeyMaterial"],
        Type="SecureString",
        KeyId="alias/aws/ssm",
        Overwrite=False,
        Tags=[{"Key": "datagtt", "Value": "etl-jobs"}],
        Tier="Standard",
    )
########################################################################################
template = Template(open("CodeBuild.jinja").read())

output = template.render(
    items=newLST,
    customerName=ecs_names,
    amiId=ImageId,
    secGroup=ecsSG,
    subID=ecsSubnet,
    instanceProfile=instanceProfile,
)
print(
    "\n".join([i for i in output.split("\n") if len(i.strip()) > 0]),
    file=open("template.yml", "w"),
)
