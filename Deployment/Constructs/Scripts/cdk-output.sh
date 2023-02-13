#!/bin/bash
# Parse a CF template output

show_help() {
  echo "Usage: cdk-output <input_file> <output_key>"
  echo "  <input_file> CloudFormation outputs (cdk deploy --outputs-file outputs.json)"
  echo "  <output_key> Parse output for certain key"
}

input_file=$1
output_key=$2

([ -z "$input_file" ] || [ -z "$output_key" ]) && show_help && exit 1;

OUTPUT=$(
  cat $input_file \
  | jq 'to_entries[0].value' \
  | jq "to_entries | .[] | select(.key | test(\"$output_key\"))" \
  | jq -r '.value' \
  | sed 's=\\\\\\==g'  \
)

echo "${OUTPUT}"
