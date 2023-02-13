import requests
import json
import logging
import time
from functools import wraps

def log(msg, logger=None):
    if logger:
        logger.warning(msg)
    else:
        print(msg)

def retry(exceptions, total_tries=4, initial_wait=0.5, backoff_factor=2, logger=None):
    """Calling the decorated function applying an exponential backoff.

    Args:
        exceptions (Exception): Exception(s) that trigger a retry, can be a tuple
        total_tries (int, optional): Total tries. Defaults to 4.
        initial_wait (float, optional): Time to first retry. Defaults to 0.5.
        backoff_factor (int, optional): Backoff multiplier (e.g. value of 2 will double the delay each retry). Defaults to 2.
        logger ([type], optional): Logger to be used, if none specified print. Defaults to None.
    """
    def retry_decorator(f):
        @wraps(f)
        def func_with_retries(*args, **kwargs):
            _tries, _delay = total_tries + 1, initial_wait
            while _tries > 1:
                try:
                    log(f'{total_tries + 2 - _tries}. try:', logger)
                    return f(*args, **kwargs)
                except exceptions as e:
                    _tries -= 1
                    print_args = args if args else 'no args'
                    if _tries == 1:
                        msg = str(f'Function: {f.__name__}\n'
                                  f'Failed despite best efforts after {total_tries} tries.\n'
                                  f'args: {print_args}, kwargs: {kwargs}'
                        )
                        log(msg, logger)
                        raise
                    msg = str(f'Function: {f.__name__}\n'
                              f'Exception: {e}\n'
                              f'Retrying in {_delay} seconds!, args: {print_args}, kwargs: {kwargs}\n'
                    )
                    log(msg, logger)
                    time.sleep(_delay)
                    _delay *= backoff_factor
        return func_with_retries
    return retry_decorator

@retry(Exception, initial_wait=5)
def GetMp70To2100DeviceId(baseUrl, deviceid):
    response = requests.request(method='GET', url=f"{baseUrl.strip('/')}/devices/{deviceid}")
    return json.loads(response.text)['attributes']['gttSerial']
    
@retry(Exception, initial_wait=5)
def GetMp70AgencyGuid(baseUrl, deviceid):
    response = requests.request(method='GET', url=f"{baseUrl.strip('/')}/devices/{deviceid}")
    ownedby = json.loads(response.text).get('groups').get('ownedby')[0].split("/")
    response = requests.request(method='GET', url=f"{baseUrl.strip('/')}/groups/%2f{ownedby[-2]}%2f{ownedby[-1]}")
    return json.loads(response.text)['attributes']['agencyID']

if __name__ == "__main__":
    baseUrl = "https://example.api.gateway.url/StageName"
    deviceid = "SimDevice0101"

    id_2100 = GetMp70To2100DeviceId(baseUrl, deviceid)
    guid_agency = GetMp70AgencyGuid(baseUrl, deviceid)
    print(id_2100, guid_agency)