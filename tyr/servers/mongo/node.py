from tyr.servers.server import Server
import json


class MongoNode(Server):

    SERVER_TYPE = 'mongo'

    CHEF_RUNLIST = ['role[rolemongo]']
    CHEF_MONGODB_TYPE = 'generic'

    IAM_ROLE_POLICIES = ['allow-volume-control']
    IAM_MANAGED_POLICIES = ['zuun-managed']

    def __init__(self, group=None, server_type=None, instance_type=None,
                 environment=None, ami=None, region=None, role=None,
                 keypair=None, availability_zone=None,
                 security_groups=None, block_devices=None,
                 chef_path=None, subnet_id=None,
                 platform=None, use_latest_ami=False,
                 ingress_groups_to_add=None, ports_to_authorize=None,
                 classic_link=False, chef_server_url=None):

        if server_type is None:
            server_type = self.SERVER_TYPE

        super(MongoNode, self).__init__(group, server_type, instance_type,
                                        environment, ami, region, role,
                                        keypair, availability_zone,
                                        security_groups, block_devices,
                                        chef_path, subnet_id,
                                        platform, use_latest_ami,
                                        ingress_groups_to_add, ports_to_authorize,
                                        classic_link, chef_server_url)

    def set_chef_attributes(self):
        super(MongoNode, self).set_chef_attributes()

        self.CHEF_ATTRIBUTES['mongodb'] = {}

        self.CHEF_ATTRIBUTES['mongodb']['cluster_name'] = self.group
        self.log.info('Set the cluster name to "{group}"'.format(
            group=self.group)
        )

        self.CHEF_ATTRIBUTES['mongodb']['node_type'] = self.CHEF_MONGODB_TYPE
        self.log.info('Set the MongoDB node type to "{type_}"'.format(
            type_=self.CHEF_MONGODB_TYPE)
        )

        self.CHEF_ATTRIBUTES['zuun'] = {}

        self.CHEF_ATTRIBUTES['zuun']['deployment'] = '{env}-{group}'.format(
            env=self.environment[0],
            group=self.group
        )
        self.log.info('Set the Zuun deployment to "{env}-{group}"'.format(
            env=self.environment[0],
            group=self.group
        ))

        self.CHEF_ATTRIBUTES['zuun']['role'] = self.CHEF_MONGODB_TYPE
        self.log.info('Set the Zuun role to "{type_}"'.format(
            type_=self.CHEF_MONGODB_TYPE)
        )


    def configure(self):
        super(MongoNode, self).configure()
        self.set_chef_attributes()

        if self.environment == 'prod':
            self.ebs_optimized = True

        if self.environment == "prod":
            self.IAM_ROLE_POLICIES.append('allow-mongo-backup-snapshot')
        elif self.environment == "stage":
            self.IAM_ROLE_POLICIES.append('allow-mongo-snapshot-cleanup')
            self.IAM_MANAGED_POLICIES.append('allow-mongo-backup-restore')


    def run_mongo(self, command):

        template = 'mongo --port 27018 --eval "JSON.stringify({command})"'

        command = template.format(command=command)

        r = self.run(command)

        return json.loads(r['out'].split('\n')[2])
