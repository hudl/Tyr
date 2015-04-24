from tyr.servers.server import Server

class CacheServer(Server):

    SERVER_TYPE = 'cache'

    CHEF_RUNLIST=['role[RoleCache]']

    def __init__(self, group=None, server_type=None, instance_type=None,
                    environment=None, ami=None, region=None, role=None,
                    keypair=None, availability_zone=None, security_groups=None,
                    block_devices=None, chef_path=None, couchbase_version=None,
                    couchbase_username=None, couchbase_password=None):

        if server_type is None: server_type = self.SERVER_TYPE

        self.couchbase_version = couchbase_version
        self.couchbase_username = couchbase_username
        self.couchbase_password = couchbase_password

        super(CacheServer, self).__init__(group, server_type, instance_type,
                                            environment, ami, region, role,
                                            keypair, availability_zone,
                                            security_groups, block_devices,
                                            chef_path)

    def configure(self):

        super(CacheServer, self).configure()

        if self.environment == 'prod':
            self.instance_type = 'r3.large'
        else:
            self.instance_type = 'm3.large'

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

        if not any([self.couchbase_version, self.couchbase_username,
                        self.couchbase_password]):
            return

        with self.chef_api:

            if self.couchbase_version:
                self.chef_node.attributes.set_dotted('couchbase.server.version',
                                                        self.couchbase_version)

                self.log.info('Set the couchbase.server.version to' \
                            '{version}'.format(version=self.couchbase_version))

            if self.couchbase_username:
                self.chef_node.attributes.set_dotted('couchbase.server.username',
                                                        self.couchbase_username)

                self.log.info('Set the couchbase.server.username to' \
                            '{username}'.format(username=self.couchbase_username))

            if self.couchbase_password:
                self.chef_node.attributes.set_dotted('couchbase.server.password',
                                                        self.couchbase_password)

                self.log.info('Set the couchbase.server.password to' \
                            '{password}'.format(password=self.couchbase_password))

            self.chef_node.save()
            self.log.info('Saved the Chef Node configuration')

