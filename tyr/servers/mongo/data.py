from member import MongoReplicaSetMember
import sys

class MongoDataNode(MongoReplicaSetMember):

    NAME_TEMPLATE = '{envcl}-rs{replica_set}-{zone}-{index}'
    NAME_SEARCH_PREFIX = '{envcl}-rs{replica_set}-{zone}-'
    NAME_AUTO_INDEX=True

    CHEF_RUNLIST = ['role[RoleMongo]']
    CHEF_MONGODB_TYPE = 'data'

    def __init__(self, dry = None, verbose = None, size = None, cluster = None,
                    environment = None, ami = None, region = None, role = None,
                    keypair = None, availability_zone = None, chef_path = None,
                    security_groups = None, block_devices = None,
                    replica_set = None, data_volume_size=None,
                    data_volume_iops=None, role_policies=None):

        super(MongoDataNode, self).__init__(dry, verbose, size, cluster,
                                            environment, ami, region, role,
                                            keypair, availability_zone,
                                            security_groups, block_devices,
                                            role_policies, replica_set)

        self.data_volume_size = data_volume_size
        self.data_volume_iops = data_volume_iops

    def configure(self):

        if self.role_policies is None:

            self.role_policies = {
                'allow-volume-control': """{
    "Statement": [
        {
            "Sid": "Stmt1367531520227",
            "Action": [
                "ec2:AttachVolume",
                "ec2:CreateVolume",
                "ec2:DescribeVolumeAttribute",
                "ec2:DescribeVolumeStatus",
                "ec2:DescribeVolumes",
                "ec2:EnableVolumeIO",
                "ec2:DetachVolume"
             ],
             "Effect": "Allow",
             "Resource": [
                "*"
             ]
        }
     ]
}"""
            }

        super(MongoDataNode, self).configure()

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
                'iops': self.data_volume_iops,
                'device': '/dev/xvdf',
                'mount': '/volr'
            }
        ])

        self.log.info('Configured the hudl_ebs.volumes attribute')

        node.save(api=chef_api)
        self.log.info('Saved the Chef Node configuration')
