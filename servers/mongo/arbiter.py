from .. import Server
import logging
import chef

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
                template = '{envcl}-rs{set}-{zone}-arb',
                supplemental = {
                    'set': self.replica_set,
                    'zone': self.availability_zone
                },
                search_prefix = '{envcl}-rs{set}-{zone}-')

        self.unique_name = name

        self.log.info('Using node name {name}'.format(name = name))

        return name

    def bake(self):

        super(MongoArbiterNode, self).bake()

        chef_api = self.chef_api

        node = chef.Node.create(self.name, api=chef_api)

        self.log.info('Created new Chef Node \'{node}\''.format(
                        node = self.name))

        node.chef_environment = self.environment

        self.log.info('Set the Chef Environment to \'{env}\''.format(
                        env = node.chef_environment))

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
        self.log.info('Set the cluster name to \'{name}\''.format(
                                    name = cluster_name))

        node.attributes.set_dotted('mongodb.replicaset_name', replica_set)
        self.log.info('Set the replica set name to \'{name}\''.format(
                                    name = replica_set))

        node.attributes.set_dotted('mongodb.node_type', 'arbiter')
        self.log.info('Set the MongoDB node type to \'arbiter\'')

        runlist = ['role[RoleMongo]']

        if node.chef_environment == 'prod':
            pass
        else:
            runlist.append('role[RoleSumoLogic]')

        node.run_list = runlist
        self.log.info('Set the run list to \'{runlist}\''.format(
                                        runlist = node.run_list))

        node.attributes.set_dotted('mongodb.config.smallfiles', True)

        node.save(api=chef_api)
        self.log.info('Saved the Chef Node configuration')
