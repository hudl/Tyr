from member import MongoReplicaSetMember
import sys

class MongoDataNode(MongoReplicaSetMember):

    NAME_TEMPLATE = '{envcl}-rs{replica_set}-{location}-{index}'
    NAME_SEARCH_PREFIX = '{envcl}-rs{replica_set}-{location}-'
    NAME_AUTO_INDEX=True

    CHEF_RUNLIST = ['role[RoleMongo]']
    CHEF_MONGODB_TYPE = 'data'

    def __init__(self, group = None, server_type = None, instance_type = None,
                    environment = None, ami = None, region = None, role = None,
                    keypair = None, availability_zone = None,
                    security_groups = None, block_devices = None,
                    chef_path = None, replica_set = None,
                    data_volume_size = None, data_volume_iops = None,
                    mongodb_version = None, subnet_id = None):

        super(MongoDataNode, self).__init__(group, server_type, instance_type,
                                            environment, ami, region, role,
                                            keypair, availability_zone,
                                            security_groups, block_devices,
                                            chef_path, replica_set,
                                            mongodb_version, subnet_id)

        self.data_volume_size = data_volume_size
        self.data_volume_iops = data_volume_iops

    def configure(self):

        super(MongoDataNode, self).configure()

        if self.environment == 'stage':
            self.IAM_ROLE_POLICIES.append('allow-download-script-s3-stage-updater')
            self.resolve_iam_role()

        if self.data_volume_size is None:
            self.log.warn('No data volume size provided')
            self.data_volume_size = 400
        elif self.data_volume_size < 1:
            self.log.critical('The data volume size is less than 1')
            sys.exit(1)

        self.log.info('Using data volume size "{size}"'.format(
                                            size = self.data_volume_size))

        if self.data_volume_iops is None:
            self.log.warn('No data volume iops provided')
            if self.environment == 'prod':
                self.data_volume_iops = 3000
            else:
                self.data_volume_iops = 0

        self.log.info('Using data volume iops "{iops}"'.format(
                                            iops = self.data_volume_iops))

        iops_size_ratio = self.data_volume_iops/self.data_volume_size

        self.log.info('The IOPS to Size ratio is "{ratio}"'.format(
                                            ratio = iops_size_ratio))

        if iops_size_ratio > 30:
            self.log.critical('The IOPS to Size ratio is greater than 30')
            sys.exit(1)

    def bake(self):

        super(MongoDataNode, self).bake()

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
                    'iops': self.data_volume_iops,
                    'device': '/dev/xvdf',
                    'mount': '/volr'
                }
            ])

            self.log.info('Configured the hudl_ebs.volumes attribute')

            self.chef_node.save()
            self.log.info('Saved the Chef Node configuration')
