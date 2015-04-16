from node import MongoNode

class MongoConfigNode(MongoNode):

    NAME_TEMPLATE = '{envcl}-cfg-{zone}'
    NAME_SEARCH_PREFIX = '{envcl}-cfg-'
    NAME_AUTO_INDEX = False

    CHEF_RUNLIST = ['role[RoleMongo]']
    CHEF_MONGODB_TYPE = 'config'

    def __init__(self, group = None, server_type = None, instance_type = None,
                    environment = None, ami = None, region = None, role = None,
                    keypair = None, availability_zone = None,
                    security_groups = None, block_devices = None,
                    chef_path = None, vpc_id = None, subnet_id = None):

        super(MongoConfigNode, self).__init__(group, server_type, instance_type,
                                                environment, ami, region, role,
                                                keypair, availability_zone,
                                                security_groups,
                                                block_devices, chef_path, 
                                                vpc_id, subnet_id)

    def bake(self):

        super(MongoConfigNode, self).bake()

        with self.chef_api:

            self.chef_node.attributes.set_dotted('hudl_ebs.volumes', [
                {
                    'user': 'mongod',
                    'group': 'mongod',
                    'size': 5,
                    'iops': 0,
                    'device': '/dev/xvdg',
                    'mount': '/volr/journal'
                },
                {
                    'user': 'mongod',
                    'group': 'mongod',
                    'size': 5,
                    'iops': 0,
                    'device': '/dev/xvdf',
                    'mount': '/volr'
                }
            ])

            self.log.info('Configured the hudl_ebs.volumes attribute')

            self.chef_node.save()
            self.log.info('Saved the Chef Node configuration')
