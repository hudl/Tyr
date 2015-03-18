from tyr.servers.server import Server

class MongoNode(Server):

    TYPE_ = 'mongo'

    CHEF_RUNLIST = ['role[RoleMongo]']
    CHEF_MONGODB_TYPE = 'generic'

    IAM_ROLE_POLICIES = ['allow-volume-control']

    def __init__(self, group = None, type_ = None, instance_type = None,
                    environment = None, ami = None, region = None, role = None,
                    keypair = None, availability_zone = None,
                    security_groups = None, block_devices = None,
                    chef_path = None):

        if type_ is None: type_ = TYPE_

        super(MongoNode, self).__init__(group, type_, instance_type,
                                        environment, ami, region, role,
                                        keypair, availability_zone,
                                        security_groups, block_devices,
                                        chef_path)

    def run_mongo(self, command):

        template = 'mongo --port 27018 --eval "JSON.stringify({command})"'

        command = template.format(command = command)

        r = self.run(command)

        return json.loads(r['out'].split('\n')[2])

    def bake(self):

        super(MongoNode, self).bake()

        with self.chef_api:

            self.chef_node.attributes.set_dotted(
                                            'mongodb.cluster_name', self.group)
            self.log.info('Set the cluster name to "{group}"'.format(
                                        group = self.group))

            if self.chef_node.chef_environment == 'prod':
                self.chef_node.run_list.append('role[RoleSumoLogic]')

            self.log.info('Set the run list to "{runlist}"'.format(
                                        runlist = self.chef_node.run_list))

            self.chef_node.attributes.set_dotted('mongodb.node_type', self.CHEF_MONGODB_TYPE)
            self.log.info('Set the MongoDB node type to "{type_}"'.format(
                                            type_ = self.CHEF_MONGODB_TYPE))

            self.chef_node.save()
            self.log.info('Saved the Chef Node configuration')
