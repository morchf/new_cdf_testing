#!/bin/bash

. ./config.bash

AGENCY_NAME='a1'
echo "Creating agency $AGENCY_NAME"
JSON=$(<${AGENCY_NAME}_agency.json)
echo $JSON

curl -X POST \
  "$BASE_URL/groups/" \
  -H "$ACCEPT" \
  -H "$CONTENT_TYPE" \
  -d "$JSON"
