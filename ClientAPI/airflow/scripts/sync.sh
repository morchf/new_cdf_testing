#!/bin/bash

export AWS_PROFILE="${ENV:-dev}"
ENV="${ENV:-$AWS_PROFILE}"

aws s3 sync ../airflow s3://client-api-artifacts-$ENV/airflow/
