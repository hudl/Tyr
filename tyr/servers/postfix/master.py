from tyr.servers.server import Server
import chef
import os.path
import sys
import re

class PostfixMaster(Server):

    SERVER_TYPE  = 'postfix'
    CHEF_RUNLIST = ['role[RolePostfix]']
    ELASTIC_IP   = ''

    #IAM_ROLE_POLICIES = [ ]

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

        if mail_name is not None:
            if re.match('^.+hudl\.com$',mail_name) is None:
                self.mail_name = mail_name + '.hudl.com'
            else:
                self.mail_name = mail_name
        else:
            raise Exception('Must pass existing mail server name!')
            sys.exit(1)

    def configure(self):
        super(PostfixMaster, self).configure()
        """
        1.) Verify that the mail server name exists in DNS and there's an EIP
        associated with it.
        - Cannot assign the IP until there's an instance ID.
        """
        #Check for mail server name in AWS and to see if it has an EIP.
        if self.mail_name:
            route53_conn = self.route53
            elastic_ip   = self.check_mail_server(route53_conn)
            self.ELASTIC_IP = elastic_ip
            self.log.info('Found mail server!')
        else:
            self.log.critical('Must specify a mail server configured in route53!')
            sys.exit(1)


    # Params: Route53 connection object from boto
    # Return: EIP
    def check_mail_server(self,route53_conn):
        """
        Use zone object for hudl.com to search for A records that match the
        supplied mail server name.
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
            sys.exit(1)

        return elastic_ip

    def assign_eip(self):
        ec2_conn    = self.ec2
        instance_id = self.instance.id

        try:
            alloc_id = self.get_alloc_id(ec2_conn)
            if alloc_id is None:
                raise Exception('The EIP associated with the DNS name for '
                                '{mail_name} does not have an allocation ID '
                                'associated with it. This issue can be resolved '
                                'by migrating the EIP from EC2-Classic to '
                                'EC2-VPC.'.format(mail_name=self.mail_name))

            result = ec2_conn.associate_address(instance_id=instance_id,
                                                public_ip=None,
                                                allocation_id=alloc_id,
                                                network_interface_id=None,
                                                private_ip_address=None,
                                                allow_reassociation=True,
                                                dry_run=True)
            if result:
                self.log.info('Successfully assigned EIP: {elastic_ip} '
                              'to {mail_name}'.format(elastic_ip=elastic_ip,
                                                      mail_name=self.mail_name))
            else:
                raise Exception('Unable to assign EIP: {eip}! '
                                'Exiting...'.format(eip=elastic_ip))
        except Exception,e:
            self.log.error(str(e))

    def get_alloc_id(self,ec2_conn):
        try:
            eip_addresses = ec2_conn.get_all_addresses()

            for address_obj in eip_addresses:
                address_str = str(address_obj)
                ip = address_str.split(':')[1]
                if ip == self.ELASTIC_IP:
                    alloc_id = address_obj.allocation_id
                    break

        except Exception,e:
            self.log.error(str(e))

        return alloc_id

    def bake(self):
        super(PostfixMaster, self).bake()

        with self.chef_api:
            self.chef_node.attributes.set_dotted('postfix.main.myhostname',
                                                 self.mail_name)
            self.log.info('Set the mail hostname value in main.cf to '
                          '{mail_name}'.format(mail_name=self.mail_name))

            self.chef_node.save()
            self.log.info('Saved the Chef node configuration')

    def autorun(self):
        super(PostfixMaster, self).autorun()

        if self.baked():
           self.assign_eip()
