from tyr.servers.server import Server
import chef
import requests
import time
import os.path

class NginxServer(Server):

    SERVER_TYPE = 'nginx'

    CHEF_RUNLIST=['role[RoleNginx]']


    IAM_ROLE_POLICIES = [
        'allow-describe-instances',
        'allow-describe-tags',
        'allow-describe-elbs',
        'allow-get-nginx-config'
    ]

    def __init__(self, group=None, server_type=None, instance_type=None,
                    environment=None, ami=None, region=None, role=None,
                    keypair=None, availability_zone=None, security_groups=None,
                    block_devices=None, chef_path=None, subnet_id=None,
                    dns_zones=None):

        if server_type is None: server_type = self.SERVER_TYPE

        super(NginxServer, self).__init__(group, server_type, instance_type,
                                    environment, ami, region, role,
                                    keypair, availability_zone,
                                    security_groups, block_devices,
                                    chef_path, subnet_id, dns_zones)

    def configure(self):

        super(NginxServer, self).configure()

        if self.environment == 'stage':
            self.IAM_ROLE_POLICIES.append('allow-modify-nginx-elbs-stage')
        elif self.environment == 'prod':
            self.IAM_ROLE_POLICIES.append('allow-modify-nginx-elbs-prod')
        self.resolve_iam_role()
