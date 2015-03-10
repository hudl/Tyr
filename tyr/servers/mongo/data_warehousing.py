from tyr.servers import Server
import logging

class MongoDataWarehousingNode(Server):

    log = logging.getLogger('Servers.MongoDataWarehousingNode')
    log.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
            '%(asctime)s [%(name)s] %(levelname)s: %(message)s',
            datefmt = '%H:%M:%S')
    ch.setFormatter(formatter)
    log.addHandler(ch)

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
                                            role_policies)

        self.replica_set = replica_set
        self.chef_path = chef_path
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

        if self.replica_set is None:
            self.log.warn('No replica set provided')
            self.replica_set = 1

        self.log.info('Using replica set "{set}"'.format(set=self.replica_set))

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

    @property
    def name(self):

        try:
            return self.unique_name
        except Exception:
            pass

        name = self.build_name(
            template='{envcl}-rs{set}-{zone}-fulla',
            supplemental={
                'set': self.replica_set,
                'zone': self.availability_zone[-1:]
            },
            search_prefix='{envcl}-rs{set}-{zone}-')

        self.unique_name = name

        self.log.info('Using node name {name}'.format(name=name))

        return name

    def bake(self):

        super(MongoDataNode, self).bake()

        chef_api = self.chef_api

        node = chef.Node.create(self.name, api=chef_api)

        self.log.info('Created new Chef Node "{node}"'.format(
                        node = self.name))

        node.chef_environment = self.environment

        self.log.info('Set the Chef Environment to "{env}"'.format(
                        env = node.chef_environment))


