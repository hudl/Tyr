from tyr.servers.server import Server
from tyr.files.user_data import generic_user_data
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
                    block_devices=None, chef_path=None):

        if server_type is None: server_type = self.SERVER_TYPE

        super(NginxServer, self).__init__(group, server_type, instance_type,
                                    environment, ami, region, role,
                                    keypair, availability_zone,
                                    security_groups, chef_path)

    def configure(self):

        super(NginxServer, self).configure()

        if self.environment == 'stage':
            self.IAM_ROLE_POLICIES.append('allow-update-route53-stage')
            self.IAM_ROLE_POLICIES.append('allow-modify-nginx-elbs-stage')
        elif self.environment == 'prod':
            self.IAM_ROLE_POLICIES.append('allow-update-route53-prod')
            self.IAM_ROLE_POLICIES.append('allow-modify-nginx-elbs-prod')
        self.resolve_iam_role()

    def bake(self):

        chef_path = os.path.expanduser(self.chef_path)
        self.chef_api = chef.autoconfigure(chef_path)

        with self.chef_api:
            try:
                node = chef.Node(self.name)
                node.delete()

                self.log.info('Removed previous chef node "{node}"'.format(
                                node = self.name))
            except chef.exceptions.ChefServerNotFoundError:
                pass
            except Exception as e:
                self.log.error(str(e))
                raise e

            try:
                client = chef.Client(self.name)
                client = client.delete()

                self.log.info('Removed previous chef client "{client}"'.format(
                                client = self.name))
            except chef.exceptions.ChefServerNotFoundError:
                pass
            except Exception as e:
                self.log.error(str(e))
                raise e

    @property
    def user_data(self):

        template = generic_user_data

        validation_key_path = os.path.expanduser('~/.chef/chef-validator.pem')
        validation_key_file = open(validation_key_path, 'r')
        validation_key = validation_key_file.read()

        return template.format(hostname = self.hostname,
                                fqdn = self.hostname,
                                validation_key = validation_key,
                                chef_server = 'http://chef.app.hudl.com/',
                                logfile = '/var/log/chef-client.log')

    def autorun(self):

        self.establish_logger()
        self.configure()
        self.launch()
        self.tag()
        self.bake()
