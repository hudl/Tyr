from tyr.servers.server import Server
from tyr.helpers import data_file


class IISThorNode(Server):

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

        self.mongos_service = mongos_service
        self.mongo_servers = mongo_servers

        super(IISThorNode, self).__init__(group=group, server_type=server_type,
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
                                      use_latest_ami=use_latest_ami,
                                      dns_zones=None,
                                      add_route53_dns=False)

        env_prefix = self.environment[0]

        if self.security_groups is None:
            self.security_groups = [
                "management",
                "{env}-mv-web".format(env=env_prefix),
                "{env}-{grp}-web".format(env=env_prefix, grp=self.group),
                "{env}-hudl-{grp}".format(env=env_prefix, grp=self.group),
                "chef-nodes",
            ]

        self.classic_link_vpc_security_groups = [
        ]

        self.ingress_groups_to_add = [ ]

        if self.mongos_service:
            mongo_ops = ("mongos_host", "no_mongos", "mongos_service")
            if self.mongos_service not in mongo_ops:
                raise ValueError(
                    "Mongo service name must be one of: {0}".format(
                        mongo_ops))

        self.ports_to_authorize = [9000, 9001, 8095, 8096]
        self.IAM_MANAGED_POLICIES.append('hudl-webserver-{environment}-multiverse')

    def configure(self):
        super(IISThorNode, self).establish_logger()
        super(IISThorNode, self).configure()

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
