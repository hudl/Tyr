from tyr.utilities.replace_mongo_server import ReplicaSet
from tyr.utilities.replace_mongo_server import run_command, run_mongo_command


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


def fetch_script(host, version):
    run_command(host, 'rm -rf /home/ec2-user/compact.js')

    uri = 'https://s3.amazonaws.com/hudl-chef-artifacts/mongodb/compact-{v}.js'
    uri = uri.format(v=version)

    command = 'curl -o /home/ec2-user/compact.js {uri}'.format(uri=uri)

    run_command(host, command)


def compact(host):
    run_command(host, 'mongo --port 27018 /home/ec2-user/compact.js')


def compact_mongodb_server(host, version):
    replica_set = ReplicaSet(host)

    validate_sync_to(replica_set, version)

    secondaries = [node for node in replica_set.status['members']
                   if node['stateStr'] == 'SECONDARY']

    for secondary in secondaries:
        address = secondary['name'].split(':')[0]
        fetch_script(address, version)

        compact(address)
