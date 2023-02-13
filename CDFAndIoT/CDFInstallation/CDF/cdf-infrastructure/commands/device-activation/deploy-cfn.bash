#!/bin/bash
set -e
if [[ "$DEBUG" == "true" ]]; then
    set -x
fi
source ../../../cdf-core/infrastructure/common-deploy-functions.bash


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
    Deploys Demo specific resources.

MANDATORY ARGUMENTS:
    -e (string)   Name of environment.

OPTIONAL ARGUMENTS
    -C (string)   Name of commands stack.  Defaults to cdf-commands-${ENVIRONMENT}.
    -R (string)   AWS region.
    -P (string)   AWS profile.
    
EOF
}

while getopts ":e:C:R:P:" opt; do
  case $opt in

    e  ) export ENVIRONMENT=$OPTARG;;

    C  ) export COMMANDS_STACK_NAME=$OPTARG;;

    R  ) export AWS_REGION=$OPTARG;;
    P  ) export AWS_PROFILE=$OPTARG;;

    \? ) echo "Unknown option: -$OPTARG" >&2; help_message; exit 1;;
    :  ) echo "Missing option argument for -$OPTARG" >&2; help_message; exit 1;;
    *  ) echo "Unimplemented option: -$OPTARG" >&2; help_message; exit 1;;
  esac
done

incorrect_args=0
incorrect_args=$((incorrect_args+$(verifyMandatoryArgument ENVIRONMENT e $ENVIRONMENT)))

if [[ "$incorrect_args" -gt 0 ]]; then
    help_message; exit 1;
fi

AWS_ARGS=$(buildAwsArgs "$AWS_REGION" "$AWS_PROFILE" )

COMMANDS_STACK_NAME="$(defaultIfNotSet 'COMMANDS_STACK_NAME' z ${COMMANDS_STACK_NAME} cdf-commands-${ENVIRONMENT})"
STACK_NAME=cdf-device-activation-${ENVIRONMENT}

echo "
Running with:
  ENVIRONMENT:          $ENVIRONMENT
  AWS_REGION:           $AWS_PROFILE
  COMMANDS_STACK_NAME: $COMMANDS_STACK_NAME
"


logTitle 'Deploying the Device Activation CloudFormation template'

aws cloudformation deploy \
  --template-file cfn-device-activation-output.yml \
  --stack-name $STACK_NAME \
  --parameter-overrides \
      Environment=$ENVIRONMENT \
      CommandsStackName=$COMMANDS_STACK_NAME \
  --capabilities CAPABILITY_NAMED_IAM \
  --no-fail-on-empty-changeset \
  $AWS_ARGS


logTitle 'Device activation deployment complete!'
