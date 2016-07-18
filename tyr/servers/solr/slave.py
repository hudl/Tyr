from tyr.servers.server import Server
import sys


class SolrSlaveNode(Server):

    SERVER_TYPE = 'solr'
    CHEF_RUNLIST = ['role[RoleSolr]']
    IAM_ROLE_POLICIES = [
        'allow-volume-control',
        'allow-get-solr-schema'
    ]

    def __init__(self, group=None, server_type=None, instance_type=None,
                 environment=None, ami=None, region=None, role=None,
                 keypair=None, availability_zone=None, security_groups=None,
                 data_volume_size=None, data_volume_iops=None, chef_path=None,
                 subnet_id=None, dns_zones=None, platform=None,
                 use_latest_ami=False, master=None):

        self.master = master
        self.data_volume_size = data_volume_size
        self.data_volume_iops = data_volume_iops

        if self.data_volume_size is None:
            self.log.info("No data volume set, defaulting to 200")
            self.data_volume_size = 200

        if server_type is None:
            server_type = self.SERVER_TYPE

        super(SolrSlaveNode, self).__init__(group, server_type, instance_type,
                                            environment, ami, region, role,
                                            keypair, availability_zone,
                                            security_groups, None,
                                            chef_path, subnet_id, dns_zones,
                                            platform, use_latest_ami)

    def configure(self):

        super(SolrSlaveNode, self).configure()

        if self.master is None:
            self.log.critical('The solr master is not defined')
            sys.exit(1)

        self.security_groups = [
            'management',
            'chef-nodes',
            self.envcl,
            '{env}-solr-management'.format(env=self.environment[0])
        ]

        self.resolve_security_groups()

    def bake(self):

        super(SolrSlaveNode, self).bake()

        with self.chef_api:
            self.chef_node.attributes.set_dotted('solr.is_slave', True)
            self.log.info('Set solr.is_slave to True')

            self.chef_node.attributes.set_dotted('solr.is_master', False)
            self.log.info('Set solr.is_master to False')

            self.chef_node.attributes.set_dotted('solr.master_host',
                                                 self.master)
            self.log.info('Set solr.master_host to {master}'.format(
                          master=self.master))

            self.chef_node.attributes.set_dotted('solr.group', self.group)
            self.log.info('Set solr.group to {group}'.format(group=self.group))

            self.chef_node.attributes.set_dotted('hudl_ebs.volumes', [{
                'user': 'tomcat',
                'group': 'tomcat',
                'size': self.data_volume_size,
                'iops': self.data_volume_iops,
                'device': '/dev/xvdg',
                'mount': '/volr'
            }
            ])

            self.chef_node.save()
            self.log.info('Saved the Chef Node configuration')
