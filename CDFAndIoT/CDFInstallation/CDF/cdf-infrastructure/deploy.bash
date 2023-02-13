#!/bin/bash

set -e
source ../cdf-core/infrastructure/common-deploy-functions.bash


function help_message {
    cat << EOF

NAME:
    deploy.bash    

DESCRIPTION:
    Deploys the CDF platform.

MANDATORY ARGUMENTS:
====================

    -e (string)   Name of environment.
    -u (string)   The name of the S3 bucket where devices shall be allowed to upload content to.
    -p (string)   The name of the key pair to use to deploy the Bastion EC2 host.
    -i (string)   The remote access CIDR to configure Bastion SSH access (e.g. 1.2.3.4/32).

    -y (string)   S3 uri base directory where Cloudformation template snippets are stored.
    -z (string)   Name of API Gateway cloudformation template snippet. If none provided, all API Gateway instances are configured without authentication.


OPTIONAL ARGUMENTS

    COMMON OPTIONS::
    ----------------
    -E (string)   Alternate existing cdf-core environment to use.
    -b (string)   The name of the S3 bucket to deploy CloudFormation templates into.  If not provided, a new bucket named 'cdf-cfn-artifacts-$AWS_ACCOUNT_ID-$AWS_REGION' is created.
    -k (string)   The KMS Key ID to use for CDF. If not provided, a new KMS key will be created.

    COMMON AUTH OPTIONS::
    -------------------------------
    -a (string)   API Gateway authorization type. Must be from the following list (default is None):
                  - None
                  - Private
                  - Cognito
                  - LambdaRequest
                  - LambdaToken
                  - ApiKey
                  - IAM

    COMMON PRIVATE API AUTH OPTIONS:
    ------------------------------
    -i (string)   ID of VPC execute-api endpoint

    COMMON COGNITO AUTH OPTIONS:
    --------------------------
    -c (string)   Cognito user pool arn

    COMMON LAMBDA REQUEST/TOKEN AUTH OPTIONS:
    ---------------------------------------------
    -A (string)   Lambda authorizer function arn.

    COMPILING OPTIONS:
    ------------------
    -B (flag)     Bypass bundling customer specific modules, such as the facade, as well as cdf clients.
    -C (flag)     Bypass bundling the cdf-core modules.  If deploying from a prebuilt tarfile rather than source code, setting this flag will speed up the deploy.

    MISC OPTIONS:
    -------------
    -D (flag)     Enable debug mode.

    AWS OPTIONS:
    ------------
    -R (string)   AWS region.
    -P (string)   AWS profile.

DEPENDENCIES REQUIRED:

    - aws-cli
    - jq
    - zip
    
EOF
}


##########################################################
######  parse and validate the provided arguments   ######
##########################################################
while getopts ":e:E:u:p:i:a:y:z:c:A:b:k:BCDR:P:" opt; do
  case $opt in
    e  ) export ENVIRONMENT=$OPTARG;;
    E  ) export CDF_CORE_ENVIRONMENT=$OPTARG;;
    u  ) export DEVICE_UPLOAD_BUCKET=$OPTARG;;
    p  ) export KEY_PAIR_NAME=$OPTARG;;
    i  ) export BASTION_REMOTE_ACCESS_CIDR=$OPTARG;;

    b  ) export DEPLOY_ARTIFACTS_STORE_BUCKET=$OPTARG;;
    k  ) export KMS_KEY_ID=$OPTARG;;

    a  ) export API_GATEWAY_AUTH=$OPTARG;;
    y  ) export TEMPLATE_SNIPPET_S3_URI_BASE=$OPTARG;;
    z  ) export API_GATEWAY_DEFINITION_TEMPLATE=$OPTARG;;
    c  ) export COGNTIO_USER_POOL_ARN=$OPTARG;;
    A  ) export AUTHORIZER_FUNCTION_ARN=$OPTARG;;

    B  ) export BYPASS_BUNDLE_CUSTOMER=true;;
    C  ) export BYPASS_BUNDLE_CDF=true;;
    D  ) export DEBUG=true;;

    R  ) export AWS_REGION=$OPTARG;;
    P  ) export AWS_PROFILE=$OPTARG;;

    \? ) echo "Unknown option: -$OPTARG" >&2; help_message; exit 1;;
    :  ) echo "Missing option argument for -$OPTARG" >&2; help_message; exit 1;;
    *  ) echo "Unimplemented option: -$OPTARG" >&2; help_message; exit 1;;
  esac
