from tyr.servers.server import Server


class SolrNode(Server):

    SERVER_TYPE = 'solr'
    CHEF_RUNLIST = ['role[RoleSolr]']
    IAM_ROLE_POLICIES = [
        'allow-volume-control',
        'allow-get-solr-schema'
    ]

    def __init__(self, group=None, server_type=None, instance_type=None,
                 environment=None, ami=None, region=None, role=None,
                 keypair=None, availability_zone=None, security_groups=None,
                 block_devices=None, chef_path=None, subnet_id=None,
                 dns_zones=None, is_master=True, is_slave=False,
                 master_host=None):

        if server_type is None:
            server_type = self.SERVER_TYPE

        self.is_master = is_master
        self.is_slave = is_slave
        self.master_host = master_host

        super(SolrNode, self).__init__(group, server_type, instance_type,
                                       environment, ami, region, role,
                                       keypair, availability_zone,
                                       security_groups, block_devices,
                                       chef_path, subnet_id, dns_zones)

    def configure(self):
        super(SolrNode, self).configure()

        if self.master_host is None:
            self.log.warn('No Solr master host provided')
            self.master_host = self.hostname

        self.log.info('Using Solr master host {}'.format(self.master_host))

        self.security_groups = [
            'management',
            'chef-nodes',
            self.envcl,
            '{env}-solr-management'.format(env=self.environment[0])
        ]

        self.resolve_security_groups()

    def bake(self):
        super(SolrNode, self).bake()

        with self.chef_api:
            self.chef_node.attributes.set_dotted('solr.is_master',
                                                 self.is_master)
            self.log.info('Set solr.is_master to {}'.format(self.is_master))

            self.chef_node.attributes.set_dotted('solr.is_slave',
                                                 self.is_slave)
            self.log.info('Set solr.is_slave to {}'.format(self.is_slave))

            self.chef_node.attributes.set_dotted('solr.group', self.group)
            self.log.info('Set solr.group to {group}'.format(group=self.group))

            self.chef_node.attributes.set_dotted('solr.master_host',
                                                 self.master_host)
            self.log.info('Set solr.master_host to {master}'.format(
                          master=self.master_host))

            self.chef_node.save()
            self.log.info('Saved the Chef Node configuration')
