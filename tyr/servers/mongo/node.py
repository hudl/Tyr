from tyr.servers.server import Server
import json


class MongoNode(Server):

    SERVER_TYPE = 'mongo'

    CHEF_RUNLIST = ['role[RoleMongo]']
    CHEF_MONGODB_TYPE = 'generic'

    IAM_ROLE_POLICIES = ['allow-volume-control']

    def __init__(self, group=None, server_type=None, instance_type=None,
                 environment=None, ami=None, region=None, role=None,
                 keypair=None, availability_zone=None,
                 security_groups=None, block_devices=None,
                 chef_path=None, subnet_id=None, dns_zones=None,
                 mongodb_version=None):

        self.mongodb_version = mongodb_version

        if server_type is None:
            server_type = self.SERVER_TYPE

        super(MongoNode, self).__init__(group, server_type, instance_type,
                                        environment, ami, region, role,
                                        keypair, availability_zone,
                                        security_groups, block_devices,
                                        chef_path, subnet_id, dns_zones)

    def configure(self):

        super(MongoNode, self).configure()
        self.ebs_optimized = True

        if self.environment == "prod":
            self.IAM_ROLE_POLICIES.append('allow-mongo-backup-snapshot')
        elif self.environment == "stage":
            self.IAM_ROLE_POLICIES.append('allow-mongo-snapshot-cleanup')

        self.resolve_iam_role()

        if self.mongodb_version is None:
            self.log.warn('MongoDB version not set')
            self.mongodb_version = '2.4.13'

        self.log.info('Using version {version} of MongoDB'.format(
                                                version=self.mongodb_version))

        # This is just a temporary fix to override the default security
        # groups for MongoDB nodes until the security_groups argument
        # is removed.

        self.security_groups = [
            'management',
            'chef-nodes',
            self.envcl,
            '{env}-mongo-management'.format(env=self.environment[0])
        ]

        self.resolve_security_groups()

    def run_mongo(self, command):

        template = 'mongo --port 27018 --eval "JSON.stringify({command})"'

        command = template.format(command=command)

        r = self.run(command)

        return json.loads(r['out'].split('\n')[2])

    def bake(self):

        super(MongoNode, self).bake()

        with self.chef_api:

            self.chef_node.attributes.set_dotted(
                                            'mongodb.cluster_name', self.group)
            self.log.info('Set the cluster name to "{group}"'.format(
                                        group=self.group))

            self.chef_node.attributes.set_dotted(
                                'mongodb.package_version',
                                self.mongodb_version)

            self.log.info('Set the MongoDB package version to '
                          '{version}'.format(version=self.mongodb_version))

            self.chef_node.attributes.set_dotted('mongodb.node_type',
                                                 self.CHEF_MONGODB_TYPE)
            self.log.info('Set the MongoDB node type to "{type_}"'.format(
                                            type_=self.CHEF_MONGODB_TYPE))

            self.chef_node.save()
            self.log.info('Saved the Chef Node configuration')
