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
                 platform=None, use_latest_ami=False,
                 ingress_groups_to_add=None, ports_to_authorize=None,
                 classic_link=False, add_route53_dns=True, chef_server_url=None,
                 mongodb_version=None, install_automation_agent=None, mongo_cm_group=None):

        self.mongodb_version = mongodb_version
        self.install_automation_agent = install_automation_agent
        self.mongo_cm_group = mongo_cm_group

        if server_type is None:
            server_type = self.SERVER_TYPE

        super(MongoNode, self).__init__(group=group, 
                                        server_type=server_type, 
                                        instance_type=instance_type,
                                        environment=environment, 
                                        ami=ami, 
                                        region=region, 
                                        role=role,
                                        keypair=keypair, 
                                        availability_zone=availability_zone,
                                        security_groups=security_groups, 
                                        block_devices=block_devices,
                                        chef_path=chef_path, 
                                        subnet_id=subnet_id, 
                                        dns_zones=dns_zones,
                                        platform=platform, 
                                        use_latest_ami=use_latest_ami,
                                        ingress_groups_to_add=ingress_groups_to_add, 
                                        ports_to_authorize=ports_to_authorize,
                                        classic_link=classic_link, 
                                        add_route53_dns=add_route53_dns,
                                        chef_server_url=chef_server_url)

    def set_chef_attributes(self):
        super(MongoNode, self).set_chef_attributes()
        self.CHEF_ATTRIBUTES['mongodb'] = {}
        self.CHEF_ATTRIBUTES['mongodb']['cluster_name'] = self.group
        self.log.info('Set the cluster name to "{group}"'.format(
            group=self.group)
        )
        self.CHEF_ATTRIBUTES['mongodb']['package_version'] = self.mongodb_version
        self.log.info('Set the MongoDB package version to {version}'.format(
            version=self.mongodb_version)
        )
        self.CHEF_ATTRIBUTES['mongodb']['node_type'] = self.CHEF_MONGODB_TYPE
        self.log.info('Set the MongoDB node type to "{type_}"'.format(
            type_=self.CHEF_MONGODB_TYPE)
        )
        if self.install_automation_agent:
            self.CHEF_ATTRIBUTES['mongodb']['automation_agent'] = {}
            self.CHEF_ATTRIBUTES['mongodb']['automation_agent']['mongo_cm_group'] = self.mongo_cm_group
            self.CHEF_ATTRIBUTES['mongodb']['automation_agent']['install'] = True


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
        self.resolve_iam_role()

        if self.mongodb_version is None:
            self.log.warn('MongoDB version not set')
            self.mongodb_version = '2.4.13'

        self.log.info('Using version {version} of MongoDB'.format(
            version=self.mongodb_version)
        )

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
