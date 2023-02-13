#!/bin/bash

set -e
source ../../cdf-core/packages/services/assetlibrary/infrastructure/common-seeding-functions.bash
source ../../cdf-core/infrastructure/common-deploy-functions.bash

function help_message {
    cat << EOF

NAME:
    assetlibrary_seed.bash

DESCRIPTION:
    Seeds an asset library database.

MANDATORY ARGUMENTS:
====================

    -e (string)   Name of environment.

OPTIONAL ARGUMENTS:
===================

    -D (flag)     Enable debug mode.
    -R (string)   AWS region.
    -P (string)   AWS profile.

DEPENDENCIES REQUIRED:

    - aws-cli
    - jq

EOF
}


##########################################################
######  parse and validate the provided arguments   ######
##########################################################
while getopts ":e:DR:P:" opt; do
  case $opt in
    e  ) export ENVIRONMENT=$OPTARG;;
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

if [[ "$incorrect_args" -gt 0 ]]; then
    help_message; exit 1;
fi

export AWS_ARGS=$(buildAwsArgs "$AWS_REGION" "$AWS_PROFILE" )

if [[ -z "$AWS_REGION" ]]; then
    export AWS_REGION=$(getAwsRegion $AWG_ARGS)
fi


assetlibrary_stack_name=cdf-assetlibrary-${ENVIRONMENT}

stack_exports=$(aws cloudformation list-exports $AWS_ARGS)
function_name_export="$assetlibrary_stack_name-restApiFunctionName"
export function_name=$(echo ${stack_exports} \
  | jq -r --arg function_name_export "$function_name_export" \
  '.Exports[] | select(.Name==$function_name_export) | .Value')


############################################################################
####   Add your custom Asset Library objects to create here...
############################################################################

create_or_update_type group location
create_or_update_type group supplier
create_or_update_type group customer
create_or_update_type group vehicle
create_or_update_type group engine

create_or_update_type device edge

create_or_update_provisioning_template demoDeviceSupplierProvisioningTemplate
create_or_update_bulkgroup_data %2Fsupplier%2Fdemodevicesupplier demoGroups

