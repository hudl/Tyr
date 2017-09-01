from tyr.servers.server import Server
from tyr.helpers import data_file


class IISNode(Server):

    SERVER_TYPE = 'web'

    AMI_NAME = None
    # Do not run chef
    CHEF_RUNLIST = []

    IAM_MANAGED_POLICIES = [
        'hudl-webserver-generic',
        'aws-hudl-base',
        'ChefAllowAccess'
    ]

    IAM_ROLE_POLICIES = [

    ]

    def __init__(self, group=None, server_type=None, instance_type=None,
                 environment=None, ami=None, region=None, role=None,
                 block_devices=None, keypair=None, availability_zone=None, security_groups=None,
                 subnet_id=None, platform="Windows", use_latest_ami=False,
                 mongos_service="no_mongos", mongo_servers=""):

        if server_type is None:
            server_type = self.SERVER_TYPE

        super(IISNode, self).__init__(group=group, server_type=server_type,
                                      instance_type=instance_type,
                                      environment=environment,
                                      ami=ami,
                                      region=region,
                                      role=role,
                                      block_devices=block_devices,
                                      keypair=keypair,
                                      availability_zone=availability_zone,
                                      security_groups=security_groups,
                                      subnet_id=subnet_id,
                                      platform=platform,
                                      use_latest_ami=use_latest_ami)                                      

        self.mongos_service = mongos_service
        self.mongo_servers = mongo_servers


    def configure(self):        
        super(IISNode, self).configure()

        self.IAM_MANAGED_POLICIES.append('hudl-webserver-{environment}-multiverse')
        self.security_groups.extend(['{env}-hudl-{group}', '{env}-mv-web'])        
        self.ports_to_authorize.extend([9000, 9001, 8095, 8096])        
        self.ingress_groups_to_add.extend(['{env}-web','{env}-nginx','{env}-queueproc-jobs'])
        self.classic_link_vpc_security_groups = []

        mongos_options = ("mongos_host", "no_mongos", "mongos_service")
        if self.mongos_service and self.mongos_service not in mongos_options:
            raise ValueError('mongos_service value {} not in options {}'.format(
                self.mongos_service, mongos_options
            ))

    @property
    def user_data(self):
        # read in userdata file
        user_data = None
        try:
            f = data_file('user_data_base_fetch_s3.ps2')
            user_data = f.read()
        except IOError:
            self.log.critical('No user info found, exiting!')
            exit(1)
        return user_data
