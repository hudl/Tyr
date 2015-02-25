from .. import Server
import logging

class MongoArbiterNode(Server):

    log = logging.getLogger('Servers.MongoArbiterNode')
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
                    replica_set = None):

        super(MongoArbiterNode, self).__init__(dry, verbose, size, cluster,
                                                environment, ami, region, role,
                                                keypair, availability_zone,
                                                security_groups, block_devices)

        self.replica_set = replica_set
        self.chef_path = chef_path

    def configure(self):

        super(MongoArbiterNode, self).configure()

        if self.replica_set is None:
            self.log.warn('No replica set provided')
            self.replica_set = 1

        self.log.info('Using replica set {set}'.format(set = self.replica_set))

    @property
    def name(self):

        try:
            return self.unique_name
        except Exception:
            pass

        name = self.build_name(
                template = '{envcl}-rs{set}-{zone}-arbiter',
                supplemental = {
                    'set': self.replica_set,
                    'zone': self.availability_zone
                },
                search_prefix = '{envcl}-rs{set}-{zone}-')

        self.unique_name = name

        self.log.info('Using node name {name}'.format(name = name))

        return name
