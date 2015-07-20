from tyr.utilities.replace_mongo_server import (ReplicaSet, run_command,
                                                run_mongo_command, timeit,
                                                set_maintenance_mode,
                                                unset_maintenance_mode)
import time
import logging
import os
import sys


log = logging.getLogger('Tyr.Utilities.ReplaceMongoServer')
if not log.handlers:
    log.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s [%(name)s] %(levelname)s: %(message)s',
        datefmt='%H:%M:%S')
    ch.setFormatter(formatter)
    log.addHandler(ch)


@timeit
def validate_sync_to(replica_set):
    nodes = [node for node in replica_set.status['members']
             if node['stateStr'] == 'SECONDARY']

    primary = [node for node in replica_set.status['members']
               if node['stateStr'] == 'PRIMARY'][0]

    for node in nodes:
        if node['syncingTo'] != primary['name']:
            command = 'rs.syncFrom(\'{primary}:27018\')'.format(
                primary=replica_set.primary)
            run_mongo_command(replica_set.primary, command)

            break


@timeit
def fetch_script(host, version):
    run_command(host, 'rm -rf /home/ec2-user/compact.js')

    uri = 'https://s3.amazonaws.com/hudl-chef-artifacts/mongodb/compact-{v}.js'
    uri = uri.format(v=version)

    command = 'curl -o /home/ec2-user/compact.js {uri}'.format(uri=uri)

    run_command(host, command)


@timeit
def compact(host):
    run_command(host, 'mongo --port 27018 /home/ec2-user/compact.js')


@timeit
def recovering(replica_set, host):
    nodes = replica_set.status['members']
    recovering = True

    for node in nodes:
        if node['name'] == host:
            if node['stateStr'] != 'RECOVERING':
                recovering = False

    return recovering


@timeit
def id_for_host(host):
    log.debug('Retrieving the instance ID')

    command = 'curl http://169.254.169.254/latest/meta-data/instance-id'
    instance_id = run_command(host, command)

    log.debug('The instance ID is {id_}'.format(id_=instance_id))

    return instance_id


@timeit
def compact_mongodb_server(host, version):
    stackdriver_api_key = os.environ.get('STACKDRIVER_API_KEY', False)

    if not stackdriver_api_key:
        log.critical('The environment variable STACKDRIVER_API_KEY '
                     'is undefined')
        sys.exit(1)

    stackdriver_username = os.environ.get('STACKDRIVER_USERNAME', False)

    if not stackdriver_username:
        log.critical('The environment variable STACKDRIVER_USERNAME '
                     'is undefined')
        sys.exit(1)

    replica_set = ReplicaSet(host)

    validate_sync_to(replica_set)

    secondaries = [node for node in replica_set.status['members']
                   if node['stateStr'] == 'SECONDARY']

    for secondary in secondaries:
        address = secondary['name'].split(':')[0]
        fetch_script(address, version)

        set_maintenance_mode(stackdriver_username, stackdriver_api_key,
                             id_for_host(secondary['name'].split(':')[0]))

        compact(address)

        while recovering(replica_set, secondary['name']):
            time.sleep(30)

        unset_maintenance_mode(stackdriver_username, stackdriver_api_key,
                               id_for_host(secondary['name'].split(':')[0]))

    secondaries = [node for node in replica_set.status['members']
                   if node['stateStr'] == 'PRIMARY']

    replica_set.failover()

    validate_sync_to(replica_set)

    for secondary in secondaries:
        address = secondary['name'].split(':')[0]
        fetch_script(address, version)

        set_maintenance_mode(stackdriver_username, stackdriver_api_key,
                             id_for_host(secondary['name'].split(':')[0]))

        compact(address)

        while recovering(replica_set, secondary['name']):
            time.sleep(30)

        unset_maintenance_mode(stackdriver_username, stackdriver_api_key,
                               id_for_host(secondary['name'].split(':')[0]))
