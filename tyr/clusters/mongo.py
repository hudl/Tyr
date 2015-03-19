import logging
from tyr.servers.mongo import MongoDataNode, MongoArbiterNode
import time
import json

class MongoCluster(object):

    log = logging.getLogger('Clusters.Mongo')
    log.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
            '%(asctime)s [%(name)s] %(levelname)s: %(message)s',
            datefmt = '%H:%M:%S')
    ch.setFormatter(formatter)
    log.addHandler(ch)

    def __init__(self, group = None, server_type = None, instance_type = None,
                    environment = None, ami = None, region = None, role = None,
                    keypair = None, chef_path = None, replica_set = None,
                    security_groups = None, block_devices = None,
                    data_volume_size=None, data_volume_iops=None,
                    data_nodes=None, mongodb_version=None):

        self.nodes = []

        self.instance_type = instance_type
        self.group = group
        self.server_type = server_type
        self.environment = environment
        self.ami = ami
        self.region = region
        self.role = role
        self.keypair = keypair
        self.chef_path = chef_path
        self.security_groups = security_groups
        self.block_devices = block_devices
        self.replica_set = replica_set
        self.data_volume_size = data_volume_size
        self.data_volume_iops = data_volume_iops
        self.data_nodes = data_nodes
        self.mongodb_version = mongodb_version

    def provision(self):

        zones = 'cde'

        self.log.info('Building availability zone list')

        while len(zones) < (self.data_nodes+1):

            zones += zones

        self.log.info('Provisioning MongoDB Data Nodes')

        i = 0

        for i in range(self.data_nodes):

            node = MongoDataNode(group = self.group, server_type = self.server_type,,
                                    instance_type = self.instance_type,
                                    environment = self.environment,
                                    ami = self.ami, region = self.region,
                                    role = self.role, keypair = self.keypair,
                                    chef_path = self.chef_path,
                                    replica_set = self.replica_set,
                                    security_groups = self.security_groups,
                                    block_devices = self.block_devices,
                                    availability_zone = zones[i],
                                    data_volume_size = self.data_volume_size,
                                    data_volume_iops = self.data_volume_iops,
                                    mongodb_version = mongodb_version)

            node.autorun()

            self.nodes.append(node)

        if (self.data_nodes%2) == 0:

            self.log.info('Including Arbiter Node')

            node = MongoArbiterNode(group = self.group, server_type = self.server_type,
                                    instance_type = self.instance_type,
                                    environment = self.environment,
                                    ami = self.ami, region = self.region,
                                    role = self.role, keypair = self.keypair,
                                    chef_path = self.chef_path,
                                    replica_set = self.replica_set,
                                    security_groups = self.security_groups,
                                    block_devices = self.block_devices,
                                    availability_zone = zones[i+1],
                                    mongodb_version = mongodb_version)

            node.autorun()

            self.nodes.append(node)

    def baked(self):

        return all([node.baked() for node in self.nodes])

    def status(self):

        self.log.info('Determining replica set status')

        return self.nodes[0].run_mongo('rs.status()')

    def initiate(self):

        self.log.info('Initiating replica set')

        return self.nodes[0].run_mongo('rs.initiate()')

    def add(self, node):

        self.log.info('Adding "{node}" to the replica set'.format(
                                    node = node.hostname))

        template = 'rs.add(\'{node}:27018\')'

        if node.__class__.__name__ == 'MongoArbiterNode':
            template = 'rs.addArb(\'{node}:27018\')'

        return self.nodes[0].run_mongo(template.format(node = node.hostname))

    def add_all(self):

        for node in self.nodes[1:]:
            self.add(node)

    def autorun(self):

        self.provision()
        if self.baked():
            self.initiate()
            while True:
                if len(self.status()['members']) > 0:
                    if self.status()['members'][0]['stateStr'] == 'PRIMARY':
                        break
            self.add_all()
