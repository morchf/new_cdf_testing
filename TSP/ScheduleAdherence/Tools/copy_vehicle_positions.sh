#!/bin/bash

# e.g copy_vehicle_positions.sh gtt-etl-dev/gtfs-realtime/vehicle_positions cdta 0537199e-e853-11ec-a8b8-f65b686c7d91 2022-06-11

bucket_path=$1
agency1=$2
agency2=$3
utc_date=$4


aws s3 sync \
    s3://$bucket_path/agency=$agency1/date=$utc_date \
    s3://$bucket_path/agency_id=$agency2/date=$utc_date
