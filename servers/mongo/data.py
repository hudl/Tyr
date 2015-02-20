from .. import Server
import logging
import os
import chef

class MongoDataNode(Server):

    log = logging.getLogger('Servers.MongoDataNode')
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
                    keypair = None, availability_zone = None,
                    security_groups = None, block_devices = None,
                    replica_set = None, replica_set_index = None):

        super(MongoDataNode, self).__init__(dry, verbose, size, cluster,
                                            environment, ami, region, role,
                                            keypair, availability_zone,
                                            security_groups, block_devices)

        self.replica_set = replica_set
        self.replica_set_index = replica_set_index

    def configure(self):

        super(MongoDataNode, self).configure()

        if self.replica_set is None:
            self.log.warn('No replica set provided')
            self.replica_set = 1

        self.log.info('Using replica set {set}'.format(set=self.replica_set))

        if self.replica_set_index is None:
            self.log.warn('No replica set set index provided')
            self.replica_set_index = 1

        self.log.info('Using replica set index {index}'.format(
                        index=self.replica_set_index))

    @property
    def name(self):

        try:
            return self.unique_name
        except Exception:
            pass

        template = '{envcl}-rs{set}-{zone}-{index}'
        name = template.format(envcl=self.envcl, set=self.replica_set,
                                zone=self.availability_zone[-1:],
                                index=self.replica_set_index)

        self.unique_name = name

        self.log.info('Using node name {name}'.format(name=name))

        return name

    def bake(self):

        chef_path = os.path.expanduser('~/.chef')
        chef_api = chef.autoconfigure(chef_path)

        try:
            node = chef.Node('self.name')
            node.delete()
        except chef.exceptions.ChefServerNotFoundError:
            pass
        except Exception as e:
            raise e

        try:
            client = chef.Client(self.name)
            client = client.delete()
        except chef.exceptions.ChefServerNotFoundError:
            pass
        except Exception as e:
            raise e

        node = chef.Node.create(self.name, api=chef_api)
        node.chef_environment = self.environment

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
                    'size': 400,
                    'iops': 3000,
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
                    'size': 400,
                    'iops': 0,
                    'device': '/dev/xvdf',
                    'mount': '/volr'
                }
            ])

        cluster_name = self.cluster.split('-')[0]
        replica_set = 'rs' + str(self.replica_set)

        node.attributes.set_dotted('mongodb.cluster_name', cluster_name)
        node.attributes.set_dotted('mongodb.replicaset_name', replica_set)

        runlist = ['role[RoleMongo]']

        if node.chef_environment == 'prod':
            pass
        else:
            runlist.append('role[RoleSumoLogic]')

        node.run_list = runlist

        node.save(api=chef_api)

    def autorun(self):

        super(MongoDataNode, self).autorun()
        self.bake()