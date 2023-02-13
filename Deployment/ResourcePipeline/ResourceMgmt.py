# import boto3, datetime, time
import boto3, time
import os
from datetime import datetime, timedelta
from botocore.config import Config
from botocore.exceptions import ClientError

account_name = print(os.environ["Env"])
print(account_name)

region = "us-east-1"


def get_session(region):
    return boto3.session.Session(region_name=region)


# Creates tags for EBS volumes that connect them to AWS Backup. Outputs correctly tagged volumes to a txt file.
def ebs_tag(region="us-east-1"):
    """Creates tags for EBS volumes that connect them to AWS Backup. Outputs correctly tagged
    volumes to a txt file."""
    session = get_session(region)
    resource = session.resource("ec2")
    volumes = resource.volumes.all()
    tagset = {"Key": "EBSKey", "Value": "EBSValue"}
    f = open("tagged_ebs_volumes.txt", "w+")

    for v in volumes:
        # if tagset not in v.tags:
        v.create_tags(Tags=[tagset])
        f.write(v.id + "\n")
    f.close()


# Tags all EFS for backup. Outputs correctly tagged EFS to a txt file
def efs_tag():
    """Tags all EFS for backup. Outputs correctly tagged
    EFS to a txt file"""
    client = boto3.client("efs")
    files = client.describe_file_systems()["FileSystems"]
    tagging = boto3.client("resourcegroupstaggingapi")
    f = open("tagged_efs_volumes.txt", "w+")
    tagset = {"EFSKey": "EFSValue"}
    for file in files:
        arn = [file["FileSystemArn"]]
        if tagset not in file["Tags"]:
            tagging.tag_resources(ResourceARNList=arn, Tags=tagset)
        f.write(file["FileSystemId"] + "\n")

    f.close()


# If a role hasn't been used in 6 months. Outputs roles to a txt file
def iam_mgmt(region="us-east-1"):
    '''If a role hasn't been used in 6 months, delete (output to file)
    Does not account for "An Error Occured"'''
    client = boto3.client("iam")
    resource = boto3.resource("iam")
    roles_list = client.list_roles(MaxItems=300)["Roles"]
    days_to_delete = 180
    # time_now = datetime.datetime.now()
    time_now = datetime.now()

    f = open("roles_to_delete.txt", "w+")

    for r in roles_list:
        role = resource.Role(name=r["RoleName"])
        if role.role_last_used:
            time_diff = time_now - role.role_last_used["LastUsedDate"].replace(
                tzinfo=None
            )
            if time_diff.days >= days_to_delete:
                f.write(role.role_name + ": " + str(time_diff.days) + "\n")
        else:
            f.write(role.role_name + ": No last used date." + "\n")

    f.close()


# Scans CloudwatchLogs for Lambdas. Checks if the lastEventTime from each log has been run in the past 6 months.
# If log has not been run in the past 6 months, delete (write to file).
# Cross-references inactive log names with lambda function names to identify unused lambdas.


def lambda_mgmt(region="us-east-1"):
    """
    Scans CloudwatchLogs for Lambdas. Checks if the lastEventTime from each log has been run in the past 6 months.
    If log has not been run in the past 6 months, delete (write to file).
    Cross-references inactive log names with lambda function names to identify unused lambdas.
    """
    config = Config(retries={"max_attempts": 10, "mode": "standard"})
    client = boto3.client("logs", config=config)
    paginator = client.get_paginator("describe_log_groups")
    iterator = paginator.paginate()
    six_months = (time.time() - 15778458) * 1000
    logs, filtered_logs = [], []
    funcs = lambda_work()

    logs_file = open("logs_to_delete.txt", "w+")
    lambdas_file = open("lambdas_to_delete.txt", "w+")

    for page in iterator:
        for group in page["logGroups"]:
            if "lambda" in group["logGroupName"]:
                logs.append(group)

    for log in logs:
        streams = client.describe_log_streams(
            logGroupName=log["logGroupName"], orderBy="LastEventTime", descending=True
        )["logStreams"]
        try:
            lastEventTime = streams[0]["lastEventTimestamp"]
        except:
            logs_file.write(log["logGroupName"] + ": " + "No log streams" + "\n")
            filtered_logs.append(log["logGroupName"][12:])
        if lastEventTime < six_months:
            logs_file.write(
                log["logGroupName"]
                + ": "
                # + str(datetime.datetime.fromtimestamp(lastEventTime / 1000))
                + str(datetime.fromtimestamp(lastEventTime / 1000))
                + "\n"
            )
            filtered_logs.append(log["logGroupName"][12:])

    for element in filtered_logs:
        if element in funcs:
            lambdas_file.write(element + "\n")

    logs_file.close()
    lambdas_file.close()


