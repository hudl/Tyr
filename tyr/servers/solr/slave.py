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
                 subnet_id=None, platform=None,
                 use_latest_ami=False, ingress_groups_to_add=None,
                 ports_to_authorize=None, classic_link=False,
                 chef_server_url=None, master=None):

        self.master = master
        self.data_volume_size = data_volume_size
        self.data_volume_iops = data_volume_iops

        if server_type is None:
            server_type = self.SERVER_TYPE

        super(SolrSlaveNode, self).__init__(group, server_type, instance_type,
                                            environment, ami, region, role,
                                            keypair, availability_zone,
                                            security_groups, None,
                                            chef_path, subnet_id,
                                            platform, use_latest_ami,
                                            ingress_groups_to_add,
                                            ports_to_authorize, classic_link,
                                            chef_server_url)

    def set_chef_attributes(self):
        super(SolrSlaveNode, self).set_chef_attributes()
        self.CHEF_ATTRIBUTES['solr'] = {}

        self.CHEF_ATTRIBUTES['solr']['is_slave'] = 'true'
        self.log.info('Set solr.is_slave to True')

        self.CHEF_ATTRIBUTES['solr']['is_master'] = 'false'
        self.log.info('Set solr.is_master to False')

        self.CHEF_ATTRIBUTES['solr']['master_host'] = self.master
        self.log.info('Set solr.master_host to {master}'.format(
            master=self.master)
        )

        self.CHEF_ATTRIBUTES['solr']['group'] = self.group
        self.log.info('Set solr.group to {group}'.format(group=self.group))

        self.CHEF_ATTRIBUTES['volumes'] = [
            {
                'device': {
                    'path': '/dev/xvdg',
                    'size': self.data_volume_size,
                    'iops': self.data_volume_iops,
                    'name': 'solr-data'
                },
                'mounth': {
                    'path': '/volr',
                    'user': 'tomcat',
                    'group': 'tomcat',
                    'chown': True
                }
            }
        ]

    def configure(self):
        super(SolrSlaveNode, self).configure()

        if self.data_volume_size is None:
            self.log.info("No data volume set, defaulting to 200")
            self.data_volume_size = 200

        if self.master is None:
            self.log.critical('The solr master is not defined')
            sys.exit(1)
