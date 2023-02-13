import json

def handler(event, context):
  petId = event['path'].split('/')[-1]

  if petId == '1234abcd':
    status_code = 200
    response_body = {
      'id': '1234abcd',
      'category': 'doggo',
      'name': 'Fido',
      'tags': [
        'attac',
        'protec',
        'snacc'
      ],
      'status': 'available'
    }

  else:
    status_code = 404
    response_body = {
        'code': 1,
        'type': 'NotFoundError',
        'message': 'The requested pet could not be found'
    }

  return {
    'statusCode': status_code,
    'body': json.dumps(response_body)
  }
