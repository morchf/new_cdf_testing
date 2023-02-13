#!/bin/bash

# Build a base Docker image and push to ECR
# e.g ./build-and-push-image.sh -d amazoncorretto/11-python3.10


show_help() {
  echo "Usage: build-and-push-image [options...]"
  echo "  -i [aws_account_id]  12-digit account id, defaults to \`aws sts get-caller-identity --query Account\`"
  echo "  -r [region_name]     aws region name, defaults to \`aws configure get region\`"
  echo "  -d [dir]             Base image directory. Used to build Dockerfile and tag image"
}

while getopts "h?r:i:d:" opt; do
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
      dir=$OPTARG
      ;;
  esac
done

[ -z $dir ] && echo "Must pass in directory (-d)" && exit 1

region=${region:-$(aws configure get region)}
account_id=${account_id:-$(aws sts get-caller-identity --query Account --output text)}

[ -z $region ] && echo "Must pass in region or include in profile config file"
[ -z $account_id ] && echo "Must pass in account ID or include in profile config file"

# Build a Docker image assuming directory format is 'repository/tag'
ecr_url=${account_id}.dkr.ecr.${region}.amazonaws.com

# Must be authenticated
docker logout
aws ecr get-login-password \
  --region $region \
  | docker login --username AWS --password-stdin $ecr_url

repository=`echo $dir | cut -d '/' -f1`
tag=("${dir//// }")
tag=($tag)
tag=${tag[1]:-latest}

docker build \
  --build-arg BASE_CONTAINER_REPO=$ecr_url \
    -f "$dir/Dockerfile" \
    -t "$ecr_url/$repository:$tag" \
    .

# Create repository if it doesn't exist
aws ecr create-repository --repository-name $repository || true

docker push $ecr_url/$repository:$tag
