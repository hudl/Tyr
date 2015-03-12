from tyr.servers import Server
import logging
import chef

class MongoArbiterNode(Server):

    NAME_TEMPLATE = '{envcl}-rs{replica_set}-{zone}-arb'
    NAME_SEARCH_PREFIX = '{envcl}-rs{replica_set}-{zone}-'
    NAME_AUTO_INDEX=False

    CHEF_RUNLIST = ['role[RoleMongo]']

    def __init__(self, dry = None, verbose = None, size = None, cluster = None,
                    environment = None, ami = None, region = None, role = None,
                    keypair = None, availability_zone = None, chef_path = None,
                    security_groups = None, block_devices = None,
                    replica_set = None, role_policies=None):

        super(MongoArbiterNode, self).__init__(dry, verbose, size, cluster,
                                                environment, ami, region, role,
                                                keypair, availability_zone,
                                                security_groups, block_devices,
                                                role_policies)

        self.replica_set = replica_set
        self.chef_path = chef_path

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

        super(MongoArbiterNode, self).configure()

        if self.replica_set is None:
            self.log.warn('No replica set provided')
            self.replica_set = 1

        self.log.info('Using replica set {set}'.format(set = self.replica_set))

    def bake(self):

        super(MongoArbiterNode, self).bake()

        chef_api = self.chef_api
        node = self.chef_node

        node.attributes.set_dotted('hudl_ebs.volumes', [
            {
                'user': 'mongod',
                'group': 'mongod',
                'size': 1,
                'iops': 0,
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

        node.attributes.set_dotted('mongodb.node_type', 'arbiter')
        self.log.info('Set the MongoDB node type to "arbiter"')

        if node.chef_environment == 'prod':
            node.run_list.append('role[RoleSumoLogic]')

        self.log.info('Set the run list to "{runlist}"'.format(
                                        runlist = node.run_list))

        node.attributes.set_dotted('mongodb.config.smallfiles', True)

        node.save(api=chef_api)
        self.log.info('Saved the Chef Node configuration')
