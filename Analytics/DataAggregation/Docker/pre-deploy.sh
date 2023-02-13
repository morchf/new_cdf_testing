#! /bin/sh
# This file is to handle the build/deploy steps needed before using cloudformation
script_dir=$(dirname "$0")

show_help() {
  echo "-i [aws_account_id]  12-digit account id, defaults to \`aws sts get-caller-identity --query Account\`"
  echo "-r [region_name]     aws region name, defaults to \`aws configure get region\`"
  echo "-d                   delete stack and all resources"
}

while getopts "h?r:i:d" opt; do
  case "$opt" in
    h|\?)
      show_help
      exit 0
      ;;
    r)
      region=$OPTARG
      ;;
    i)
      account_id=$OPTARG
      ;;
    d)
      should_delete_resources=true
  esac
done
region=${region:-$(aws configure get region)}
account_id=${account_id:-$(aws sts get-caller-identity --query Account --output text)}

ecr_url=${account_id}.dkr.ecr.${region}.amazonaws.com
repository="gtt/data-aggregation"
tag="latest"

if [ $should_delete_resources ]; then
  # ecr image
  aws ecr batch-delete-image \
    --repository-name $repository \
    --image-ids imageTag=$tag
  echo "Deleted ${ecr_url}/${repository}:${tag}"
  exit 0
fi

# login to ecr registry
aws ecr get-login-password --region $region \
  | docker login --username AWS --password-stdin $ecr_url

# create ecr repo if it doesn't exist
aws ecr describe-repositories --repository-names $repository --no-cli-pager \
  || aws ecr create-repository --repository-name $repository

# build docker images
docker build -f ${script_dir}/Dockerfile -t ${ecr_url}/${repository}:${tag} ${script_dir}/..

# push images to ecr
docker push ${ecr_url}/${repository}:${tag}
echo "Built and pushed ${ecr_url}/${repository}:${tag}"

echo "To deploy, run:"
echo "  aws cloudformation create-stack \\"
echo "    --stack-name data-aggregation-test \\"
echo "    --template-body file://Deployment/DataAggregationPipeline/DataAggregationDeployment.yml \\"
echo "    --capabilities CAPABILITY_AUTO_EXPAND CAPABILITY_NAMED_IAM \\"
echo "    --parameters \\"
echo "      ParameterKey=Env,ParameterValue=develop \\"
echo "      ParameterKey=DataAggregationImageTag,ParameterValue=${tag}"
