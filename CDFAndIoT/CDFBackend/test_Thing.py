import boto3
import botocore
from botocore.stub import Stubber
import pytest
from unittest.mock import Mock, patch

from thing import Thing

iot = boto3.client('iot')

class TestThing:
  @pytest.fixture
  def thing(self):
    return Thing('test_thing')

  @pytest.fixture
  def populated_thing_list(self):
    return {
      'things': [
          {
              'thingName': 'test_thing',
              'thingArn': 'arn:aws:iot:us-east-1:123456789012:thing/test_thing',
              'attributes': {},
              'version': 1
          },
      ]
  }

  @pytest.fixture
  def empty_thing_list(self):
    return {'things': []}

  @pytest.fixture
  def cert_arn(self):
    return 'arn:aws:iot:us-east-1:123456789012:cert/0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef0'

  def test_create(self, thing, empty_thing_list):
    mock_response = {
      'thingName': 'test_thing',
      'thingArn': 'arn:aws:iot:us-east-1:123456789012:thing/test_thing',
      'thingId': '12345678-1234-1234-1234-1234567890ab'
    }

    with Stubber(iot) as stub:
      with patch.object(thing, 'client', iot):
        stub.add_response('list_things', empty_thing_list, {})
        stub.add_response('create_thing', mock_response, {'thingName': 'test_thing'})
        arn = thing.create()

    assert arn == thing.arn == mock_response['thingArn']

  def test_delete(self, thing, populated_thing_list, cert_arn):
    mock_principals = {'principals': [cert_arn]}
    with Stubber(iot) as stub:
      with patch.object(thing, 'client', iot):
        stub.add_response('list_things', populated_thing_list, {})
        stub.add_response('list_things', populated_thing_list, {})
        stub.add_response('list_thing_principals', mock_principals, {'thingName': 'test_thing'})
        stub.add_response('list_things', populated_thing_list, {})
        stub.add_response('detach_thing_principal', {}, {'principal': cert_arn, 'thingName': 'test_thing'})
        stub.add_response('delete_thing', {}, {'thingName': 'test_thing'})
        thing.delete()

      stub.assert_no_pending_responses()

  def test_exists(self, thing, populated_thing_list):
    with Stubber(iot) as stub:
      with patch.object(thing, 'client', iot):
        stub.add_response('list_things', populated_thing_list, {})
        exists = thing.exists()

    assert exists, 'thing does not exist'

  def test_not_exists(self, thing, empty_thing_list):
    with Stubber(iot) as stub:
      with patch.object(thing, 'client', iot):
        stub.add_response('list_things', empty_thing_list, {})
        exists = thing.exists()

    assert not exists, 'thing exists'

  def test_attach_principal(self, thing, populated_thing_list, cert_arn):
    with Stubber(iot) as stub:
      with patch.object(thing, 'client', iot):
        stub.add_response('list_things', populated_thing_list, {})
        stub.add_response('attach_thing_principal', {}, {'principal': cert_arn, 'thingName': 'test_thing'})
        thing.attach_principal(arn=cert_arn)

      stub.assert_no_pending_responses()

  def test_detach_principal(self, thing, populated_thing_list, cert_arn):
    with Stubber(iot) as stub:
      with patch.object(thing, 'client', iot):
        stub.add_response('list_things', populated_thing_list, {})
        stub.add_response('detach_thing_principal', {}, {'principal': cert_arn, 'thingName': 'test_thing'})
        thing.detach_principal(arn=cert_arn)

      stub.assert_no_pending_responses()

  def test_list_principals(self, thing, populated_thing_list, cert_arn):
    mock_response = {
      'principals': [cert_arn]
    }

    with Stubber(iot) as stub:
      with patch.object(thing, 'client', iot):
        stub.add_response('list_things', populated_thing_list, {})
        stub.add_response('list_thing_principals', mock_response, {'thingName': 'test_thing'})
        res = thing.list_principals()

    assert res == mock_response['principals']
