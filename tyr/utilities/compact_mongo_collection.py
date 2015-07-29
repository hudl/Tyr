from tyr.utilities.replace_mongo_server import (ReplicaSet, run_command,
                                                run_mongo_command, timeit)

from tyr.utilities.stackdriver import (set_maintenance_mode,
                                       unset_maintenance_mode)
import time
import logging
import os
import sys
import pprint


log = logging.getLogger('Tyr.Utilities.CompactMongoCollection')
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
    log.debug('Replica set status')
    for line in pprint.pformat(replica_set.status).split('\n'):
        log.debug(line)

    log.debug('Retrieving list of secondaries')

    nodes = [node for node in replica_set.status['members']
             if node['stateStr'] == 'SECONDARY']

    log.debug('Secondaries: {secondaries}'.format(
        secondaries=[n['name'] for n in nodes]))

    log.debug('Retrieving the primary')

    primary = [node for node in replica_set.status['members']
               if node['stateStr'] == 'PRIMARY'][0]

    log.debug('Primary: {primary}'.format(primary=primary['name']))

    log.debug('Checking value of the syncTo property')

    for node in nodes:
        if node['syncingTo'] != primary['name']:
            return False

    return True


@timeit
def enforce_sync_to(replica_set):
    log.debug('Replica set status')
    for line in pprint.pformat(replica_set.status).split('\n'):
        log.debug(line)

    log.debug('Retrieving list of secondaries')

    nodes = [node for node in replica_set.status['members']
             if node['stateStr'] == 'SECONDARY']

    log.debug('Secondaries: {secondaries}'.format(
        secondaries=[n['name'] for n in nodes]))

    log.debug('Retrieving the primary')

    primary = [node for node in replica_set.status['members']
               if node['stateStr'] == 'PRIMARY'][0]

    log.debug('Primary: {primary}'.format(primary=primary['name']))

    log.debug('Enforcing value of the syncTo property')

    for node in nodes:
        log.warning('{node} is syncing to {target}'.format(
            node=node['name'],
            target=node['syncingTo']))
        command = 'rs.syncFrom(\'{primary}:27018\')'.format(
            primary=replica_set.primary)
        log.info('Correcting using rs.syncFrom')
        run_mongo_command(node['name'].split(':')[0], command)

    log.debug('Replica set status')
    for line in pprint.pformat(replica_set.status).split('\n'):
        log.debug(line)


@timeit
def fetch_script(host, version):
    log.debug('Removing compact.js if it exists')
    run_command(host, 'rm -rf /home/ec2-user/compact.js')

    uri = 'https://s3.amazonaws.com/hudl-chef-artifacts/mongodb/compact-{v}.js'
    uri = uri.format(v=version)

    log.debug('Retrieving compact.js from {uri}'.format(uri=uri))

    command = 'curl -o /home/ec2-user/compact.js {uri}'.format(uri=uri)

    run_command(host, command)


@timeit
def compact(host):
    log.debug('Running compact.js on {host}'.format(host=host))
    run_command(host, 'mongo --port 27018 /home/ec2-user/compact.js')


@timeit
def recovering(replica_set, host):
    log.debug('Confirming {host} is finished recovering'.format(host=host))

    nodes = replica_set.status['members']
    recovering = True

    for node in nodes:
        if node['name'] == host:
            if node['stateStr'] != 'RECOVERING':
                recovering = False

    if recovering:
        log.debug('{host} is still recovering'.format(host=host))
    else:
        log.debug('{host} has finished recovering'.format(host=host))

    return recovering


@timeit
def id_for_host(host):
    log.debug('Retrieving the instance ID')

    command = 'curl http://169.254.169.254/latest/meta-data/instance-id'
    instance_id = run_command(host, command)

    log.debug('The instance ID is {id_}'.format(id_=instance_id))

    return instance_id


@timeit
def compact_mongodb_server(host, version, prompt_before_failover=True):

    log.debug('Retrieving replica set for host {host}'.format(host=host))
    replica_set = ReplicaSet(host)

    log.debug('Validating the syncingTo property on nodes')
    while not validate_sync_to(replica_set):
        log.debug('Enforcing the syncingTo property on nodes')
        enforce_sync_to(replica_set)

    log.debug('Validation of syncingTo property on nodes complete')

    secondaries = [node for node in replica_set.status['members']
                   if node['stateStr'] == 'SECONDARY']

    log.info('Compacting {nodes}'.format(
        nodes=[s['name'] for s in secondaries]))

    for secondary in secondaries:
        address = secondary['name'].split(':')[0]

        log.debug('Retrieving compact.js on {host}'.format(host=address))
        fetch_script(address, version)

        log.debug('Setting maintenance mode for {host}'.format(host=address))
        set_maintenance_mode(id_for_host(address))

        log.info('Compacting {host}'.format(host=address))
        compact(address)

        log.info('Waiting for {host} to recover'.format(host=address))
        while recovering(replica_set, secondary['name']):
            log.warning('{host} is still recovering.'.format(host=address))
            log.debug('Sleeping for 30 seconds.')
            time.sleep(30)

        log.debug('Unsetting maintenance mode for {host}'.format(
            host=address))
        unset_maintenance_mode(id_for_host(address))

    log.debug('Retrieving current primary')
    secondaries = [node for node in replica_set.status['members']
                   if node['stateStr'] == 'PRIMARY']

    log.debug('Preparing to compact primary {host}'.format(
        host=secondaries[0]['name']))

    log.info('Preparing to fail over replica set')

    if prompt_before_failover:
        print '\a'
        _ = raw_input('Press return to continue')

    log.debug('Instructing the replica set to fail over')
    replica_set.failover()

    log.debug('Validating the syncingTo property on nodes')
    while not validate_sync_to(replica_set):
        log.debug('Enforcing the syncingTo property on nodes')
        enforce_sync_to(replica_set)

    log.debug('Validation of syncingTo property on nodes complete')

    for secondary in secondaries:
        address = secondary['name'].split(':')[0]

        log.debug('Retrieving compact.js on {host}'.format(host=address))
        fetch_script(address, version)

        log.debug('Setting maintenance mode for {host}'.format(host=address))
        set_maintenance_mode(id_for_host(address))

        log.info('Compacting {host}'.format(host=address))
        compact(address)

        log.info('Waiting for {host} to recover'.format(host=address))
        while recovering(replica_set, secondary['name']):
            log.warning('{host} is still recovering.'.format(host=address))
            log.debug('Sleeping for 30 seconds.')
            time.sleep(30)

        log.debug('Unsetting maintenance mode for {host}'.format(
            host=address))
        unset_maintenance_mode(id_for_host(address))
