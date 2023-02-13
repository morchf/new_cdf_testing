#!/bin/bash

# Copy a Docker image from Docker Hub and push to ECR
# e.g ./copy-image.sh -n golang:1.19-alpine


show_help() {
  echo "Usage: copy-image [options...]"
  echo "  -i [aws_account_id]  12-digit account id, defaults to \`aws sts get-caller-identity --query Account\`"
  echo "  -r [region_name]     aws region name, defaults to \`aws configure get region\`"
  echo "  -n [image_name]      Image name, with optional tag"
}

while getopts "h?r:i:n:" opt; do
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
    n)
      image_name=$OPTARG
      ;;
  esac
done

[ -z $image_name ] && echo "Must pass in image name (-n)" && exit 1

region=${region:-$(aws configure get region)}
account_id=${account_id:-$(aws sts get-caller-identity --query Account --output text)}

[ -z $region ] && echo "Must pass in region or include in profile config file"
[ -z $account_id ] && echo "Must pass in account ID or include in profile config file"

ecr_url=${account_id}.dkr.ecr.${region}.amazonaws.com
repository=`echo $image_name | cut -d ':' -f1`

docker pull $image_name

docker tag $image_name "$ecr_url/$image_name"

# Create repository if it doesn't exist
aws ecr create-repository --repository-name $repository || true

# Must be authenticated
docker logout
aws ecr get-login-password \
  --region $region \
  | docker login --username AWS --password-stdin $ecr_url

docker push $ecr_url/$image_name
