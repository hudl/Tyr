import logging

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
