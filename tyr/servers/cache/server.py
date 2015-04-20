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

    def configure(self):

        super(CacheServer, self).configure()

        # This is just a temporary fix to override the default security
        # groups for Cache servers until the security_groups argument is
        # removed.

        self.security_groups = [
            'management',
            'chef-nodes',
            self.envcl,
            '{env}-cache-management'.format(env=self.environment[0])
        ]

        self.resolve_security_groups()

    def bake(self):

        super(CacheServer, self).bake()

        with self.chef_api:

            if self.chef_node.chef_environment == 'prod':
                self.chef_node.run_list.append('role[RoleSumoLogic]')

            self.log.info('Set the run list to "{runlist}"'.format(
                                            runlist = self.chef_node.run_list))

            self.chef_node.save()

            self.log.info('Saved the Chef Node configuration')
