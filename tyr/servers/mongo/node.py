from tyr.servers import Server

class MongoNode(Server):

    CHEF_RUNLIST = ['role[RoleMongo]']
    CHEF_MONGODB_TYPE = 'generic'

    def __init__(self, dry = None, verbose = None, size = None, cluster = None,
                    environment = None, ami = None, region = None, role = None,
                    keypair = None, availability_zone = None, chef_path = None,
                    security_groups = None, block_devices = None):

        super(MongoNode, self).__init__(dry, verbose, size, cluster,
                                                environment, ami, region, role,
                                                keypair, availability_zone,
                                                security_groups, block_devices)
    def run_mongo(self, command):

        template = 'mongo --port 27018 --eval "JSON.stringify({command})"'

        command = template.format(command = command)

        r = self.run(command)

        return json.loads(r['out'].split('\n')[2])

    def bake(self):

        super(MongoNode, self).bake()

        chef_api = self.chef_api
        node = self.chef_node

        cluster_name = self.cluster.split('-')[0]

        node.attributes.set_dotted('mongodb.cluster_name', cluster_name)
        self.log.info('Set the cluster name to "{name}"'.format(
                                    name = cluster_name))

        if node.chef_environment == 'prod':
            node.run_list.append('role[RoleSumoLogic]')

        self.log.info('Set the run list to "{runlist}"'.format(
                                        runlist = node.run_list))

        node.attributes.set_dotted('mongodb.node_type', self.CHEF_MONGODB_TYPE)
        self.log.info('Set the MongoDB node type to "{type_}"'.format(
                                            type_ = self.CHEF_MONGODB_TYPE))

        node.save(api=chef_api)
        self.log.info('Saved the Chef Node configuration')
