#!/bin/bash

. ./config.bash

AGENCY='gttdot'

curl -X PATCH \
  "$BASE_URL/groups/%2fagency%2f$AGENCY" \
  -H "$ACCEPT" \
  -H "$CONTENT_TYPE" \
  -d '{
        "attributes": {
           "ca_cert_id": "new_cert_id_1"
      }
}'
