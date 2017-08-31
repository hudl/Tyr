from node import MongoNode


class MongoRouterNode(MongoNode):

    NAME_TEMPLATE = '{envcl}-router-{location}-{index}'
    NAME_SEARCH_PREFIX = '{envcl}-router-'
    NAME_AUTO_INDEX = True

    CHEF_RUNLIST = ['role[RoleMongo]']
    CHEF_MONGODB_TYPE = 'router'

    def __init__(self, group=None, server_type=None, instance_type=None,
                 environment=None, ami=None, region=None, role=None,
                 keypair=None, availability_zone=None,
                 security_groups=None, block_devices=None,
                 chef_path=None, subnet_id=None,
                 ingress_groups_to_add=None, ports_to_authorize=None,
                 classic_link=False, chef_server_url=None):

        super(MongoRouterNode, self).__init__(group, server_type,
                                              instance_type,
                                              environment, ami, region, role,
                                              keypair, availability_zone,
                                              security_groups,
                                              block_devices, chef_path,
                                              subnet_id,
                                              ingress_groups_to_add,
                                              ports_to_authorize, classic_link,
                                              chef_server_url)

def set_chef_attributes(self):
    super(MongoConfigNode, self).set_chef_attributes()

    volumes = [
        {
            'device': {
                'path': '/dev/xvdh',
                'size': 10,                    
                'name': 'mongodb-logs'
            },
            'mount': {
                'path': '/mongologs',
                'user': 'mongod',
                'group': 'mongod'                    
            }
        }
    ]
    
    self.CHEF_ATTRIBUTES['volumes'] = volumes
    self.log.info('Configured the volumes attribute')