done

if [[ "$DEBUG" == "true" ]]; then
    set -x
fi

incorrect_args=0

incorrect_args=$((incorrect_args+$(verifyMandatoryArgument ENVIRONMENT e ${ENVIRONMENT})))

API_GATEWAY_AUTH="$(defaultIfNotSet 'API_GATEWAY_AUTH' a ${API_GATEWAY_AUTH} 'None')"
incorrect_args=$((incorrect_args+$(verifyApiGatewayAuthType ${API_GATEWAY_AUTH})))
if [[ "$API_GATEWAY_AUTH" = "Cognito" ]]; then
    incorrect_args=$((incorrect_args+$(verifyMandatoryArgument COGNTIO_USER_POOL_ARN C ${COGNTIO_USER_POOL_ARN})))
fi
if [[ "$API_GATEWAY_AUTH" = "LambdaRequest" || "$API_GATEWAY_AUTH" = "LambdaToken" ]]; then
    incorrect_args=$((incorrect_args+$(verifyMandatoryArgument AUTHORIZER_FUNCTION_ARN A ${AUTHORIZER_FUNCTION_ARN})))
fi

incorrect_args=$((incorrect_args+$(verifyMandatoryArgument TEMPLATE_SNIPPET_S3_URI_BASE y "$TEMPLATE_SNIPPET_S3_URI_BASE")))

incorrect_args=$((incorrect_args+$(verifyMandatoryArgument DEVICE_UPLOAD_BUCKET u ${DEVICE_UPLOAD_BUCKET})))
incorrect_args=$((incorrect_args+$(verifyMandatoryArgument KEY_PAIR_NAME p ${KEY_PAIR_NAME})))
incorrect_args=$((incorrect_args+$(verifyMandatoryArgument BASTION_REMOTE_ACCESS_CIDR i ${BASTION_REMOTE_ACCESS_CIDR})))

API_GATEWAY_DEFINITION_TEMPLATE="$(defaultIfNotSet 'API_GATEWAY_DEFINITION_TEMPLATE' z ${API_GATEWAY_DEFINITION_TEMPLATE} 'cfn-apiGateway-noAuth.yaml')"
CDF_CORE_ENVIRONMENT="$(defaultIfNotSet 'CDF_CORE_ENVIRONMENT' E ${CDF_CORE_ENVIRONMENT} ${ENVIRONMENT})"

if [[ "$incorrect_args" -gt 0 ]]; then
    help_message; exit 1;
fi

if [[ -z "$KMS_KEY_ID" ]]; then
    KMS_OPTION=""
    KMS_PRINT="not provided - a key will be created"
else
    KMS_OPTION="-k $KMS_KEY_ID "
    KMS_PRINT=${KMS_KEY_ID}
fi

AWS_ARGS=$(buildAwsArgs "$AWS_REGION" "$AWS_PROFILE" )
AWS_SCRIPT_ARGS=$(buildAwsScriptArgs "$AWS_REGION" "$AWS_PROFILE" )


if [[ -z "$AWS_REGION" ]]; then
    AWS_REGION=$(getAwsRegion $AWG_ARGS)
fi

AWS_ACCOUNT_ID=$(getAwsAccountId $AWG_ARGS)

##########################################################
######  confirm whether to proceed or not           ######
##########################################################

config_message="
**********************************************************
*****   Connected Device Framework                  ******
**********************************************************

The Connected Device Framework (CDF) will install using the following configuration:

    -e (ENVIRONMENT)                    : $ENVIRONMENT
    -E (CDF_CORE_ENVIRONMENT)           : $CDF_CORE_ENVIRONMENT

    -y (TEMPLATE_SNIPPET_S3_URI_BASE)    : $TEMPLATE_SNIPPET_S3_URI_BASE
    -z (API_GATEWAY_DEFINITION_TEMPLATE) : $API_GATEWAY_DEFINITION_TEMPLATE

    -a (API_GATEWAY_AUTH)               : $API_GATEWAY_AUTH
    -C (COGNTIO_USER_POOL_ARN)          : $COGNTIO_USER_POOL_ARN
    -A (AUTHORIZER_FUNCTION_ARN)        : $AUTHORIZER_FUNCTION_ARN

    -b (DEPLOY_ARTIFACTS_STORE_BUCKET)  : $DEPLOY_ARTIFACTS_STORE_BUCKET
    -u (DEVICE_UPLOAD_BUCKET)           : $DEVICE_UPLOAD_BUCKET
    -k (KMS_KEY_ID)                     : $KMS_PRINT
    -p (KEY_PAIR_NAME)                  : $KEY_PAIR_NAME
    -i (BASTION_REMOTE_ACCESS_CIDR)     : $BASTION_REMOTE_ACCESS_CIDR
    -R (AWS_REGION)                     : $AWS_REGION
    -P (AWS_PROFILE)                    : $AWS_PROFILE
        AWS_ACCOUNT_ID                  : $AWS_ACCOUNT_ID
    -B (BYPASS_BUNDLE_CUSTOMER)         : $BYPASS_BUNDLE_CUSTOMER"

