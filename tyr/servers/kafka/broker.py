from tyr.servers.server import Server


VOLUME_TYPES = ['standard', 'io1', 'gp2', 'sc1', 'st1']


class KafkaBroker(Server):

    SERVER_TYPE = 'kafka'

    CHEF_RUNLIST = ['role[RoleKafka]']

    IAM_ROLE_POLICIES = [
        'allow-describe-instances',
        'allow-describe-tags',
        'allow-volume-control'
    ]

    def __init__(self, group=None, server_type=None, instance_type=None,
                 environment=None, ami=None, region=None, role=None,
                 keypair=None, availability_zone=None, security_groups=None,
                 block_devices=None, chef_path=None, subnet_id=None,
                 dns_zones=None, platform=None, use_latest_ami=False,
                 ingress_groups_to_add=None, ports_to_authorize=None,
                 classic_link=False, add_route53_dns=True, chef_server_url=None,
                 volume_count=None, volume_size=None,
                 volume_type=None, logdir_root=None,
                 zookeeper_connection=None):

        if server_type is None:
            server_type = self.SERVER_TYPE

        self.volume_count = volume_count
        self.volume_size = volume_size
        self.volume_type = volume_type
        self.logdir_root = logdir_root
        self.zookeeper_connection = zookeeper_connection

        super(KafkaBroker, self).__init__(group, server_type, instance_type,
                                          environment, ami, region, role,
                                          keypair, availability_zone,
                                          security_groups, block_devices,
                                          chef_path, subnet_id, dns_zones,
                                          platform, use_latest_ami,
                                          ingress_groups_to_add,
                                          ports_to_authorize, classic_link,
                                          add_route53_dns, chef_server_url)

    def set_chef_attributes(self):
        super(KafkaBroker, self).set_chef_attributes()
        self.CHEF_ATTRIBUTES['role_kafka'] = {}
        self.CHEF_ATTRIBUTES['kafka'] = {}
        self.CHEF_ATTRIBUTES['kafka']['broker'] = {}
        self.CHEF_ATTRIBUTES['kafka']['broker']['zookeeper'] = {}

        if self.volume_count:
            if isinstance(self.volume_count, int):
                self.CHEF_ATTRIBUTES['role_kafka']['volume_count'] = self.volume_count
                self.log.info('Set role_kafka.volume_count to {}'.format(
                    self.volume_count)
                )
            else:
                raise TypeError('volume_count is of type {}. Expected integer'
                                .format(type(self.volume_count)))
        else:
            self.log.info('role_kafka.volume_count is not set. Using default.')

        if self.volume_size:
            if isinstance(self.volume_size, int):
                self.CHEF_ATTRIBUTES['role_kafka']['volume_size'] = self.volume_size
                self.log.info('Set role_kafka.volume_size to {}'
                              .format(self.volume_size))
            else:
                raise TypeError('volume_size is of type {}. Expected integer'
                                .format(type(self.volume_size)))
        else:
            self.log.info('role_kafka.volume_size is not set. Using default.')

        if self.volume_type:
            if self.volume_type in VOLUME_TYPES:
                self.CHEF_ATTRIBUTES['role_kafka']['volume_type'] = self.volume_type
                self.log.info('Set role_kafka.volume_type to {}'
                              .format(self.volume_type))
            else:
                raise ValueError('volume_type must be in {}. Received {}.'
                                 .format(VOLUME_TYPES, self.volume_type))
        else:
            self.log.info('role_kafka.volume_type is not set. Using default.')

        if self.logdir_root:
            self.CHEF_ATTRIBUTES['role_kafka']['logdir_root'] = self.logdir_root
            self.log.info('Set role_kafka.logdir_root to {}'
                          .format(self.logdir_root))
        else:
            self.log.info('role_kafka.logdir_root not set. Using default.')

        if self.zookeeper_connection:
            self.CHEF_ATTRIBUTES['kafka']['broker']['zookeeper']['connect'] = self.zookeeper_connection
            self.log.info('Set kafka.broker.zookeeper.connect to {}'
                          .format(self.zookeeper_connection))
        else:
            self.CHEF_ATTRIBUTES['kafka']['automatic_start'] = False
            self.log.warn('No zookeeper connection string given.'
                          'Kafka will not be started on boot.')

    def configure(self):
        super(KafkaBroker, self).configure()
        self.set_chef_attributes()

