from node import MongoNode


class MongoConfigNode(MongoNode):

    NAME_TEMPLATE = '{envcl}-cfg-{location}-{index}'
    NAME_SEARCH_PREFIX = '{envcl}-cfg-'
    NAME_AUTO_INDEX = True

    CHEF_RUNLIST = ['role[RoleMongo]']
    CHEF_MONGODB_TYPE = 'config'

    def __init__(self, group=None, server_type=None, instance_type=None,
                 environment=None, ami=None, region=None, role=None,
                 keypair=None, availability_zone=None,
                 security_groups=None, block_devices=None,
                 chef_path=None, subnet_id=None,
                 ingress_groups_to_add=None, ports_to_authorize=None,
                 classic_link=False, chef_server_url=None,
                 data_volume_snapshot_id=None):

        super(MongoConfigNode, self).__init__(group, server_type,
                                              instance_type,
                                              environment, ami, region, role,
                                              keypair, availability_zone,
                                              security_groups,
                                              block_devices, chef_path,
                                              subnet_id,
                                              ingress_groups_to_add,
                                              ports_to_authorize, classic_link,
                                              chef_server_url)

        self.data_volume_snapshot_id = data_volume_snapshot_id
                                              

    def set_chef_attributes(self):
        super(MongoConfigNode, self).set_chef_attributes()

        volumes = [
            {
                'device': {
                    'path': '/dev/xvdf',
                    'size': 5,
                    'name': 'mongodb-data',
                    'snapshot_id': self.data_volume_snapshot_id
                },
                'mount': {
                    'path': '/volr',
                    'user': 'mongod',
                    'group': 'mongod',
                    'chown': True                    
                }
            },
            {
                'device': {
                    'path': '/dev/xvdg',
                    'size': 5,                
                    'name': 'mongodb-journal'
                },
                'mount': {
                    'path': '/volr/journal',
                    'user': 'mongod',
                    'group': 'mongod'                    
                }
            },
            {
                'device': {
                    'path': '/dev/xvdh',
                    'size': 20,                    
                    'name': 'mongodb-logs'
                },
                'mount': {
                    'path': '/mongologs',
                    'user': 'mongod',
                    'group': 'mongod'                    
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
