#!/bin/bash

. ./config.bash

AGENCY_NAME='a1'
echo "Deleting agency $AGENCY_NAME"
curl -X DELETE \
  "$BASE_URL/groups/%2fagency%2f$AGENCY_NAME" \
  -H "$ACCEPT" \
  -H "$CONTENT_TYPE" 