# Helper function to extract Lambda function names
def lambda_work():
    """Helper function to extract Lambda function names."""
    client = boto3.client("lambda")
    paginator = client.get_paginator("list_functions")
    iterator = paginator.paginate()
    funcs = []
    for page in iterator:
        for i in page["Functions"]:
            funcs.append(i["FunctionName"])
    return funcs


# Checks all DynamoDBs for encryption. Encrypts unencrypted DBs
def dynamo_encryption_check():
    """Checks all DynamoDBs for encryption.
    Encrypts unencrypted DBs."""
    client = boto3.client("dynamodb")
    response = client.list_tables()
    tables = response["TableNames"]
    f = open("dynamo_encrypted_tables.txt", "w+")
    for table in tables:
        try:
            table_des = client.describe_table(TableName=table)
            if table_des["Table"]["SSEDescription"]["Status"] == "ENABLED":
                f.write("Table: " + table + " is encrypted" + "\n")
        except:
            f.write("Table: " + table + " was not encrypted; Encrypting Table" + "\n")
            encrypt_table(table)
            continue
    f.close()


# Helper function that encrypts a DynamoDB
def encrypt_table(tablename):
    """Helper function that encrypts a DynamoDB."""
    client = boto3.client("dynamodb")
    client.update_table(
        TableName=tablename, SSESpecification={"Enabled": True, "SSEType": "KMS"}
    )


# Outputs the dynamodbs tagged for backup through AWS Backup
def dynamo_backup_status():
    """Outputs the dynamodbs tagged for backup through AWS Backup."""
    client = boto3.client("dynamodb")
    tables = client.list_tables()["TableNames"]
    tagset = {"Key": "DynamoDBKey", "Value": "DynamoDBValue"}
    tagged_for_backup, not_tagged_for_backup = [], []

    for table in tables:
        arn = client.describe_table(TableName=table)["Table"]["TableArn"]
        tags = client.list_tags_of_resource(ResourceArn=arn)["Tags"]
        if tagset in tags:
            tagged_for_backup.append(table)
        else:
            not_tagged_for_backup.append(table)

    line1 = (
        "Following DynamoDBs tagged 'DynamoDBKey:DynamoDBValue' are backed up in the vault DynamoDBVault:"
        + "\n"
    )
    line3 = (
        "Following DynamoDBs are not tagged with 'DynamoDBKey:DynamoDBValue' and will not be backed up:"
        + "\n"
    )
    with open("dynamodb_backup_status.txt", "w+") as out:
        out.writelines(line1)
        out.writelines(element + "\n" for element in tagged_for_backup)
        out.writelines(line3)
        out.writelines(element + "\n" for element in not_tagged_for_backup)


# Give the accesskey and password lastused info. Outputs accesskey_lastused and password_last_used to a txt file
def password_accesskey_check():
    resource = boto3.resource("iam")
    client = boto3.client("iam")

    # today = datetime.datetime.now()
    today = datetime.now()
    number = 1
    f = open("pass_accesskey_lastused.txt", "w+")

    for user in resource.users.all():

        keys_response = client.list_access_keys(UserName=user.user_name)
        last_access = None

        for key in keys_response["AccessKeyMetadata"]:

            last_used_response = client.get_access_key_last_used(
                AccessKeyId=key["AccessKeyId"]
            )
            if "LastUsedDate" in last_used_response["AccessKeyLastUsed"]:
                accesskey_last_used = last_used_response["AccessKeyLastUsed"][
                    "LastUsedDate"
                ]
                if last_access is None or accesskey_last_used < last_access:
                    last_access = accesskey_last_used

        if last_access is not None:
            delta = (today - last_access.replace(tzinfo=None)).days
            if delta >= 180:
                f.write(
                    "Access Key not used: username: "
                    + [user.user_name][0]
                    + " - "
                    + str(delta)
                    + " days\n"
                )
                number += 1

        if user.password_last_used is not None:
            delta = (today - user.password_last_used.replace(tzinfo=None)).days
            if delta >= 180:
                f.write(
                    "Password not used:  username: "
                    + [user.user_name][0]
                    + " - "
                    + str(delta)
                    + " days\n"
                )
                number += 1
    f.close()


