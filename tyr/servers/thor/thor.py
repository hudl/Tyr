from tyr.servers.server import Server
from tyr.helpers import data_file
import chef
import os.path


class ThorServer(Server):

    SERVER_TYPE='web'

    CHEF_RUNLIST = ['role[RoleWeb]']
    
    IAM_MANAGED_POLICIES = [ 'allow-describe-instances',
                                'allow-describe-tags',
                                'ChefAllowAccess',
                                ]

    def __init__(self, group=None, server_type=None, instance_type=None,
                 environment=None, ami=None, region=None, role=None,
                 keypair=None, availability_zone=None, security_groups=None,
                 block_devices=None, chef_path=None, subnet_id=None,
                 dns_zones=None, platform=None, use_latest_ami=False,
                 ingress_groups_to_add=None, ports_to_authorize=None,
                 classic_link=False, add_route53_dns=True,
                 chef_server_url=None):

        if server_type is None:
            server_type = self.SERVER_TYPE

        if chef_server_url is None:
            chef_server_url = ('https://chef12.app.hudl.com/'
                                'organizations/hudl'
                                )

        super(ThorServer, self).__init__(group, server_type, instance_type,
                                          environment, ami, region, role,
                                          keypair, availability_zone,
                                          security_groups, block_devices,
                                          chef_path, subnet_id, dns_zones,
                                          platform, use_latest_ami,
                                          ingress_groups_to_add,
                                          ports_to_authorize, classic_link,
                                          add_route53_dns, chef_server_url)

    def configure(self):
        super(ThorServer, self).configure()

    @property
    def user_data(self):
        # read in userdata file
        user_data = None
        try:
            f = data_file('user_data_thor.ps2')
            user_data = f.read()
        except IOError:
            self.log.critical('No user info found, exiting!')
            exit(1)
        return user_data
