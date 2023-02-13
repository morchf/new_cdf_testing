#!/bin/bash

# e.g download_vehicle_positions.sh gtt-etl-dev/gtfs-realtime/vehicle_positions 12345 2022-09-21 util/data

bucket_path=$1
agency=$2
utc_date=$3
output_dir=$4

aws s3 sync \
    s3://$bucket_path/agency=$agency/date=$utc_date \
    $output_dir/agency=$agency/date=$utc_date
