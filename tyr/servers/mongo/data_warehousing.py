from member import MongoReplicaSetMember

class MongoDataWarehousingNode(MongoReplicaSetMember):

    NAME_TEMPLATE = '{envcl}-rs{replica_set}-{zone}-fulla'
    NAME_SEARCH_PREFIX = '{envcl}-rs{replica_set}-{zone}-'
    NAME_AUTO_INDEX=False

    IAM_ROLE_POLICIES = [
        'allow-volume-control',
        'allow-upload-to-s3-fulla',
        'allow-download-scripts-s3-fulla'
    ]

    CHEF_RUNLIST = ['role[RoleMongo]']
    CHEF_MONGODB_TYPE = 'data_warehousing'

    def __init__(self, group = None, server_type = None, instance_type = None,
                    environment = None, ami = None, region = None, role = None,
                    keypair = None, availability_zone = None,
                    security_groups = None, block_devices = None,
                    chef_path = None, replica_set = None,
                    data_volume_size = None, mongodb_version = None,
                    subnet_id = None):

        super(MongoDataWarehousingNode, self).__init__(group, server_type,
                                                        instance_type,
                                                        environment,  ami,
                                                        region, role, keypair,
                                                        availability_zone,
                                                        security_groups,
                                                        block_devices,
                                                        chef_path,
                                                        replica_set,
                                                        mongodb_version,
                                                        subnet_id)

        self.data_volume_size = data_volume_size

    def configure(self):

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

        with self.chef_api:

            self.chef_node.attributes.set_dotted('hudl_ebs.volumes', [
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
                    'user': 'ec2-user',
                    'group': 'ec2-user',
                    'size': self.data_volume_size,
                    'iops': 0,
                    'device': '/dev/xvde',
                    'mount': '/fulla'
                }
            ])

            self.log.info('Configured the hudl_ebs.volumes attribute')

            self.chef_node.save()
            self.log.info('Saved the Chef Node configuration')
