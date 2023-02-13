#!/bin/bash

# e.g copy_static_gtfs.sh gtt-etl-dev/gtfs/ cdta 12345 2022-09-21

bucket_path=$1
agency1=$2
agency2=$3
utc_date=$4


for table in agency calendar_dates calendar fare_attributes fare_rules routes shapes stop_times stops trips
do
    aws s3 sync \
        s3://$bucket_path/$table/agency=$agency1/date=$utc_date \
        s3://$bucket_path/$table/agency=$agency1/date=$utc_date
done
