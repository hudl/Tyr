from tyr.servers.server import Server
import sys


class AutomationAgent(Server):

    SERVER_TYPE = 'mongo'

    CHEF_RUNLIST = ['role[RoleMongo]']
    CHEF_MONGODB_TYPE = 'automation'

    IAM_ROLE_POLICIES = ['allow-volume-control']

    MONGO_CM_GROUPS = ['stage', 'foundation', 'teamsports', 'community']

    def __init__(self, group=None, server_type=None, instance_type=None,
                 environment=None, ami=None, region=None, role=None,
                 keypair=None, availability_zone=None,
                 security_groups=None, block_devices=None,
                 chef_path=None, subnet_id=None, dns_zones=None,
                 data_volume_size=None, data_volume_iops=None,
                 journal_volume_size=None, journal_volume_iops=None,
                 log_volume_size=None, log_volume_iops=None,
                 mongodb_automation_agent=True, mongodb_cm_group=None,
                 mongodb_type=None):

        self.data_volume_size = data_volume_size
        self.data_volume_iops = data_volume_iops
        self.journal_volume_size = journal_volume_size
        self.journal_volume_iops = journal_volume_iops
        self.log_volume_size = log_volume_size
        self.log_volume_iops = log_volume_iops
        self.mongodb_automation_agent = mongodb_automation_agent
        self.mongodb_cm_group = mongodb_cm_group
        self.mongodb_type = mongodb_type

        if server_type is None:
            server_type = self.SERVER_TYPE

        super(AutomationAgent, self).__init__(group, server_type,
                                              instance_type, environment, ami,
                                              region, role, keypair,
                                              availability_zone,
                                              security_groups, block_devices,
                                              chef_path, subnet_id, dns_zones)

    def validate_ebs_volume(self, volume_type):
        volume_size = 0
        volume_iops = 0

        if volume_type == 'data':
            volume_size = self.data_volume_size
            volume_iops = self.data_volume_iops
        elif volume_type == 'journal':
            volume_size = self.journal_volume_size
            volume_iops = self.journal_volume_iops
        elif volume_type == 'log':
            volume_size = self.log_volume_size
            volume_iops = self.log_volume_iops
        else:
            msg = 'Unable to validate drive type: {volume_type}'.format(
                volume_type=volume_type)
            self.log.critical(msg)
            sys.exit(1)

        if volume_size is None:
            msg = 'No {volume_type} volume size provided'.format(
                volume_type=volume_type)
            self.log.warn(msg)
            volume_size = self.set_default_volume_size(volume_type)
        elif volume_size < 1:
            self.log.critical('The {volume_type} volume size is less than 1'.
                              format(volume_type=volume_type))
            sys.exit(1)

        msg = 'Using {volume_type} volume size "{size}"'.format(
            volume_type=volume_type, size=volume_size)
        self.log.info(msg)

        if volume_iops is None:
            msg = 'No {volume_type} volume iops provided'.format(
                volume_type=volume_type)
            self.log.warn(msg)

            volume_iops = self.set_default_volume_iops(volume_type)

        msg = 'Using {volume_type} volume iops "{iops}"'.format(
            volume_type=volume_type, iops=volume_iops)
        self.log.info(msg)

        iops_size_ratio = volume_iops/volume_size

        self.log.info('The IOPS to Size ratio is "{ratio}"'.format(
            ratio=iops_size_ratio))

        if iops_size_ratio > 30:
            self.log.critical('The IOPS to Size ratio is greater than 30')
            sys.exit(1)

    def set_default_volume_size(self, volume_type):
        if volume_type == 'data':
            self.data_volume_size = 200
            size = 200
        elif volume_type == 'journal':
            self.journal_volume_size = 50
            size = 50
        elif volume_type == 'log':
            self.log_volume_size = 10
            size = 10

        return size

    def set_default_volume_iops(self, volume_type):
        if volume_type == 'data':
            if self.environment == 'prod':
                self.data_volume_iops = 2000
            else:
                self.data_volume_iops = 0
            default_volume_iops = self.data_volume_iops
        elif volume_type == 'journal':
            if self.environment == 'prod':
                self.journal_volume_iops = 500
            else:
                self.journal_volume_iops = 0
            default_volume_iops = self.journal_volume_iops
        elif volume_type == 'log':
            if self.environment == 'prod':
                self.log_volume_iops = 200
            else:
                self.log_volume_iops = 0
            default_volume_iops = self.log_volume_iops

        return default_volume_iops

    def configure(self):

        super(AutomationAgent, self).configure()

        if self.environment == 'prod':
            self.ebs_optimized = True

        if self.environment == "prod":
            self.IAM_ROLE_POLICIES.append('allow-mongo-backup-snapshot')
        elif self.environment == "stage":
            self.IAM_ROLE_POLICIES.append('allow-mongo-snapshot-cleanup')

        self.resolve_iam_role()

        # This is just a temporary fix to override the default security
        # groups for MongoDB nodes until the security_groups argument
        # is removed.

        self.security_groups = [
            'management',
            'chef-nodes',
            self.envcl,
            '{env}-mongo-management'.format(env=self.environment[0])
        ]

        self.resolve_security_groups()

        self.validate_ebs_volume('data')
        self.validate_ebs_volume('journal')
        self.validate_ebs_volume('log')

        # Validate the Mongo CM Group if the Automation agent is being
        # installed.
        if self.mongodb_cm_group in self.MONGO_CM_GROUPS:
            self.log.info('Using Mongo CM Group {group}'.format(
                group=self.mongodb_cm_group))
        else:
            error_msg = ("Not a valid Mongo CM Group!\n"
                         "Must be: stage, teamsports, foundation, or "
                         "community"
                         )
            self.log.critical(error_msg)
            raise error_msg

    def determine_ebs_volumes(self):
        ebs_volumes = []

        if self.mongodb_type == 'router' or \
                self.mongodb_type == 'mongos':
            ebs_volumes = [
                {
                    'user': 'mongod',
                    'group': 'mongod',
                    'size': 5,
                    'iops': 0,
                    'device': '/dev/xvdf',
                    'mount': '/volr'
                }]
        else:
            ebs_volumes = [
                {
                    'user': 'mongod',
                    'group': 'mongod',
                    'size': self.data_volume_size,
                    'iops': self.data_volume_iops,
                    'device': '/dev/xvdf',
                    'mount': '/volr'
                },
                {
                    'user': 'mongod',
                    'group': 'mongod',
                    'size': self.journal_volume_size,
                    'iops': self.journal_volume_iops,
                    'device': '/dev/xvdg',
                    'mount': '/volr/journal'
                },
                {
                    'user': 'mongod',
                    'group': 'mongod',
                    'size': self.log_volume_size,
                    'iops': self.log_volume_iops,
                    'device': '/dev/xvdh',
                    'mount': '/mongologs',
                }]

        return ebs_volumes

    def bake(self):

        super(AutomationAgent, self).bake()

        with self.chef_api:

            self.chef_node.attributes.set_dotted('mongodb.node_type',
                                                 self.CHEF_MONGODB_TYPE)
            self.log.info('Set the MongoDB node type to "{type_}"'.format(
                type_=self.CHEF_MONGODB_TYPE))

            ebs_volumes = self.determine_ebs_volumes()
            self.chef_node.attributes.set_dotted('hudl_ebs.volumes',
                                                 ebs_volumes)
            self.log.info('Configured the hudl_ebs.volumes attribute')

            self.chef_node.attributes.set_dotted(
                'mongodb.automation_agent.install',
                self.mongodb_automation_agent)
            self.log.info('Installing the CM Automation Agent')

            self.chef_node.attributes.set_dotted(
                'mongodb.automation_agent.mongo_cm_group',
                self.mongodb_cm_group)
            self.log.info('Using Mongo CM Group "{group}"'.format(
                group=self.mongodb_cm_group))

            self.chef_node.save()
            self.log.info('Saved the Chef Node configuration')