# Give the log_stream names that are not updated in last 6 months. outputs in a txt file.
def log_streams(prefix=None):
    config = Config(retries={"max_attempts": 10, "mode": "standard"})
    tod = datetime.today() - timedelta(days=180)
    epoch_date = str(int(tod.timestamp()))
    previous_date = int(epoch_date.ljust(13, "0"))
    print(previous_date)
    f = open("log_stream_file.txt", "w+")

    """Delete CloudWatch Logs log streams with given prefix or all."""
    next_token = None
    logs = boto3.client("logs", config=config)

    if prefix:
        log_groups = logs.describe_log_groups(logGroupNamePrefix=prefix)
    else:
        log_groups = logs.describe_log_groups()

    for log_group in log_groups["logGroups"]:
        log_group_name = log_group["logGroupName"]
        print("log group:", log_group_name)
        f.write("log group: " + log_group_name + "\n")
        while True:
            if next_token:
                log_streams = logs.describe_log_streams(
                    logGroupName=log_group_name, nextToken=next_token
                )
            else:
                log_streams = logs.describe_log_streams(logGroupName=log_group_name)

            next_token = log_streams.get("nextToken", None)

            for stream in log_streams["logStreams"]:
                try:
                    if stream["lastEventTimestamp"] < previous_date:
                        log_stream_name = stream["logStreamName"]
                        f.write(log_stream_name + "\n")
                except KeyError:
                    print("logStreamName is not present")

            if not next_token or len(log_streams["logStreams"]) == 0:
                break
    f.close()


def unused_elastic_ips():
    client = boto3.client("ec2")
    addresses_dict = client.describe_addresses()
    f = open("unused_EIP.txt", "w+")
    for eip_dict in addresses_dict["Addresses"]:
        if "InstanceId" not in eip_dict:
            f.write(
                "Elastic IP: "
                + eip_dict["PublicIp"]
                + " doesn't have any instances associated"
                + "\n"
            )


def unused_volumes():
    AWS_REGION = "us-east-1"
    ec2_resource = boto3.resource("ec2", region_name=AWS_REGION)
    f = open("unused_volume.txt", "w+")
    for volume in ec2_resource.volumes.all():
        a = volume.create_time
        b = a.date()
        c = datetime.now().date()
        d = c - b
        if volume.state == "available" and d.days > 1095:
            f.write(f"Volume {volume.id} ({volume.size} GiB)  -> {volume.state}" + "\n")


def unused_loadbalancers():
    AWS_REGION = "us-east-1"
    client = boto3.client("elb", region_name=AWS_REGION)
    loadbalancers = client.describe_load_balancers()
    f = open("unused_loadbalancer.txt", "w+")
    for elb in loadbalancers["LoadBalancerDescriptions"]:
        f.write("Unused LB_Name " + elb["LoadBalancerName"] + "\n")


def unused_old_snapshots():
    client = boto3.client("ec2", region_name="us-east-1")
    snapshots = client.describe_snapshots(MaxResults=2000)
    f = open("unused_old_snapshots.txt", "w+")
    for snapshot in snapshots["Snapshots"]:
        a = snapshot["StartTime"]
        b = a.date()
        c = datetime.now().date()
        d = c - b
        if d.days > 1095:
            id = snapshot["SnapshotId"]
            f.write("unused_old_snapshots: " + id + "\n")


def get_used_amis_by_instances():
    REGION = "us-east-1"
    ec2_client = boto3.client("ec2", REGION)
    reservations = ec2_client.describe_instances(MaxResults=123)["Reservations"]
    amis_used_list = []
    for reservation in reservations:
        ec2_instances = reservation["Instances"]
        for ec2 in ec2_instances:
            ImageId = ec2["ImageId"]
            if ImageId not in amis_used_list:
                amis_used_list = amis_used_list + [ImageId]
    return amis_used_list


def get_all_amis():
    REGION = "us-east-1"
    ec2_resource = boto3.resource("ec2", REGION)
    amis = ec2_resource.images.filter(ExecutableUsers=["self"])
    all_amis = []
    for ami in amis.all():
        if ami.id not in all_amis:
            all_amis = all_amis + [ami.id]
    return all_amis


# Using this function we will try to findout the AMIs which is not attached to any EC2 instance and LaunchTime of AMI is greater than 2Months.
def get_unused_amis(all_amis, amis_used_list):
    REGION = "us-east-1"
    client = boto3.client("ec2", REGION)
    f = open("unused_amis.txt", "w+")
    unused_amis_list = []
    # For loop to iterate over all of the AMIs present in a AWS account
    for ami_id in all_amis:
        try:
            responce = client.describe_image_attribute(
                ImageId=str(ami_id), Attribute="lastLaunchedTime"
            )
            # print(responce)
            res = responce["LastLaunchedTime"]["Value"]
            a = datetime.fromisoformat(res[:-1] + "+00:00")
            print(a)
            b = a.date()
            c = datetime.now().date()
            d = c - b
            print(d)
            # If condition to check if an AMI is not present in the amis_used_list.
            if ami_id not in amis_used_list and d.days > 60:
                # If AMI is not present in the amis_used_list and unused_ami_list then adding the ami in unused_amis_list
                if ami_id not in unused_amis_list:
                    unused_amis_list = unused_amis_list + [
                        ami_id
                    ]  # Checking the ami in unused_amis_list for duplication purpose
                    print(unused_amis_list)
                    f.write(str(unused_amis_list))
        # except ClientError as e:
        except ClientError:
            continue
            # print("Unexpected error: %s" % e)


