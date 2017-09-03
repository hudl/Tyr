from node import MongoNode
from chef.exceptions import ChefServerError

REPLICA_SET_MODS = {
    'monolith': {
        'data': lambda n: 'RS{}'.format(n.replica_set)
    },        
    'exchanges': {
        'data': lambda n: 'RS{}'.format(n.replica_set)
    },
    'clips': {
        'data': lambda n: 'CLIPS'
    },
    'feed': {
        'data': lambda n: 'FEED-RS{}'.format(n.replica_set)
    },
    'highlights': {
        'data': lambda n: {1: 'highlights_0', 2: 'highlights_1', 3: 'highlights-rs3'}[n.replica_set],
        'config': lambda n: 'configHighlights'
    },
    'hudlrd': {
        'data': lambda n: 'predator-rs{}'.format(n.replica_set)
    },
    'leroy': {
        'data': lambda n: 'LEROY'
    },
    'overwatch': {
        'data': lambda n: '{}-overwatch'.format(n.environment[0])
    },
    'push': {
        'data': lambda n: 'PUSH'
    },
    'recruit': {
        'data': lambda n: 'REC'
    },
    'statistics': {
        'data': lambda n: 'STATS'
    }
}


class MongoReplicaSetMember(MongoNode):

    REPLICA_SET_TEMPLATE = '{group}-rs{set_}'

    def __init__(self, group=None, server_type=None, instance_type=None,
                 environment=None, ami=None, region=None, role=None,
                 keypair=None, availability_zone=None,
                 security_groups=None, block_devices=None,
                 chef_path=None, subnet_id=None,
                 platform=None, use_latest_ami=None,
                 ingress_groups_to_add=None, ports_to_authorize=None,
                 classic_link=False, chef_server_url=None,
                 mongodb_version=None, replica_set=None):

        super(MongoReplicaSetMember, self).__init__(group, server_type,
                                                    instance_type,
                                                    environment, ami, region,
                                                    role, keypair,
                                                    availability_zone,
                                                    security_groups,
                                                    block_devices, chef_path,
                                                    subnet_id, platform,
                                                    use_latest_ami,
                                                    ingress_groups_to_add,
                                                    ports_to_authorize,
                                                    classic_link,
                                                    chef_server_url,
                                                    mongodb_version)

        self.replica_set = replica_set


    def set_chef_attributes(self):
        super(MongoReplicaSetMember, self).set_chef_attributes()
        self.CHEF_ATTRIBUTES['mongodb']['replicaset_name'] = self.replica_set


    def configure(self):
        super(MongoReplicaSetMember, self).configure()

        try:
            self.replica_set = REPLICA_SET_MODS[self.group][self.CHEF_MONGODB_TYPE](self)
        except KeyError:
            self.replica_set = self.REPLICA_SET_TEMPLATE.format(
                group=self.group, set_=self.replica_set
            )

        self.log.info('Using replica set {set}'.format(set=self.replica_set))

    def configure(self):
        super(MongoReplicaSetMember, self).configure()


    @property
    def tags(self):

        tags = super(MongoReplicaSetMember, self).tags
        tags['ReplicaSet'] = self.replica_set

        return tags
