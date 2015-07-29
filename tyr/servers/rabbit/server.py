from tyr.servers.server import Server
import sys


class RabbitMQServer(Server):

    SERVER_TYPE = 'rabbit'

    CHEF_RUNLIST = ['role[RoleRabbit]']

    IAM_ROLE_POLICIES = [
        'allow-describe-tags',
        'allow-volume-control',
        'allow-update-route53-{environment}'
    ]

    def __init__(self, group=None, server_type=None, instance_type=None,
                 environment=None, ami=None, region=None, role=None,
                 keypair=None, availability_zone=None, security_groups=None,
                 block_devices=None, chef_path=None, subnet_id=None,
                 dns_zones=None, vol_iops=500, vol_size=100,
                 rabbit_user=None, rabbit_pass=None):

        if server_type is None: server_type = self.SERVER_TYPE

        self.vol_iops = vol_iops
        self.vol_size = vol_size

        if rabbit_user is None:
            raise Exception("A rabbit user was not defined!")
            sys.exit(1)
        else:
            self.rabbit_user = rabbit_user

        if rabbit_pass is None:
            raise Exception("A rabbit user password was not defined!")
            sys.exit(1)
        else:
            self.rabbit_pass = rabbit_pass

        super(RabbitMQServer, self).__init__(group, server_type, instance_type,
                                             environment, ami, region, role,
                                             keypair, availability_zone,
                                             security_groups, block_devices,
                                             chef_path, subnet_id, dns_zones)

    def configure(self):
        """Make sure the IOPS to Size ratio is not greater than 30 for an EBS"""

        super(RabbitMQServer, self).configure()

        iops_size_ratio = self.vol_iops/self.vol_size
        self.log.info('The IOPS to Size ratio is "{ratio}"'.format(ratio=iops_size_ratio))
        if iops_size_ratio > 30:
            self.log.critical('The IOPS to Size ratio is greater than 30')
            sys.exit(1)

    def bake(self):
        """Add IOPS and Volume Size attributes based on dynamic values from tyr"""

        super(RabbitMQServer, self).bake()

        with self.chef_api:

            self.chef_node.attributes.set_dotted('rabbitmq.volumes.iops',
                                                 self.vol_iops)
            self.log.info('Set the rabbitmq volume IOPS to '
                          '{vol_iops}'.format(vol_iops=self.vol_iops))

            self.chef_node.attributes.set_dotted('rabbitmq.volumes.size',
                                                 self.vol_size)
            self.log.info('Set the rabbitmq volume size to '
                          '{vol_size}'.format(vol_size=self.vol_size))

            self.chef_node.attributes.set_dotted('rabbitmq.user',
                                                 self.rabbit_user)
            self.log.info('Set the rabbitmq user to '
                          '{rabbit_user}'.format(rabbit_user=self.rabbit_user))

            self.chef_node.attributes.set_dotted('rabbitmq.passwd',
                                                 self.rabbit_pass)
            self.log.info('Set the rabbitmq password to ... something secret')

            self.chef_node.save()
            self.log.info('Saved the Chef node configuration')
