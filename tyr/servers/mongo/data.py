from tyr.servers import Server
import logging
import os
import chef
import sys
import json

class MongoDataNode(Server):

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
            template='{envcl}-rs{set}-{zone}-{index}',
            supplemental={
                'set': self.replica_set,
                'zone': self.availability_zone[-1:]
            },
            search_prefix='{envcl}-rs{set}-{zone}-')

        self.unique_name = name

        self.log.info('Using node name {name}'.format(name=name))

        return name

    def run_mongo(self, command):

        template = 'mongo --port 27018 --eval "JSON.stringify({command})"'

        command = template.format(command = command)

        r = self.run(command)

        return json.loads(r['out'].split('\n')[2])

    def bake(self):

        super(MongoDataNode, self).bake()

        chef_api = self.chef_api

        node = chef.Node.create(self.name, api=chef_api)

        self.log.info('Created new Chef Node "{node}"'.format(
                        node = self.name))

        node.chef_environment = self.environment

        self.log.info('Set the Chef Environment to "{env}"'.format(
                        env = node.chef_environment))

        if node.chef_environment == 'prod':
            node.attributes.set_dotted('hudl_ebs.volumes', [
                {
                    'user': 'mongod',
                    'group': 'mongod',
                    'size': 10,
                    'iops': 0,
                    'device': '/dev/xvdg',
                    'mount': '/volr/journal'},
                {
                    'user': 'mongod',
                    'group': 'mongod',
                    'size': self.data_volume_size,
                    'iops': self.data_volume_iops,
                    'device': '/dev/xvdf',
                    'mount': '/volr'
                }
            ])
        else:
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

        cluster_name = self.cluster.split('-')[0]
        replica_set = 'rs' + str(self.replica_set)

        node.attributes.set_dotted('mongodb.cluster_name', cluster_name)
        self.log.info('Set the cluster name to "{name}"'.format(
                                    name = cluster_name))

        node.attributes.set_dotted('mongodb.replicaset_name', replica_set)
        self.log.info('Set the replica set name to "{name}"'.format(
                                    name = replica_set))

        node.attributes.set_dotted('mongodb.node_type', 'data')
        self.log.info('Set the MongoDB node type to "data"')

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

    def autorun(self):

        super(MongoDataNode, self).autorun()
