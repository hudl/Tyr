from node import MongoNode

class MongoReplicaSetMember(MongoNode):

    def __init__(self, dry = None, verbose = None, instance_type = None,
                    group = None, type_ = None, environment = None, ami = None,
                    region = None, role = None, keypair = None,
                    availability_zone = None, security_groups = None,
                    block_devices = None, chef_path = None, replica_set = None):

        super(MongoReplicaSetMember, self).__init__(dry, verbose, instance_type,
                                                    group, type_, environment,
                                                    ami, region, role, keypair,
                                                    availability_zone,
                                                    security_groups,
                                                    block_devices, chef_path)

        self.replica_set = replica_set

    def configure(self):

        super(MongoReplicaSetMember, self).configure()

        if self.replica_set is None:
            self.log.warn('No replica set provided')
            self.replica_set = 1

        self.log.info('Using replica set {set}'.format(set = self.replica_set))

    def bake(self):

        super(MongoReplicaSetMember, self).bake()

        with self.chef_api:

            replica_set = '{group}-rs{set_}'.format(group = self.group,
                                                    set_ = self.replica_set)

            self.chef_node.attributes.set_dotted(
                                        'mongodb.replicaset_name', replica_set)
            self.log.info('Set the replica set name to "{name}"'.format(
                                        name = replica_set))

            self.chef_node.save()
            self.log.info('Saved the Chef Node configuration')
