from tyr.servers.server import Server


class ScriptsServer(Server):

    SERVER_TYPE = 'scripts'

    CHEF_RUNLIST = ['role[RoleScripts]']

    IAM_ROLE_POLICIES = [
        'allow-describe-instances',
        'allow-describe-tags',
        'allow-describe-elbs',
        'allow-describe-snapshots',
        'allow-get-hudl-config',
    ]

    def __init__(self, group=None, server_type=None, instance_type=None,
                 environment=None, ami=None, region=None, role=None,
                 keypair=None, availability_zone=None, security_groups=None,
                 block_devices=None, chef_path=None, subnet_id=None,
                 dns_zones=None):

        if server_type is None:
            server_type = self.SERVER_TYPE

        super(ScriptsServer, self).__init__(group, server_type, instance_type,
                                            environment, ami, region, role,
                                            keypair, availability_zone,
                                            security_groups, block_devices,
                                            chef_path, subnet_id, dns_zones)

    def configure(self):
        if not self.instance_type:
            if self.environment == 'prod':
                self.instance_type = 't2.micro'
            else:
                self.instance_type = 't2.micro'
        super(ScriptsServer, self).configure()

        self.resolve_iam_role()
