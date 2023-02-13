#!/bin/bash

. ./config.bash

echo 'GET $BASE_URL/groups/%2fagency/members/groups'
curl -X GET \
  "$BASE_URL/groups/%2fagency/members/groups" \
  -H "$ACCEPT" \
  -H "$CONTENT_TYPE" 

echo ''
echo 'GET $BASE_URL/groups/%2fagency/memberships'
curl -X GET \
  "$BASE_URL/groups/%2fagency/memberships" \
  -H "$ACCEPT" \
  -H "$CONTENT_TYPE" 

echo ''
echo 'GET BASE_URL/groups/%2fagency'
curl -X GET \
  "$BASE_URL/groups/%2fagency" \
  -H "$ACCEPT" \
  -H "$CONTENT_TYPE" 

echo ''
echo 'GET "$BASE_URL/groups/%2f/'
curl -X GET \
  "$BASE_URL/groups/%2f/" \
  -H "$ACCEPT" \
  -H "$CONTENT_TYPE" 

echo ''

