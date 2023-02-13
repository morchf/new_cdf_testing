#!/bin/bash

# 2100
aggregate_rt_radio_messages \
  --device-model                2100 \
  --device-operational-mode     EVP \
  --aws-region                  ${AWS_REGION} \
  --cdf-url                     ${CDF_URL} \
  --incoming-bucket-name        ${INCOMING_BUCKET_NAME} \
  --outgoing-bucket-name        ${OUTGOING_BUCKET_NAME} \
  --cloudwatch-log-group        ${CLOUDWATCH_LOG_GROUP} \
  --incoming-s3-path            2100-EVP \
  --cloudwatch-log-stream-name  2100-logs

# 2101
aggregate_rt_radio_messages \
  --device-model                2101 \
  --device-operational-mode     TSP \
  --aws-region                  ${AWS_REGION} \
  --cdf-url                     ${CDF_URL} \
  --incoming-bucket-name        ${INCOMING_BUCKET_NAME} \
  --outgoing-bucket-name        ${OUTGOING_BUCKET_NAME} \
  --cloudwatch-log-group        ${CLOUDWATCH_LOG_GROUP} \
  --incoming-s3-path            2101-TSP \
  --cloudwatch-log-stream-name  2101-logs

# MP70 EVP
aggregate_rt_radio_messages \
  --device-model                MP70 \
  --device-operational-mode     EVP \
  --aws-region                  ${AWS_REGION} \
  --cdf-url                     ${CDF_URL} \
  --incoming-bucket-name        ${INCOMING_BUCKET_NAME} \
  --outgoing-bucket-name        ${OUTGOING_BUCKET_NAME} \
  --cloudwatch-log-group        ${CLOUDWATCH_LOG_GROUP} \
  --incoming-s3-path            MP70-EVP \
  --cloudwatch-log-stream-name  MP70-EVP-logs

# MP70 TSP
aggregate_rt_radio_messages \
  --device-model                MP70 \
  --device-operational-mode     TSP \
  --aws-region                  ${AWS_REGION} \
  --cdf-url                     ${CDF_URL} \
  --incoming-bucket-name        ${INCOMING_BUCKET_NAME} \
  --outgoing-bucket-name        ${OUTGOING_BUCKET_NAME} \
  --cloudwatch-log-group        ${CLOUDWATCH_LOG_GROUP} \
  --incoming-s3-path            MP70-TSP \
  --cloudwatch-log-stream-name  MP70-TSP-logs