def unused_dynamodb_tables():
    AWS_REGION = "us-east-1"
    dynamodb_client = boto3.client("dynamodb", region_name=AWS_REGION)
    existing_tables = dynamodb_client.list_tables()["TableNames"]
    f = open("unused_dynamodb_tables.txt", "w+")
    for table_name in existing_tables:
        response = dynamodb_client.describe_table(TableName=table_name)
        if response["Table"]["ItemCount"] == 0:
            f.write("Unused Tables Names: " + table_name + "\n")


# Get the list of unused security groups
def unused_securitygroups():
    ec2 = boto3.client("ec2")
    all_instances = ec2.describe_instances()
    all_sg = ec2.describe_security_groups()
    all_eni = ec2.describe_network_interfaces()
    all_lambda = boto3.client("lambda")
    all_elb = boto3.client("elb")
    all_alb = boto3.client("elbv2")
    all_rds = boto3.client("rds")

    instance_sg_set = set()
    sg_set = set()
    elb_set = set()
    alb_set = set()
    rds_set = set()
    eni_set = set()
    lambda_set = set()
    # security groups used by Instances
    for reservation in all_instances["Reservations"]:
        for instance in reservation["Instances"]:
            for sg in instance["SecurityGroups"]:
                instance_sg_set.add(sg["GroupId"])

    # All Security groups
    for security_group in all_sg["SecurityGroups"]:
        sg_set.add(security_group["GroupId"])

    # Security groups used by classic ELBs
    elb_dict = all_elb.describe_load_balancers()
    for sg in elb_dict["LoadBalancerDescriptions"]:
        for elb_sg in sg["SecurityGroups"]:
            elb_set.add(elb_sg)

    # Security groups used by ALBs
    elb2_dict = all_alb.describe_load_balancers()
    for sg in elb2_dict["LoadBalancers"]:
        try:
            for alb_sg in sg["SecurityGroups"]:
                alb_set.add(alb_sg)
        except KeyError:
            pass

    # Security groups used by RDS
    rds_dict = all_rds.describe_db_instances()
    for sg in rds_dict["DBInstances"]:
        for rds_sg in sg["VpcSecurityGroups"]:
            rds_set.add(rds_sg["VpcSecurityGroupId"])

    # Security Groups in use by Network Interfaces
    for eni in all_eni["NetworkInterfaces"]:
        for sg in eni["Groups"]:
            eni_set.add(sg["GroupId"])

    # Security Groups in use by Lambda Function
    lambda_functions = all_lambda.list_functions()
    while True:
        if "NextMarker" in lambda_functions:
            nextMarker = lambda_functions["NextMarker"]
        else:
            nextMarker = ""
        for function in lambda_functions["Functions"]:
            # functionName = function["FunctionName"]
            functionVpcConfig = ""
            functionSecurityGroupIds = ""
            try:
                functionVpcConfig = function["VpcConfig"]
                functionSecurityGroupIds = functionVpcConfig["SecurityGroupIds"]
                for lambda_sg in functionSecurityGroupIds:
                    lambda_set.add(lambda_sg)
            except KeyError:
                continue
        if nextMarker == "":
            break
        else:
            lambda_functions = all_lambda.list_functions(Marker=nextMarker)

    idle_sg = (
        sg_set - instance_sg_set - elb_set - alb_set - rds_set - eni_set - lambda_set
    )
    print(idle_sg)


# Create the IAM groups
def iam_create_group():
    client = boto3.client("iam")
    if (
        os.environ["Env"] == "test"
        or os.environ["Env"] == "pilot"
        or os.environ["Env"] == "production"
    ):
        try:
            client.create_group(GroupName="gtt_restricted_access")
            client.create_group(GroupName="gtt_elevated_access")
            client.create_group(GroupName="gtt_administrators")
        except ClientError as error:
            if error.response["Error"]["Code"] == "EntityAlreadyExists":
                print("Group already exists...Use the same group")
            else:
                print(
                    "Unexpected error occured while creating group... exiting from here",
                    error,
                )
                return "Group could not be created", error