if [[ -z "$BYPASS_BUNDLE_CUSTOMER" ]]; then
    config_message+='not provided, therefore each TypeScript customer project will be bundled
'
fi
config_message+="
    -C (BYPASS_BUNDLE_CDF)              : $BYPASS_BUNDLE_CDF"
if [[ -z "$BYPASS_BUNDLE_CDF" ]]; then
    config_message+='not provided, therefore each TypeScript CDF project will be bundled
'
fi

asksure "$config_message"


export CUSTOMER_SPECIAL=true

######################################################################
######  check that we have the required configuration/modules in place
######################################################################

config_dir=$(pwd)
root_dir=$(dirname $config_dir)

cdf_core_modules="$root_dir/cdf-core"
verifyMandatoryDirectory "$cdf_core_modules"

if [[ -z "$BYPASS_BUNDLE_CUSTOMER" ]]; then
    cdf_client_modules="$root_dir/cdf-clients"
fi

if [[ -z "$CUSTOMER_SPECIAL" ]]; then
    verifyMandatoryDirectory "$cdf_client_modules"
fi

if [[ -z "$BYPASS_BUNDLE_CUSTOMER" ]]; then
    facade_config="$config_dir/facade/$ENVIRONMENT-config.json"
fi
if [[ -z "$CUSTOMER_SPECIAL" ]]; then
    verifyMandatoryFile "$facade_config"
fi


######################################################################
######  stack names                                             ######
######################################################################

ASSETLIBRARY_STACK_NAME=cdf-assetlibrary-${ENVIRONMENT}
if [[ -z "$BYPASS_BUNDLE_CUSTOMER" ]]; then
    FACADE_STACK_NAME=cdf-demofacade-${ENVIRONMENT}
fi

if [[ -z "$CUSTOMER_SPECIAL" ]]; then
    OPENSSL_LAYER_STACK_NAME=cdf-openssl-${ENVIRONMENT}
fi


######################################################################
######  build clients / facade if we need to                    ######
######################################################################

if [[ -z "$BYPASS_BUNDLE_CUSTOMER" ]]; then
    logTitle 'Bundling dependencies'

    # we first have to build cdf-clients with devDependencies
    apps_to_build=(cdf-clients)
    for app in "${apps_to_build[@]}"; do
        echo Building ${app} ...
        cd "$root_dir/$app"
        pnpm run build:libraries
    done

    # we can now go ahead and build the facade
    apps_to_bundle=(cdf-facade-demo)
    for app in "${apps_to_bundle[@]}"; do
        echo Bundling ${app} ...
        cd "$root_dir/$app"
        pnpm run bundle:prepare
    done

    # before bundling we need to remove cdf-clients devDependencies
    apps_to_build=(cdf-clients)
    for app in "${apps_to_build[@]}"; do
        echo Building ${app} ...
        cd "$root_dir/$app"
        pnpm run bundle:libraries
    done

    # finally, we can bundle the facade excluding devDependencies
    apps_to_bundle=(cdf-facade-demo)
    for app in "${apps_to_bundle[@]}"; do
        echo Bundling ${app} ...
        cd "$root_dir/$app"
        pnpm run bundle
    done

fi

######################################################################
######  if your deployment requires any auth related            ######
######  resources deploying to lock down the core services,     ######
######  such as Cognito configuring, or a lambda authorizer     ######
######  deploying, do that here before deploying the core       ######
######  services.                                               ######
######################################################################

## TODO:  wire up any cdf-core authorizers here.  The following commented
## out section if an example of a lambda authorizer that verifies jwt tokens:

