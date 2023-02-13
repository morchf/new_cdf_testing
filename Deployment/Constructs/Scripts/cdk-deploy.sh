#!/bin/bash

# Deploy CDK app
# e.g ./cdk-deploy.sh -a infra/stacks/redfield/redfield_stack.py


show_help() {
  echo "Usage: build-and-push-image [options...]"
  echo "  -a [app]             CDK app file. e.g. \`stack.py\`"
  echo "  -i [aws_account_id]  12-digit account id, defaults to \`aws sts get-caller-identity --query Account\`"
  echo "  -r [region_name]     aws region name, defaults to \`aws configure get region\`"
  echo "  -o [output_file]          Stack outputs file. Defaults to 'outputs.json'"
}

while getopts "h?r:i:a:o:" opt; do
  case "$opt" in
    h|\?)
      show_help
      exit 0
      ;;
    a)
      app=$OPTARG
      ;;
    r)
      region=$OPTARG
      ;;
    i)
      account_id=$OPTARG
      ;;
    o)
      output_file=$OPTARG
      ;;
  esac
done

region=${region:-$(aws configure get region)}
region=${region:-"$AWS_DEFAULT_REGION"}
account_id=${account_id:-$(aws sts get-caller-identity --query Account --output text)}
output_file=${output_file:-outputs.json}

cdk bootstrap \
    aws://$account_id/$region \
    --app "python3 $app" \
  && cdk deploy \
    --app "python3 $app" \
    --require-approval never \
    --outputs-file $output_file
