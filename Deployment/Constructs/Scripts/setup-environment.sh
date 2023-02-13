#!/bin/bash
# Setup a CodeBuild environment with some default configuration

aws configure list

echo "Setting environment variables"

# Useful environment variables
export PWD=`pwd`
export ENVIRONMENT=${ENVIRONMENT:-$Env}

export ACCOUNT_ID=$(aws sts get-caller-identity --output text --query 'Account' $AWS_ARGS)
export AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:-$ACCOUNT_ID}"

# Language/library versions
export PYTHON3_VERSION=$(python3 --version | awk '{print $2}')
export NODE_VERSION=${NODE_VERSION:-14.18.3}
export CDK_VERSION=${CDK_VERSION:-2.41.0}

echo "Setting up Python and virtual environment (${PYTHON3_VERSION}) "
python3 -m venv .venv
source .venv/bin/activate
python3 --version

echo "Setting up Node.js ($NODE_VERSION)"
n $NODE_VERSION
node --version
npm update
npm --version

echo "Setting up CDK ($CDK_VERSION)"
npm uninstall -g aws-cdk
npm install -g aws-cdk@$CDK_VERSION
cdk --version
