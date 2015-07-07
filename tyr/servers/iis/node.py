from tyr.servers.server import Server


class IISNode(Server):

    SERVER_TYPE = 'web'

    AMI_NAME = ''

    IAM_ROLE_POLICIES = [
        'allow-describe-instances',
        'allow-describe-tags',
        'allow-describe-elbs',
        'allow-set-cloudwatch-alarms',
        'allow-remove-cloudwatch-alarms',
        'allow_deploy_web_updates',

    ]

    def __init__(self, group=None, server_type=None, instance_type=None,
                 environment=None, ami=None, region=None, role=None,
                 keypair=None, availability_zone=None, security_groups=None,
                 block_devices=None, chef_path=None, subnet_id=None,
                 dns_zones=None, desired_capacity=None, max_capacity=None,
                 min_capacity=None):

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
                                      block_devices=block_devices,
                                      chef_path=chef_path,
                                      subnet_id=subnet_id,
                                      dns_zones=dns_zones,
                                      desired_capacity=desired_capacity,
                                      max_capacity=max_capacity,
                                      min_capacity=min_capacity)

    def configure(self):
        super(IISNode, self).configure()

        env_prefix = self.environment[0]

        self.security_groups = [
            "management",
            "chef-client",
            "{0}-queueproc-jobs".format(env_prefix),
            "{0}-queues-jobs".format(env_prefix),
            "{0}-web".format(env_prefix),
            "{0}-nginx".format(env_prefix),
        ]

        self.ingress_groups_to_add = [
            "{0}-web".format(env_prefix),
            "{0}-nginx".format(env_prefix)
        ]

        self.IAM_ROLE_POLICIES.append('allow_web_initialization_{0}'
            .format(self.environment))
        self.IAM_ROLE_POLICIES.append('allow_outpost_sns_prod_{0}'
            .format(self.environment))
        self.IAM_ROLE_POLICIES.append('{0}-{1}-web'
            .format(self.environment))

        self.resolve_iam_role()
        self.launch_configuration()
        self.autoscale_group()
        self.ingress_rules()
