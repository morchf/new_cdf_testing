#!/bin/bash

. ./config.bash

echo "POST BASE_URL/devices" 
JSON=$(< v1.json)
echo $JSON

curl -X POST \
  "$BASE_URL/devices" \
  -H "$ACCEPT" \
  -H "$CONTENT_TYPE" \
  -d "$JSON"
