#!/bin/bash

. ./config.bash

curl -X PATCH \
  "$BASE_URL/devices/mphcar" \
  -H "$ACCEPT" \
  -H "$CONTENT_TYPE" \
  -d '{
        "attributes": {
            "dev_cert_id": "dev_cert_id_1"
      }
}'
