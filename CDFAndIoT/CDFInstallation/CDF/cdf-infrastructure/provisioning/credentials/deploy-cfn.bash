#!/bin/bash
set -e

#-------------------------------------------------------------------------------
# Copyright (c) 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# 
# This source code is subject to the terms found in the AWS Enterprise Customer Agreement.
#-------------------------------------------------------------------------------

function help_message {
    cat << EOF

NAME
    deploy-cfn.bash    

DESCRIPTION
    Deploys credentials specific resources.

MANDATORY ARGUMENTS:
    -e (string)   Name of environment.
    -b (string)   Name of bucket to apply to S3 polices.

OPTIONAL ARGUMENTS
    -R (string)   AWS region.
    -P (string)   AWS profile.
    
EOF
}

while getopts ":e:b:R:P:" opt; do
  case $opt in

    e  ) export ENVIRONMENT=$OPTARG;;
    b  ) export BUCKET=$OPTARG;;

    R  ) export AWS_REGION=$OPTARG;;
    P  ) export AWS_PROFILE=$OPTARG;;

    \? ) echo "Unknown option: -$OPTARG" >&2; help_message; exit 1;;
    :  ) echo "Missing option argument for -$OPTARG" >&2; help_message; exit 1;;
    *  ) echo "Unimplemented option: -$OPTARG" >&2; help_message; exit 1;;
  esac
done


if [ -z "$ENVIRONMENT" ]; then
	echo -e ENVIRONMENT is required; help_message; exit 1;
fi

if [ -z "$BUCKET" ]; then
	echo -b BUCKET is required; help_message; exit 1;
fi

AWS_ARGS=
if [ -n "$AWS_REGION" ]; then
	AWS_ARGS="--region $AWS_REGION "
fi
if [ -n "$AWS_PROFILE" ]; then
	AWS_ARGS="$AWS_ARGS--profile $AWS_PROFILE"
fi

CREDENTIALS_STACK_NAME=cdf-credentials-${ENVIRONMENT}

echo "
Running with:
  ENVIRONMENT:        $ENVIRONMENT
  BUCKET:             $BUCKET
  AWS_REGION:         $AWS_PROFILE
"


echo '
**********************************************************
  Deploying the CloudFormation template 
**********************************************************
'

aws cloudformation deploy \
  --template-file cfn-credentials-output.yml \
  --stack-name $CREDENTIALS_STACK_NAME \
  --parameter-overrides \
      Environment=$ENVIRONMENT \
      BucketName=$BUCKET \
  --capabilities CAPABILITY_NAMED_IAM \
  --no-fail-on-empty-changeset \
  $AWS_ARGS


echo '
**********************************************************
  Identifying name of new role
**********************************************************
'
stack_exports=$(aws cloudformation list-exports $AWS_ARGS)

s3_device_access_role_arn_export="$CREDENTIALS_STACK_NAME-S3DeviceAccessRoleArn"
s3_device_access_role_arn=$(echo $stack_exports \
    | jq -r --arg s3_device_access_role_arn_export "$s3_device_access_role_arn_export" \
    '.Exports[] | select(.Name==$s3_device_access_role_arn_export) | .Value')


echo '
**********************************************************
  Creating role alias
**********************************************************
'     
ROLE_ALIAS_NAME=s3-device-access-role-alias

existing_role_alias=$(aws iot describe-role-alias \
    --role-alias $ROLE_ALIAS_NAME $AWS_ARGS \
        | jq -r '.roleAliasDescription.roleAlias' \
        || true)

if [ "$ROLE_ALIAS_NAME" = "$existing_role_alias" ]; then
  aws iot update-role-alias \
  --role-alias $ROLE_ALIAS_NAME \
  --role-arn $s3_device_access_role_arn \
  --credential-duration-seconds 3600 \
    $AWS_ARGS &
else
  aws iot create-role-alias \
  --role-alias s3-device-access-role-alias \
  --role-arn $s3_device_access_role_arn \
  --credential-duration-seconds 3600 \
    $AWS_ARGS &
fi



echo '
**********************************************************
  Done!
**********************************************************
'