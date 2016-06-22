from tyr.servers.server import Server
from tyr.helpers import data_file
import chef
import requests
import time
import os.path


class NginxServer(Server):

    SERVER_TYPE = 'nginx'

    CHEF_RUNLIST = ['role[RoleNginx]']

    IAM_ROLE_POLICIES = [
        'allow-describe-instances',
        'allow-describe-tags',
        'allow-create-tags',
        'allow-lifecycle-nginx-stage',
        'allow-describe-elbs',
        'allow-get-nginx-config',
        'allow-modify-nginx-elbs-{environment}'
    ]

    def __init__(self, group=None, server_type=None, instance_type=None,
                 environment=None, ami=None, region=None, role=None,
                 keypair=None, availability_zone=None, security_groups=None,
                 block_devices=None, chef_path=None, subnet_id=None,
                 dns_zones=None):

        if server_type is None:
            server_type = self.SERVER_TYPE

        super(NginxServer, self).__init__(group, server_type, instance_type,
                                          environment, ami, region, role,
                                          keypair, availability_zone,
                                          security_groups, block_devices,
                                          chef_path, subnet_id, dns_zones)

    def configure(self):
        super(NginxServer, self).establish_logger()
        super(NginxServer, self).configure()

    @property
    def user_data(self):    
        # read in userdata file
        self.log.info("Loading user-data [user_data_file.ps2]")
        user_data = None
        try:
            f = data_file('user_data_base.ps2')
            user_data = f.read()
        except IOError:
            # Handle error reading file
            pass
            self.log.warning("Could not load user data file")
        return user_data
