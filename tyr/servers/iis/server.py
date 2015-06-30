from tyr.servers.server import Server


class IISServer(Server):

    SERVER_TYPE = 'iis'

    CHEF_RUNLIST = ['role[RoleIIS]']

    IAM_ROLE_POLICIES = [
        'allow-describe-instances',
        'allow-describe-tags',
        'allow-describe-elbs',
    ]

    def __init__(self, group=None, server_type=None, instance_type=None,
                 environment=None, ami=None, region=None, role=None,
                 keypair=None, availability_zone=None, security_groups=None,
                 block_devices=None, chef_path=None, subnet_id=None,
                 dns_zones=None):

        if server_type is None:
            server_type = self.SERVER_TYPE

        super(IISServer, self).__init__(group, server_type, instance_type,
                                        environment, ami, region, role,
                                        keypair, availability_zone,
                                        security_groups, block_devices,
                                        chef_path, subnet_id, dns_zones)

    def configure(self):

        super(IISServer, self).configure()

        if self.environment == 'stage':
            self.IAM_ROLE_POLICIES.append('allow-modify-iis-elbs-stage')
        elif self.environment == 'prod':
            self.IAM_ROLE_POLICIES.append('allow-modify-iis-elbs-prod')
        self.resolve_iam_role()
