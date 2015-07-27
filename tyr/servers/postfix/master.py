from tyr.servers.server import Server
from tyr.utilities.replace_mongo_server import stop_decommissioned_node
import chef
import sys
import re
import os

class PostfixMaster(Server):

    SERVER_TYPE          = 'postfix'
    CHEF_RUNLIST         = ['role[RolePostfix]']
    ELASTIC_IP           = ''
    STACKDRIVER_API_KEY  = os.environ.get('STACKDRIVER_API_KEY', False)
    STACKDRIVER_USERNAME = os.environ.get('STACKDRIVER_USERNAME', False)

    def __init__(self, group=None, server_type=None, instance_type=None,
                 environment=None, ami=None, region=None, role=None,
                 keypair=None, availability_zone=None,
                 security_groups=None, block_devices=None,
                 chef_path=None, subnet_id=None, dns_zones=None,
                 mail_name=None):

        if server_type is None:
            server_type = self.SERVER_TYPE

        super(PostfixMaster, self).__init__(group, server_type, instance_type,
                                            environment, ami, region, role,
                                            keypair, availability_zone,
                                            security_groups, block_devices,
                                            chef_path, subnet_id, dns_zones)

        try:
            if mail_name is not None:
                if re.match('^.+hudl\.com$',mail_name) is None:
                    self.mail_name = mail_name + '.hudl.com'
                else:
                    self.mail_name = mail_name
            else:
                raise Exception('Must pass existing mail server name!')
        except Exception,e:
            self.log.critical(str(e))
            raise e
            sys.exit(1)

    def configure(self):
        super(PostfixMaster, self).configure()

        if self.mail_name:
            route53_conn = self.route53
            elastic_ip   = self.check_mail_server(route53_conn)
            self.ELASTIC_IP = elastic_ip
            self.log.info('Found mail server!')
        else:
            self.log.critical('Must specify a mail server configured in route53!')
            sys.exit(1)

    def check_mail_server(self,route53_conn):
        """Verify the mail server exists in DNS ans has an EIP

        :param route53_conn: The route53 boto object.
        :type route53_conn: obj.
        :returns: str -- A string with the elastic IP.
        """
        hosted_zone    = 'hudl.com'
        zone_obj       = route53_conn.get_zone(hosted_zone)
        try:
            a_record = zone_obj.get_a(self.mail_name)
            if a_record:
                a_record_str    = str(a_record)
                a_record_format = a_record_str.translate(None, '<>')
                elastic_ip      = a_record_format.split(':')[3]
                self.log.info('Using Elastic IP {elastic_ip}...'.format(
                                                    elastic_ip=elastic_ip))
            else:
                raise Exception('Unable to find mail server {mail_name} in '
                                'route53!'.format(mail_name=self.mail_name))
        except Exception, e:
            self.log.critical(str(e))
            raise e
            sys.exit(1)

        return elastic_ip

    def assign_eip(self):
        """Assigns an EIP to an instance"""
        ec2_conn    = self.ec2
        instance_id = self.instance.id
        address     = self.instance.ip_address

        try:
            alloc_id = self.get_alloc_id(ec2_conn)
            result   = ec2_conn.associate_address(instance_id=instance_id,
                                                  public_ip=None,
                                                  allocation_id=alloc_id,
                                                  network_interface_id=None,
                                                  private_ip_address=None,
                                                  allow_reassociation=True,
                                                  dry_run=False)
            if result:
                self.log.info('Successfully assigned EIP: {elastic_ip} '
                              'to {mail_name}'.format(elastic_ip=elastic_ip,
                                                      mail_name=self.mail_name))
            else:
                raise Exception('Unable to assign EIP: {eip}! '
                                'Exiting...'.format(eip=elastic_ip))
        except Exception,e:
            self.log.critical(str(e))
            self.terminate_node(address)
            raise e
            sys.exit(1)

    def get_alloc_id(self,ec2_conn):
        """Determine the allocation ID for an EIP.

        :param ec2_conn: The boto ec2 connection object.
        :type ec2_conn: obj.
        :returns: str -- the allocation ID
        """

        address  = self.instance.ip_address
        alloc_id = None
        try:
            eip_addresses = ec2_conn.get_all_addresses()

            for address_obj in eip_addresses:
                address_str = str(address_obj)
                ip = address_str.split(':')[1]
                if ip == self.ELASTIC_IP:
                    alloc_id = address_obj.allocation_id
                    break

            if alloc_id is None:
                raise Exception('The EIP associated with the DNS name for '
                                '{mail_name} does not have an allocation ID '
                                'associated with it. This issue can be resolved '
                                'by migrating the EIP from EC2-Classic to '
                                'EC2-VPC.'.format(mail_name=self.mail_name))

        except Exception,e:
            self.log.critical(str(e))
            self.terminate_node(address)
            raise e
            sys.exit(1)

        return alloc_id

    def terminate_node(self,address):
        stop_decommissioned_node(address=address,terminate=True,
                                 stackdriver_username=self.STACKDRIVER_USERNAME,
                                 stackdriver_api_key=self.STACKDRIVER_API_KEY)

    def bake(self):
        """ Add the myhostname attribute for the main.cf postfix config"""

        super(PostfixMaster, self).bake()

        with self.chef_api:
            self.chef_node.attributes.set_dotted('postfix.main.myhostname',
                                                 self.mail_name)
            self.log.info('Set the mail hostname value in main.cf to '
                          '{mail_name}'.format(mail_name=self.mail_name))
            self.chef_node.save()
            self.log.info('Saved the Chef node configuration')

    def autorun(self):
        """Asign the EIP after the instance is up and configured."""

        super(PostfixMaster, self).autorun()

        if self.baked():
           self.assign_eip()
