#!/bin/bash

#
# Create ~/.aws/credentials file from temporary CodeBuild credentials
#

# Pull the temporary credentials
CODE_BUILD_CREDENTIALS=$(curl 169.254.170.2$AWS_CONTAINER_CREDENTIALS_RELATIVE_URI)

AWS_ACCESS_KEY_ID=$(echo "${CODE_BUILD_CREDENTIALS}" | jq -r '.AccessKeyId')
AWS_SECRET_ACCESS_KEY=$(echo "${CODE_BUILD_CREDENTIALS}" | jq -r '.SecretAccessKey')
AWS_SESSION_TOKEN=$(echo "${CODE_BUILD_CREDENTIALS}" | jq -r '.Token')

# Create read-only credentials file
AWS_CREDENTIALS_FILE=~/.aws/credentials

mkdir ~/.aws
touch $AWS_CREDENTIALS_FILE
chmod 600 $AWS_CREDENTIALS_FILE

# Populate credentials
echo "[default]" > $AWS_CREDENTIALS_FILE
echo "aws_access_key_id=${AWS_ACCESS_KEY_ID}" >> $AWS_CREDENTIALS_FILE
echo "aws_secret_access_key=${AWS_SECRET_ACCESS_KEY}" >> $AWS_CREDENTIALS_FILE
echo "aws_session_token=${AWS_SESSION_TOKEN}" >> $AWS_CREDENTIALS_FILE
