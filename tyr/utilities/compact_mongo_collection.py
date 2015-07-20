from tyr.utilities.replace_mongo_server import (ReplicaSet, run_command,
                                                run_mongo_command, timeit)
import time
import logging

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
            command = 'rs.syncFrom(\'{primary}\')'.format(
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
def compact_mongodb_server(host, version):
    replica_set = ReplicaSet(host)

    validate_sync_to(replica_set)

    secondaries = [node for node in replica_set.status['members']
                   if node['stateStr'] == 'SECONDARY']

    for secondary in secondaries:
        address = secondary['name'].split(':')[0]
        fetch_script(address, version)

        compact(address)

        while recovering(replica_set, secondary['name']):
            time.sleep(30)

    secondaries = [node for node in replica_set.status['members']
                   if node['stateStr'] == 'PRIMARY']

    replica_set.failover()

    validate_sync_to(replica_set)

    for secondary in secondaries:
        address = secondary['name'].split(':')[0]
        fetch_script(address, version)

        compact(address)

        while recovering(replica_set, secondary['name']):
            time.sleep(30)
