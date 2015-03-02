import logging
from tyr.servers import MongoDataNode
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

    def __init__(self, dry = None, verbose = None, size = None, cluster = None,
                    environment = None, ami = None, region = None, role = None,
                    keypair = None, chef_path = None, replica_set = None,
                    security_groups = None, block_devices = None,
                    data_nodes=None):

        self.nodes = []

        self.dry = dry
        self.verbose = verbose
        self.size = size
        self.cluster = cluster
        self.environment = environment
        self.ami = ami
        self.region = region
        self.role = role
        self.keypair = keypair
        self.chef_path = chef_path
        self.security_groups = security_groups
        self.block_devices = block_devices
        self.replica_set = replica_set
        self.data_nodes = data_nodes

    def provision(self):

        zones = 'cde'

        self.log.info('Building availability zone list')

        while len(zones) < self.data_nodes:

            zones += zones

        self.log.info('Provisioning MongoDB Data Nodes')

        for i in range(self.data_nodes):

            node = MongoDataNode(dry = self.dry, verbose = self.verbose,
                                    size = self.size, cluster = self.cluster,
                                    environment = self.environment,
                                    ami = self.ami, region = self.region,
                                    role = self.role, keypair = self.keypair,
                                    chef_path = self.chef_path,
                                    replica_set = self.replica_set,
                                    security_groups = self.security_groups,
                                    block_devices = self.block_devices,
                                    availability_zone = zones[i])

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

        return self.nodes[0].run_mongo(template.format(node = node.hostname))

    def add_all(self):

        for node in self.nodes[1:]:
            self.add(node)


