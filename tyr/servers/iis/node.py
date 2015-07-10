from tyr.servers.server import Server


class IISNode(Server):

    SERVER_TYPE = 'web'

    AMI_NAME = ''
    # Do not run chef
    CHEF_RUNLIST = []

    IAM_ROLE_POLICIES = [
        'allow-describe-instances',
        'allow-describe-tags',
        'allow-describe-elbs',
        'allow-set-cloudwatch-alarms',
        'allow-remove-cloudwatch-alarms',
        'allow-deploy-web-updates',

    ]

    def __init__(self, group=None, server_type=None, instance_type=None,
                 environment=None, ami=None, region=None, role=None,
                 keypair=None, availability_zone=None, security_groups=None,
                 subnet_id=None):

        if server_type is None:
            server_type = self.SERVER_TYPE

        super(IISNode, self).__init__(group=group, server_type=server_type,
                                      instance_type=instance_type,
                                      environment=environment,
                                      ami=ami,
                                      region=region,
                                      role=role,
                                      keypair=keypair,
                                      availability_zone=availability_zone,
                                      security_groups=security_groups,
                                      subnet_id=subnet_id,
                                      dns_zones=None)

        env_prefix = self.environment[0]

        self.security_groups = [
            "{0}-management".format(env_prefix),
            "{0}-mv-web".format(env_prefix),
            "{0}-{1}-web".format(env_prefix, self.group),
            "{0}-hudl-{1}".format(env_prefix, self.group),
            "{0}-web".format(env_prefix),
        ]

        self.ingress_groups_to_add = [
            "{0}-web".format(env_prefix),
            "{0}-nginx".format(env_prefix)
        ]

#        self.user_data = "{'bucket':'hudl-config','key':'" + self.environment[0] + "-mv-web/init.config.json','mongos': '$Mongos', 'mongoServers': '$MongoServers'}"

        self.ports_to_authorize = [9000, 9001, 8095, 8096]

        self.IAM_ROLE_POLICIES.append('allow-web-initialization-{0}'
            .format(self.environment))
        self.IAM_ROLE_POLICIES.append('allow-outpost-sns-{0}'
            .format(self.environment))
        #self.IAM_ROLE_POLICIES.append('{0}-{1}-web'
        #    .format(self.environment, self.group))

    def configure(self):
        super(IISNode, self).establish_logger()
        super(IISNode, self).configure()

        self.resolve_iam_role()
        self.ingress_rules()
