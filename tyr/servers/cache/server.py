from tyr.servers.server import Server

class CacheServer(Server):

    SERVER_TYPE = 'cache'

    CHEF_RUNLIST=['role[RoleCache]']

    def __init__(self, group=None, server_type=None, instance_type=None,
                    environment=None, ami=None, region=None, role=None,
                    keypair=None, availability_zone=None, security_groups=None,
                    block_devices=None, chef_path=None):

        if server_type is None: server_type = self.SERVER_TYPE

        super(CacheServer, self).__init__(group, server_type, instance_type,
                                            environment, ami, region, role,
                                            keypair, availability_zone,
                                            security_groups, block_devices,
                                            chef_path)


