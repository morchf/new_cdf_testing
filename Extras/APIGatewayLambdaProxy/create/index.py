import json

def handler(event, context):
  status_code = 201
  response_body = { 'petId': '1234abcd' }

  return {
    'statusCode': status_code,
    'body': json.dumps(response_body)
  }
