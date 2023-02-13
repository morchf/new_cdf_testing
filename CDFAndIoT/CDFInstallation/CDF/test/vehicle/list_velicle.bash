#!/bin/bash

. ./config.bash

echo ""
echo "$BASE_URL/devices/mphcar" 
curl -X GET \
  "$BASE_URL/devices/mphcar" \
  -H "$ACCEPT" \
  -H "$CONTENT_TYPE" 

echo ""
echo "$BASE_URL/devices/sleigh"
curl -X GET \
  "$BASE_URL/devices/sleigh" \
  -H "$ACCEPT" \
  -H "$CONTENT_TYPE" 

echo ""
echo "$BASE_URL/groups/%2fagency%2fgttdot/owns/devices"
curl -X GET \
  "$BASE_URL/groups/%2fagency%2fgttdot/owns/devices" \
  -H "$ACCEPT" \
  -H "$CONTENT_TYPE" 

echo ""
echo "$BASE_URL/groups/%2fagency%2fa1/owns/devices" 
curl -X GET \
  "$BASE_URL/groups/%2fagency%2fa1/owns/devices" \
  -H "$ACCEPT" \
  -H "$CONTENT_TYPE" 
echo ""
