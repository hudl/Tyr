import requests
import os
import json
import time
import logging

log = logging.getLogger('Tyr.Utilities.Stackdriver')
if not log.handlers:
    log.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
            '%(asctime)s [%(name)s] %(levelname)s: %(message)s',
            datefmt='%H:%M:%S')
    ch.setFormatter(formatter)
    log.addHandler(ch)

STACKDRIVER_USERNAME = os.environ.get('STACKDRIVER_USERNAME',False)

if not STACKDRIVER_USERNAME:
    log.critical('The environment variable STACKDRIVER_USERNAME '
                    'is undefined')
    sys.exit(1)

STACKDRIVER_API_KEY  = os.environ.get('STACKDRIVER_API_KEY',False)

if not STACKDRIVER_API_KEY:
    log.critical('The environment variable STACKDRIVER_API_KEY '
                    'is undefined')
    sys.exit(1)


def registered_in_stackdriver(instance_id):

    log.debug('Checking if {instance_id} is listed in Stackdriver'.format(
                                                    instance_id=instance_id))

    headers = headers = {
        'x-stackdriver-apikey': STACKDRIVER_API_KEY,
        'Content-Type': 'application/json'
    }

    log.debug('Using the headers {headers}'.format(headers=headers))

    template = 'https://api.stackdriver.com/v0.2/instances/{id_}'

    endpoint = template.format(id_=instance_id)

    log.debug('Using the endpoint {endpoint}'.format(endpoint=endpoint))

    r = requests.get(endpoint, headers=headers)

    log.debug('Received status code {code}'.format(code=r.status_code))

    listed = (r.status_code != 404)

    if listed:
        log.debug('The instance is listed in Stackdriver')
    else:
        log.debug('The instance is not listed in Stackdriver')

    return listed

def set_maintenance_mode(instance_id):

    log.debug('Placing {instance_id} into maintenance mode'.format(
                                                    instance_id=instance_id))

    while not registered_in_stackdriver(log,instance_id):

        log.error('The instance is not listed in Stackdriver')
        log.debug('Trying again in 10 seconds')
        time.sleep(10)

    headers = {
        'x-stackdriver-apikey': STACKDRIVER_API_KEY,
        'Content-Type': 'application/json'
    }

    log.debug('Using the headers {headers}'.format(headers=headers))

    template = 'https://api.stackdriver.com/v0.2/instances/{id_}/maintenance/'
    endpoint = template.format(id_=instance_id)

    log.debug('Using the endpoint {endpoint}'.format(endpoint=endpoint))

    body = {
        'username': STACKDRIVER_USERNAME,
        'reason': "Waiting for MongoDB node to finish syncing.",
        'maintenance': True
    }

    log.debug('Using the body {body}'.format(body=body))

    data = json.dumps(body)

    r = requests.put(endpoint, data=data, headers=headers)

    log.debug('Received status code {code}'.format(code=r.status_code))

    if r.status_code != 200:
        log.critical('Failed to put the node into maintenance mode. '
                     'Received code {code}'.format(code=r.status_code))
        sys.exit(1)

    else:
        log.debug('Placed the node into maintenance mode')

def unset_maintenance_mode(instance_id):

    log.debug('Removing {instance_id} from maintenance mode'.format(
                                                    instance_id=instance_id))

    headers = {
        'x-stackdriver-apikey': STACKDRIVER_API_KEY,
        'Content-Type': 'application/json'
    }

    log.debug('Using the headers {headers}'.format(headers=headers))

    template = 'https://api.stackdriver.com/v0.2/instances/{id_}/maintenance/'
    endpoint = template.format(id_=instance_id)

    log.debug('Using the endpoint {endpoint}'.format(endpoint=endpoint))

    body = {
        'username': STACKDRIVER_USERNAME,
        'reason': "MongoDB node finished syncing.",
        'maintenance': False
    }

    log.debug('Using the body {body}'.format(body=body))

    data = json.dumps(body)

    r = requests.put(endpoint, data=data, headers=headers)

    log.debug('Received status code {code}'.format(code=r.status_code))

    if r.status_code != 200:

        log.critical('Failed to remove the node from maintenance mode. '
                     'Received code {code}'.format(code=r.status_code))
        sys.exit(1)

    else:

        log.debug('Removed the node from maintenance mode.')
