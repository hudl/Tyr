from tyr.servers.server import Server


class MongoCmMonitor(Server):

    SERVER_TYPE = 'mms'
    CHEF_RUNLIST = ['role[RoleMongoCmMonitor]']

    def __init__(self, group=None, server_type=None, instance_type=None,
                 environment=None, ami=None, region=None, role=None,
                 keypair=None, availability_zone=None,
                 security_groups=None, block_devices=None,
                 chef_path=None, subnet_id=None, dns_zones=None):

        if server_type is None:
            server_type = self.SERVER_TYPE

        super(MongoCmMonitor, self).__init__(group, server_type, instance_type,
                                             environment, ami, region, role,
                                             keypair, availability_zone,
                                             security_groups, block_devices,
                                             chef_path, subnet_id, dns_zones)