# logTitle 'Deploying cdf-core auth-jwt lambda authorizer'
# cd "$root_dir/packages/services/auth-jwt"
# auth_jwt_config=$CONFIG_LOCATION/auth-jwt/$CONFIG_ENVIRONMENT-config.json
# verifyMandatoryFile "$facade_config"
# infrastructure/package-cfn.bash -b "$DEPLOY_ARTIFACTS_STORE_BUCKET" ${AWS_SCRIPT_ARGS}
# infrastructure/deploy-cfn.bash -e "$ENVIRONMENT" -c "$auth_jwt_config" -o ${OPENSSL_LAYER_STACK_NAME} ${AWS_SCRIPT_ARGS}


######################################################################
######  deploy core services.  only services where an env        #####
######  config file exists will be deployed.                     #####
######################################################################

logTitle 'Deploying core CDF services'
cd "$cdf_core_modules"

bypass_core_bundle_flag=
if [[ -n "$BYPASS_BUNDLE_CDF" ]]; then
    bypass_core_bundle_flag="-B"
fi

cognito_auth_arg=
if [[ "$API_GATEWAY_AUTH" = "Cognito" ]]; then
    cognito_auth_arg="-C ${COGNTIO_USER_POOL_ARN}"
fi

lambda_invoker_auth_arg=
if [[ "$API_GATEWAY_AUTH" = "LambdaRequest" || "$API_GATEWAY_AUTH" = "LambdaToken" ]]; then
    lambda_invoker_auth_arg="-A ${AUTHORIZER_FUNCTION_ARN}"
fi

infrastructure/deploy-core.bash \
  -e ${CDF_CORE_ENVIRONMENT} -c "$config_dir" \
  -y "$TEMPLATE_SNIPPET_S3_URI_BASE" -z "$API_GATEWAY_DEFINITION_TEMPLATE" \
  -a "$API_GATEWAY_AUTH" ${cognito_auth_arg} ${lambda_invoker_auth_arg} \
  -p ${KEY_PAIR_NAME} \
  -i ${BASTION_REMOTE_ACCESS_CIDR} \
  -b ${DEPLOY_ARTIFACTS_STORE_BUCKET} \
  ${KMS_OPTION} \
  -Y ${bypass_core_bundle_flag} \
  ${AWS_SCRIPT_ARGS}

#   -x 1 -s \           # <<< this is asset library autoprovisoning.

######################################################################
######  if your deployment requires any auth related            ######
######  resources deploying to lock down the facade,            ######
#####  if your deployment requires any auth related            ######
######  resources deploying to lock down the facade,            ######
######  such as Cognito configuring, or a lambda authorizer     ######
######  deploying, do that here before deploying the core       ######
######  services.                                               ######
######################################################################

## Possible todo:  wire up any cdf-facade authorizer here...

if [[ -z "$CUSTOMER_SPECIAL" ]]; then

    logTitle 'Deploying facade'

    cd "$root_dir/cdf-facade-demo"
    infrastructure/package-cfn.bash -b ${DEPLOY_ARTIFACTS_STORE_BUCKET} ${AWS_SCRIPT_ARGS}
    infrastructure/deploy-cfn.bash -e ${ENVIRONMENT} -c "$facade_config" -S ${FACADE_STACK_NAME}  ${AWS_SCRIPT_ARGS}


    logTitle 'Deploying Demo Specific Resources'

    cd "$config_dir/commands/device-activation"
    ./package-cfn.bash -b ${DEPLOY_ARTIFACTS_STORE_BUCKET} ${AWS_SCRIPT_ARGS}
    ./deploy-cfn.bash -e ${ENVIRONMENT} ${AWS_SCRIPT_ARGS}

fi

logTitle 'Populating Demo Specific Asset Library data'

#cd "$config_dir/assetlibrary"
#python3 assetlib_seed.py

if [[ -z "$CUSTOMER_SPECIAL" ]]; then
    logTitle 'Populating demo specific EventProcessor data for push notification'

    cd "$config_dir/events-processor"
    ./events-processor-seed.bash -e $ENVIRONMENT ${AWS_SCRIPT_ARGS}
fi

if [ -z "$BYPASS_BUNDLE_CUSTOMER" ]; then
    logTitle 'Resetting application dependencies for local development'
    apps_to_install=(cdf-facade-demo)
    for app in ${apps_to_install[@]}; do
        cd "$root_dir/$app"
        pnpm run reset
    done
fi


cd $config_dir

logTitle 'Complete!'

