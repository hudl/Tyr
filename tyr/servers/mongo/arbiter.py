from member import MongoReplicaSetMember


class MongoArbiterNode(MongoReplicaSetMember):

    NAME_TEMPLATE = '{envcl}-rs{replica_set}-{location}-arb'
    NAME_SEARCH_PREFIX = '{envcl}-rs{replica_set}-{location}-'
    NAME_AUTO_INDEX = False

    CHEF_RUNLIST = ['role[RoleMongo]']
    CHEF_MONGODB_TYPE = 'arbiter'

    def __init__(self, group=None, server_type=None, instance_type=None,
                 environment=None, ami=None, region=None, role=None,
                 keypair=None, availability_zone=None,
                 security_groups=None, block_devices=None,
                 chef_path=None, subnet_id=None, dns_zones=None,
                 ingress_groups_to_add=None, ports_to_authorize=None,
                 classic_link=False, add_route53_dns=True, chef_server_url=None,
                 replica_set=None):

        super(MongoArbiterNode, self).__init__(group, server_type,
                                               instance_type,
                                               environment, ami, region, role,
                                               keypair, availability_zone,
                                               security_groups, block_devices,
                                               chef_path, subnet_id, dns_zones,
                                               ingress_groups_to_add,
                                               ports_to_authorize, classic_link,
                                               add_route53_dns, chef_server_url,
                                               replica_set)

    def set_chef_attributes(self):
        super(MongoArbiterNode, self).set_chef_attributes()
        volumes = [
            {
                'device': {
                    'path': '/dev/xvdf',
                    'size': 1,
                    'iops': 0,
                    'name': 'mongodb-data'
                },
                'mount': {
                    'path': '/volr',
                    'user': 'mongod',
                    'group': 'mongod',
                    'chown': True                    
                }
            }
        ]

        if self.ephemeral_storage == []:
            volumes.append({
                'device': {
                    'path': '/dev/xvdc',
                    'size': 8,
                    'iops': 24,
                    'name': 'mongodb-swap'
                },
                'mount': {
                    'path': '/media/ephemeral0',
                    'user': 'root',
                    'group': 'root'                    
                }
            })

            self.log.debug('No instance storage; including swap device')

        self.CHEF_ATTRIBUTES['volumes'] = volumes
        self.log.info('Configured the volumes attribute')
        self.CHEF_ATTRIBUTES['mongodb']['config'] = {}
        self.CHEF_ATTRIBUTES['mongodb']['config'] = {'smallfiles': True}
        self.log.info('Configured the mongodb.config.smallfiles attribute')