# Add policies and users to the group according to there Roles and Responsibilities
def add_users_to_group():
    resource = boto3.resource("iam")
    client = boto3.client("iam")
    response = client.list_groups()
    for group in response["Groups"]:
        if (
            os.environ["Env"] == "test"
            or os.environ["Env"] == "pilot"
            or os.environ["Env"] == "production"
        ):
            account_id = boto3.client("sts").get_caller_identity().get("Account")
            IAMReadOnlyAccess = "arn:aws:iam::aws:policy/IAMReadOnlyAccess"
            AmazonVPCReadOnlyAccess = "arn:aws:iam::aws:policy/AmazonVPCReadOnlyAccess"
            ResourceControlPipelineMgmtPolicy = (
                f"arn:aws:iam::{account_id}:policy/ResourceControlPipelineMgmtPolicy"
            )
            client.attach_group_policy(
                GroupName="gtt_elevated_access", PolicyArn=IAMReadOnlyAccess
            )
            client.attach_group_policy(
                GroupName="gtt_elevated_access", PolicyArn=AmazonVPCReadOnlyAccess
            )
            client.attach_group_policy(
                GroupName="gtt_elevated_access",
                PolicyArn=ResourceControlPipelineMgmtPolicy,
            )
            for user in resource.users.all():
                if (
                    user.user_name == "saravanan.rajagopal"
                    or user.user_name == "christian.kulus"
                    or user.user_name == "teigen.leonard"
                    or user.user_name == "allen.sharrer"
                    or user.user_name == "pragati.gupta"
                ):
                    print(user.user_name)
                    client.add_user_to_group(
                        GroupName="gtt_elevated_access", UserName=user.user_name
                    )
                else:
                    print("User is not in gtt_elevated_access group")

        if (
            os.environ["Env"] == "test"
            or os.environ["Env"] == "pilot"
            or os.environ["Env"] == "production"
        ):
            account_id = boto3.client("sts").get_caller_identity().get("Account")
            ResourceControlPipelineMgmtPolicy = (
                f"arn:aws:iam::{account_id}:policy/ResourceControlPipelineMgmtPolicy"
            )
            ReadOnlyAccessPolicy = (
                f"arn:aws:iam::{account_id}:policy/ReadOnlyAccessPolicy"
            )
            LimitedResourceAccessMgmtPolicy = (
                f"arn:aws:iam::{account_id}:policy/LimitedResourceAccessMgmtPolicy"
            )
            client.attach_group_policy(
                GroupName="gtt_restricted_access",
                PolicyArn=ResourceControlPipelineMgmtPolicy,
            )
            client.attach_group_policy(
                GroupName="gtt_restricted_access", PolicyArn=ReadOnlyAccessPolicy
            )
            client.attach_group_policy(
                GroupName="gtt_restricted_access",
                PolicyArn=LimitedResourceAccessMgmtPolicy,
            )
            for user in resource.users.all():
                if (
                    user.user_name != "jitendra.panchal"
                    and user.user_name != "nishant.jain"
                    and user.user_name != "saravanan.rajagopal"
                    and user.user_name != "christian.kulus"
                    and user.user_name != "teigen.leonard"
                    and user.user_name != "allen.sharrer"
                    and user.user_name != "pragati.gupta"
                ):
                    client.add_user_to_group(
                        GroupName="gtt_restricted_access", UserName=user.user_name
                    )
                else:
                    print("User is not in gtt_restricted_access group")

        if (
            os.environ["Env"] == "test"
            or os.environ["Env"] == "pilot"
            or os.environ["Env"] == "production"
        ):
            for user in resource.users.all():
                AdministratorAccess = "arn:aws:iam::aws:policy/AdministratorAccess"
                client.attach_group_policy(
                    GroupName="gtt_administrators", PolicyArn=AdministratorAccess
                )
                if (
                    user.user_name == "jitendra.panchal"
                    or user.user_name == "nishant.jain"
                ):
                    client.add_user_to_group(
                        GroupName="gtt_administrators", UserName=user.user_name
                    )
                else:
                    print("User is not in gtt_administrators group")


# Function Calls
iam_create_group()
add_users_to_group()
ebs_tag()
iam_mgmt()
lambda_mgmt()
time.sleep(2)
efs_tag()
dynamo_encryption_check()
dynamo_backup_status()
password_accesskey_check()
log_streams()
unused_elastic_ips()
unused_volumes()
unused_loadbalancers()
unused_old_snapshots()
unused_dynamodb_tables()
get_unused_amis(get_all_amis(), get_used_amis_by_instances())
unused_securitygroups()
