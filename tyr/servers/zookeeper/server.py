from tyr.servers.server import Server


class ZookeeperServer(Server):

    SERVER_TYPE = 'zookeeper'

    CHEF_RUNLIST = ['role[RoleZookeeper]']

    IAM_ROLE_POLICIES = [
        'allow-describe-instances',
        'allow-describe-tags',
        'allow-volume-control'
    ]

    def __init__(self, group=None, server_type=None, instance_type=None,
                 environment=None, ami=None, region=None, role=None,
                 keypair=None, availability_zone=None, security_groups=None,
                 block_devices=None, chef_path=None, subnet_id=None,
                 dns_zones=None, platform=None, use_latest_ami=False,
                 ingress_groups_to_add=None, ports_to_authorize=None,
                 classic_link=False, add_route53_dns=True, chef_server_url=None,
                 exhibitor_s3config=None):

        if server_type is None:
            server_type = self.SERVER_TYPE

        self.exhibitor_s3config = exhibitor_s3config

        super(ZookeeperServer, self).__init__(group, server_type, instance_type,
                                              environment, ami, region, role,
                                              keypair, availability_zone,
                                              security_groups, block_devices,
                                              chef_path, subnet_id, dns_zones,
                                              platform, use_latest_ami,
                                              ingress_groups_to_add,
                                              ports_to_authorize, classic_link,
                                              add_route53_dns, chef_server_url)

    def set_chef_attributes(self):
        super(ZookeeperServer, self).set_chef_attributes()
        if self.exhibitor_s3config:
            self.CHEF_ATTRIBUTES['exhibitor'] = {
                'cli': {'s3config': self.exhibitor_s3config}
            }
            self.log.info('Set exhibitor.cli.s3config to {}'.format(
                self.exhibitor_s3config)
            )
        else:
            self.log.info('exhibitor.cli.s3config not set. Using default.')

    def configure(self):
        super(ZookeeperServer, self).configure()
        self.set_chef_attributes()

    def bake(self):
        super(ZookeeperServer, self).bake()
