from node import MongoNode

class MongoReplicaSetMember(MongoNode):

    def __init__(self, dry = None, verbose = None, size = None, cluster = None,
                    environment = None, ami = None, region = None, role = None,
                    keypair = None, availability_zone = None, chef_path = None,
                    security_groups = None, block_devices = None,
                    replica_set = None):

        super(MongoReplicaSetMember, self).__init__(dry, verbose, size, cluster,
                                                environment, ami, region, role,
                                                keypair, availability_zone,
                                                security_groups, block_devices)

        self.replica_set = replica_set

    def configure(self):

        super(MongoReplicaSetMember, self).configure()

        if self.replica_set is None:
            self.log.warn('No replica set provided')
            self.replica_set = 1

        self.log.info('Using replica set {set}'.format(set = self.replica_set))

    def bake(self):

        super(MongoReplicaSetMember, self).bake()

        chef_api = self.chef_api
        node = self.chef_node

        replica_set = 'rs' + str(self.replica_set)

        node.attributes.set_dotted('mongodb.replicaset_name', replica_set)
        self.log.info('Set the replica set name to "{name}"'.format(
                                    name = replica_set))

        node.save(api=chef_api)
        self.log.info('Saved the Chef Node configuration')
