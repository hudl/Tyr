from tyr.servers.server import Server
import json


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
                 subnet_id=None, mongos_service="MongosHost",
                 mongo_servers=None):

        if server_type is None:
            server_type = self.SERVER_TYPE

        self.mongos_service = mongos_service
        self.mongo_servers = mongo_servers

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
                                      dns_zones=None,
                                      add_route53_dns=False)

        env_prefix = self.environment[0]

        self.security_groups = [
            "{0}-management".format(env_prefix),
            "{0}-mv-web".format(env_prefix),
            "{0}-{1}-web".format(env_prefix, self.group),
            "{0}-hudl-{1}".format(env_prefix, self.group),
            "{0}-web".format(env_prefix),
        ]

        self.classic_link_vpc_security_groups = [
            "{0}-management".format(env_prefix),
            "{0}-mv-web".format(env_prefix),
            "{0}-{1}-web".format(env_prefix, self.group),
            "{0}-hudl-{1}".format(env_prefix, self.group),
        ]

        self.ingress_groups_to_add = [
            "{0}-web".format(env_prefix),
            "{0}-nginx".format(env_prefix),
            "{0}-queueproc-jobs".format(env_prefix)
        ]

        if self.mongos_service:
            mongo_ops = ("MongosHost", "Disabled", "MongosService")
            if self.mongos_service not in mongo_ops:
                raise ValueError(
                    "Mongo service name must be one of: {0}".format(
                        mongo_ops))

        self.ports_to_authorize = [9000, 9001, 8095, 8096]

        self.IAM_ROLE_POLICIES.append('allow-web-initialization-{0}'
            .format(self.environment))
        self.IAM_ROLE_POLICIES.append('allow-outpost-sns-{0}'
            .format(self.environment))

    def configure(self):
        super(IISNode, self).establish_logger()
        super(IISNode, self).configure()

    @property
    def user_data(self):
        data = {"bucket": "hudl-config",
                "key": "{0}-mv-web/init.config.json".format(
                    self.environment[0]),
                "mongos": self.mongos_service,
                "mongoServers": self.mongo_servers
                }
        ud = json.dumps(data)
        self.log.info("Setting user data to: {0}".format(ud))
        return ud
