
template.yml takes nine parameters.

Except for the GITREADTOKEN parameter and the s3 bucket do not change the default values of any other parameters.
Github token which has read authorization to git hub repo (smartcityplatform) to read the docker creation python file.

S3 bucket has to be created to move the efs data from ec2 to s3 and should be passed as parameter

The MacCode is default to CC:69:B0:08:FD:69 , if the different value to be created for the initial value, override the default parameters

API created from template.yml template are NOT SECURED(it's open to public)

(restorations and encryptions of dynamoDb and efs file system are not verified)

### template.yml MUST BE EXECUTED in us-east-1 REGION

### DO NOT CREATE MORE THEN 150 VPS REQUEST PER API. REQUESTING MORE WILL CAUSE DELAY IN THE RESPONE OF LAMBDA(>30 SECONDS)

### DO NOT IMPORT A CSV FILE WHICH HAS MORE THEN 150 INTERSECTION. DYNAMODB LIMITATION PER CELL

### ASSUMPTIONS:
*   The docker created in each ec2 servers will start from port 2000, and will go up to
 2250 port or more based on the deletion and recreation of the dockers
*   The api for creation of dockers can be called in the interval of 15 minutes ONLY.
*   Initial value of the macaddress to the globalmacVPS dynamo table is added at the time of deployment. Should be performed only once per account. **primaryKey** of the first object must be 1111
```json
{
"primaryKey": 11111,
"macCode": "224754297011234",
"VPS": "V764MH0000",
}
```
*   All files from codeCommitcopy folder should be copied to the GTTVPSDELPLOYMENT code repository in the aws code commit.
*   New agency information will be populated in the codebuilddeploy dynamoDB table, with the sunbentID, latest amazon image ID and list of security group.
``` json
{
    "customerName": "AGENCYNAME",
    "dockerImage": "123456789.dkr.ecr.us-east-1.amazonaws.com/smartcity",
    "serverProperties": {
        "securityGroup": ["sg-123456789"],
        "subnetID": "subnet-123456789"
    },
    "serverRegion": "us-east-1",
    "ImageId": "ami-0f22545d00916181b"
}
```
*   New agency related CMS credential should be stored in the secret manager of us-east-1 region
*   AMI-Id's for the vps host images are found in https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs-optimized_AMI.html
*   The base url is provided by the devops team to fetch the zipfile contianing all the certificates for the variable url in DockerDeployPythonScripts/dockercreate.py
*   All the docker logs will be created in us-east-1 region with prefix /vps/{customer name}/dockername with a retention policy of 90 days
* Add "baseUrl" in the codeBuildDeploy table in the dynamoDB with the column which has primary key "gtt" (applicable while writing the certificates to vps)
* github_read parameter has been created in the ssm parameter store with key: secret and value   : vps
* m5a.large and m5a.xlarge instaces should be AVAILABLE in the subenet that are being to assigned to VPS dockers host servers
* Incase of terminatation of existing ec2 servers for disaster recovery, make sure no new entry for that particular agency will be created in the dynamoDB

``` sh
sam package --region us-east-1 --template-file template.yml --s3-bucket production-gtt-raj --output-template-file deploy.yml

sam deploy --region us-east-1 --template-file deploy.yml --stack-name VPS-DEPLOYMENTS --capabilities CAPABILITY_NAMED_IAM --parameter-overrides S3BUCKETNAME=efsdatabackup-gtt --no-fail-on-empty-changeset
```

#### Tests
* A VPS pipeline is currently unavailable, so unit tests for VpsCreate.py and VpsUpdate.py need to be ran locally
* For VpsCreate.py, run 'pytest test_App.py' under the folder /VpsCreate/tests
* For VpsUpdate.py, run 'pytest test_App.py' under the folder /VpsUpdate/tests
