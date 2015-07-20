from tyr.utilities.replace_mongo_server import ReplicaSet
from tyr.utilities.replace_mongo_server import run_mongo_command


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


def compact_mongodb_server(host):

    replica_set = ReplicaSet(host)

    validate_sync_to(replica_set)
