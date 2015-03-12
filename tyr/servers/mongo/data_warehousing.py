from member import MongoReplicaSetMember

class MongoDataWarehousingNode(MongoReplicaSetMember):

    NAME_TEMPLATE = '{envcl}-rs{replica_set}-{zone}-fulla'
    NAME_SEARCH_PREFIX = '{envcl}-rs{replica_set}-{zone}-'
    NAME_AUTO_INDEX=False

    CHEF_RUNLIST = ['role[RoleMongo]']
    CHEF_MONGODB_TYPE = 'data_warehousing'

    def __init__(self, dry = None, verbose = None, size = None, cluster = None,
                    environment = None, ami = None, region = None, role = None,
                    keypair = None, availability_zone = None, chef_path = None,
                    security_groups = None, block_devices = None,
                    replica_set = None, data_volume_size=None):

        super(MongoDataWarehousingNode, self).__init__(dry, verbose, size,
                                                        cluster, ami, role,
                                                        environment, region,
                                                        keypair,
                                                        availability_zone,
                                                        security_groups,
                                                        block_devices,
                                                        replica_set)

        self.data_volume_size = data_volume_size

    def configure(self):

        self.role_policies = [
            'allow-volume-control',
            'allow-upload-to-s3-fulla',
            'allow-download-scripts-s3-fulla'
        ]

        super(MongoDataWarehousingNode, self).configure()

        if self.data_volume_size is None:
            self.log.warn('No data volume size provided')
            self.data_volume_size = 400
        elif self.data_volume_size < 1:
            self.log.critical('The data volume size is less than 1')
            sys.exit(1)

        self.log.info('Using data volume size "{size}"'.format(
                                            size = self.data_volume_size))

    def bake(self):

        super(MongoDataWarehousingNode, self).bake()

        chef_api = self.chef_api
        node = self.chef_node

        node.attributes.set_dotted('hudl_ebs.volumes', [
            {
                'user': 'mongod',
                'group': 'mongod',
                'size': 10,
                'iops': 0,
                'device': '/dev/xvdg',
                'mount': '/volr/journal'
            },
            {
                'user': 'mongod',
                'group': 'mongod',
                'size': self.data_volume_size,
                'iops': 0,
                'device': '/dev/xvdf',
                'mount': '/volr'
            },
            {
                'user': 'mongod',
                'group': 'mongod',
                'size': self.data_volume_size,
                'iops': 0,
                'device': '/dev/xvde',
                'mount': '/fulla'
            }
        ])

        self.log.info('Configured the hudl_ebs.volumes attribute')

        node.save(api=chef_api)
        self.log.info('Saved the Chef Node configuration')
