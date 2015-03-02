import logging
from tyr.servers import MongoDataNode
import time

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

        states = []

        for node in self.nodes:

            self.log.info('Determining status of "{node}"'.format(
                                            node = node.hostname))

            self.log.info('Waiting for Chef Client to start')

            while True:
                r = node.run('ls -l /var/log')

                if 'chef-client.log' in r['out']:
                    break
                else:
                    time.sleep(10)

            self.log.info('Chef Client has started')

            self.log.info('Waiting for Chef Client to finish')

            while True:
                r = node.run('pgrep chef-client')

                if len(r['out']) > 0:
                    time.sleep(10)
                else:
                    break

            self.log.info('Chef Client has finished')

            self.log.info('Determining Node state')

            r = node.run('tail /var/log/chef-client.log')

            if 'Chef Run complete in' in r['out']:
                self.log.info('Chef Client was successful')
                states.append(True)
            else:
                self.log.info('Chef Client was not successful')
                states.append(False)

        return all(states)
