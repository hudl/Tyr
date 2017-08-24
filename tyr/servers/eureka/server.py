from tyr.servers.server import Server


class EurekaServer(Server):

    SERVER_TYPE = 'eureka'

    CHEF_RUNLIST = ['role[RoleEureka]']

    IAM_ROLE_POLICIES = [
        'allow-describe-instances',
        'allow-describe-tags'
    ]

    def __init__(self, group=None, server_type=None, instance_type=None,
                 environment=None, ami=None, region=None, role=None,
                 keypair=None, availability_zone=None, security_groups=None,
                 block_devices=None, chef_path=None, subnet_id=None,
                 platform=None, use_latest_ami=False,
                 ingress_groups_to_add=None, ports_to_authorize=None,
                 classic_link=False, chef_server_url=None):

        if server_type is None:
            server_type = self.SERVER_TYPE

        super(EurekaServer, self).__init__(group, server_type, instance_type,
                                           environment, ami, region, role,
                                           keypair, availability_zone,
                                           security_groups, block_devices,
                                           chef_path, subnet_id,
                                           platform, use_latest_ami,
                                           ingress_groups_to_add,
                                           ports_to_authorize, classic_link,
                                           chef_server_url)
