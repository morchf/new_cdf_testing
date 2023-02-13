#!/bin/bash
# Parse a CFN Stack output

show_help() {
  echo "Usage: cfn-output <stack_name> <output_key>"
  echo "  <stack_name> CloudFormation stack name"
  echo "  <output_key> Parse output for certain key"
}

stack_name=$1
output_key=$2

([ -z "$stack_name" ] || [ -z "$output_key" ]) && show_help && exit 1;

OUTPUT=$(
  aws cloudformation \
    describe-stacks \
      --stack-name $stack_name \
  | jq '.Stacks[0].Outputs | .[]' \
  | jq "select(.OutputKey | test(\"${output_key}\"))" \
  | jq -r '.OutputValue' \
)

echo "${OUTPUT}"
