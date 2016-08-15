from node import MongoNode


class MongoConfigNode(MongoNode):

    NAME_TEMPLATE = '{envcl}-cfg-{location}'
    NAME_SEARCH_PREFIX = '{envcl}-cfg-'
    NAME_AUTO_INDEX = False

    CHEF_RUNLIST = ['role[RoleMongo]']
    CHEF_MONGODB_TYPE = 'config'

    def __init__(self, group=None, server_type=None, instance_type=None,
                 environment=None, ami=None, region=None, role=None,
                 keypair=None, availability_zone=None,
                 security_groups=None, block_devices=None,
                 chef_path=None, subnet_id=None, dns_zones=None,
                 ingress_groups_to_add=None, ports_to_authorize=None,
                 classic_link=False, add_route53_dns=True,
                 chef_server_url=None):

        super(MongoConfigNode, self).__init__(group, server_type,
                                              instance_type,
                                              environment, ami, region, role,
                                              keypair, availability_zone,
                                              security_groups,
                                              block_devices, chef_path,
                                              subnet_id, dns_zones,
                                              ingress_groups_to_add,
                                              ports_to_authorize, classic_link,
                                              add_route53_dns, chef_server_url)

    def set_chef_attributes(self):
        super(MongoConfigNode, self).set_chef_attributes()
        ebs_volumes = [
            {
                'user': 'mongod',
                'group': 'mongod',
                'size': 5,
                'iops': 0,
                'device': '/dev/xvdf',
                'mount': '/volr'
            },
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
                'size': 20,
                'iops': 0,
                'device': '/dev/xvdh',
                'mount': '/mongologs',
            }
        ]

        if self.ephemeral_storage == []:
            ebs_volumes.append({
                'user': 'root',
                'group': 'root',
                'size': 8,
                'iops': 24,
                'device': '/dev/xvdc',
                'mount': '/media/ephemeral0'
            })

            self.log.debug('No instance storage; including swap device')

        self.CHEF_ATTRIBUTES['hudl_ebs'] = {'volumes': ebs_volumes}
        self.log.info('Configured the hudl_ebs.volumes attribute')

    def bake(self):
        super(MongoConfigNode, self).bake()
