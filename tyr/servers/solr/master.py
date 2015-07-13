from tyr.servers.server import Server


class SolrMasterNode(Server):

    SERVER_TYPE = 'solr'
    CHEF_RUNLIST = ['role[Solr]']
    IAM_ROLE_POLICIES = ['allow-volume-control']

    def __init__(self, group=None, server_type=None, instance_type=None,
                 environment=None, ami=None, region=None, role=None,
                 keypair=None, availability_zone=None, security_groups=None,
                 block_devices=None, chef_path=None, subnet_id=None,
                 dns_zones=None):

        if server_type is None: server_type = self.SERVER_TYPE

        super(SolrMasterNode, self).__init__(group, server_type, instance_type,
                                             environment, ami, region, role,
                                             keypair, availability_zone,
                                             security_groups, block_devices,
                                             chef_path, subnet_id, dns_zones)

    def bake(self):

        super(SolrMasterNode, self).bake()

        with self.chef_api:
            self.chef_node.attributes.set_dotted('solr.is_master', True)
            self.log.info('Set solr.is_master to True')

            self.chef_node.save()
            self.log.info('Saved the Chef Node configuration')
