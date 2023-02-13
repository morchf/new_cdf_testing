#!/bin/bash
# Deploy an API Gateway stage

show_help() {
  echo "Usage: deploy-stage <api_gateway_id> <stage_name>"
  echo "  <api_gateway_id> Auto-generated API Gateway ID"
  echo "  <stage_name> Stage name"
}

api_id=$1
stage_name=$2

aws apigateway \
    create-deployment \
    --rest-api-id $api_id 
    --api_id-name $stage_name
