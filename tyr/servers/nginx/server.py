from tyr.servers.server import Server
from tyr.helpers import data_file
import re
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
        'allow-lifecycle-nginx-{environment}',
        'allow-describe-elbs',
        'allow-get-nginx-config',
        'allow-modify-nginx-elbs-{environment}'
    ]

    def __init__(self, group=None, server_type=None, instance_type=None,
                 environment=None, ami=None, region=None, role=None,
                 keypair=None, availability_zone=None, security_groups=None,
                 block_devices=None, chef_path=None, subnet_id=None,
                 dns_zones=None, platform=None, use_latest_ami=False):

        if server_type is None:
            server_type = self.SERVER_TYPE

        super(NginxServer, self).__init__(group, server_type, instance_type,
                                          environment, ami, region, role,
                                          keypair, availability_zone,
                                          security_groups, block_devices,
                                          chef_path, subnet_id, dns_zones,
                                          platform, use_latest_ami)

    def configure(self):
        super(NginxServer, self).configure()

    @property
    def user_data(self):
        # read in userdata file
        user_data = None
        try:
            f = data_file('user_data_chef_provision')
            user_data = f.read()

            validation_key_path = os.path.expanduser('~/.chef/chef-validator.pem')
            validation_key_file = open(validation_key_path, 'r')
            validation_key = validation_key_file.read()

            return user_data.format(validation_key=validation_key)

        except IOError:
            # Handle error reading file
            pass
