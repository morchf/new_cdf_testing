#!/bin/bash

. ./config.bash

curl -X DELETE \
  "$BASE_URL/devices/v1" \
  -H "$ACCEPT" \
  -H "$CONTENT_TYPE" 
