from tyr.servers import Server
import logging
import os
import chef

class MongoDataWarehousingNode(Server):

    NAME_TEMPLATE = '{envcl}-rs{replica_set}-{zone}-fulla',
    NAME_SEARCH_PREFIX = '{envcl}-rs{replica_set}-{zone}-'
    NAME_AUTO_INDEX=False

    def __init__(self, dry = None, verbose = None, size = None, cluster = None,
                    environment = None, ami = None, region = None, role = None,
                    keypair = None, availability_zone = None, chef_path = None,
                    security_groups = None, block_devices = None,
                    replica_set = None, data_volume_size=None,
                    role_policies=None):

        super(MongoDataWarehousingNode, self).__init__(dry, verbose, size,
                                                        cluster, ami, role,
                                                        environment, region,
                                                        keypair,
                                                        availability_zone,
                                                        security_groups,
                                                        block_devices,
                                                        role_policies)

        self.replica_set = replica_set
        self.chef_path = chef_path
        self.data_volume_size = data_volume_size

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
}""",
                'allow-upload-to-s3-fulla': """{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "Stmt1421959713000",
      "Effect": "Allow",
      "Action": [
        "s3:AbortMultipartUpload",
        "s3:CreateBucket",
        "s3:ListBucketMultipartUploads",
        "s3:PutObject"
      ],
      "Resource": [
        "arn:aws:s3:::ds-fulla/*"
      ]
    }
  ]
}""",
                'allow-download-scripts-s3-fulla': """{
   "Version":"2012-10-17",
   "Statement":[
       {
           "Sid":"Stmt1408567829000",
           "Effect":"Allow",
           "Action":[
               "s3:ListBucket"
           ],
           "Resource":[
               "arn:aws:s3:::ds-fulla/*"
           ]
       },
       {
           "Sid":"Stmt1408567479000",
           "Effect":"Allow",
           "Action":[
               "s3:GetObject"
           ],
           "Resource":[
               "arn:aws:s3:::ds-fulla/*"
           ]
       }
   ]
}"""
            }

        super(MongoDataWarehousingNode, self).configure()

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

        cluster_name = self.cluster.split('-')[0]
        replica_set = 'rs' + str(self.replica_set)

        node.attributes.set_dotted('mongodb.cluster_name', cluster_name)
        self.log.info('Set the cluster name to "{name}"'.format(
                                    name = cluster_name))

        node.attributes.set_dotted('mongodb.replicaset_name', replica_set)
        self.log.info('Set the replica set name to "{name}"'.format(
                                    name = replica_set))

        node.attributes.set_dotted('mongodb.node_type', 'data_warehousing')
        self.log.info('Set the MongoDB node type to "data_warehousing"')

        runlist = ['role[RoleMongo]']

        if node.chef_environment == 'prod':
            pass
        else:
            runlist.append('role[RoleSumoLogic]')

        node.run_list = runlist
        self.log.info('Set the run list to "{runlist}"'.format(
                                        runlist = node.run_list))

        node.save(api=chef_api)
        self.log.info('Saved the Chef Node configuration')

