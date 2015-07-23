from tyr.servers.server import Server
import chef
import os.path
import sys
import re

class PostfixMaster(Server):

    SERVER_TYPE = 'postfix'
    CHEF_RUNLIST = ['role[RolePostfix]']

    #IAM_ROLE_POLICIES = [ ]

    def __init__(self, group=None, server_type=None, instance_type=None,
                 environment=None, ami=None, region=None, role=None,
                 keypair=None, availability_zone=None,
                 security_groups=None, block_devices=None,
                 chef_path=None, subnet_id=None, dns_zones=None,
                 mail_name=None):

        if re.match('^.+hudl\.com$',mail_name) is None:
            self.mail_name = mail_name + '.hudl.com'
        else:
            self.mail_name = mail_name

        if server_type is None:
            server_type = self.SERVER_TYPE

        super(PostfixMaster, self).__init__(group, server_type, instance_type,
                                        environment, ami, region, role,
                                        keypair, availability_zone,
                                        security_groups, block_devices,
                                        chef_path, subnet_id, dns_zones)

    def configure(self):
        super(PostfixMaster, self).configure()

        #Check for mail server name in AWS and to see if it has an EIP.
        if self.mail_name:
            route53_conn = self.establish_route53_connection()
            elastic_ip   = self.check_mail_server(route53_conn)
            self.log.info('Found mail server!')
            # Assign the elastic ip to the instance.
            self.assign_eip(elastic_ip)
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
        zone_obj       = conn.get_zone(hosted_zone)
        try:
            a_record = zone_obj.get_a(self.mail_name)
            if a_record:
                a_record_str    = str(a_record)
                a_record_format = a_record_str.translate(None, '<>')
                elastic_ip      = a_record_format.split(':')[3]
                self.log.info('Using Elastic IP {elastic_ip}...'.format(
                                                    elastic_ip=elastic_ip))
            else:
                raise 'Unable to find mail server in route53!'
        except Exception, e:
            self.log.critical(str(e))
            sys.exit(1)

        return elastic_ip

    def assign_eip(self,elastic_ip):
        ec2_conn    = self.establish_ec2_connection()
        instance_id = self.instance.id
        try:
            result = ec2_conn.associate_address(instance_id,elastic_ip,None,None,
                                                None,True,True)
            if result:
                self.log.info('Successfully assigned EIP: {elastic_ip} '
                              'to {mail_name}'.format(elastic_ip=elastic_ip,
                                                      mail_name=self.mail_name))
            else:
                raise 'Unable to assign EIP! Exiting...'
        except Exception,e:
            self.log.critical(str(e))
            sys.exit(1)


    def bake(self):
        super(PostfixMaster, self).bake()

        with self.chef_api:
            self.chef_node.attributes.set_dotted('postfix.main.myhostname',
                                                 self.mail_name)
            self.log.info('Set the mail hostname value in main.cf to '
                          '{mail_name}'.format(mail_name=self.mail_name))

            self.chef_node.save()
            self.log.info('Saved the Chef node configuration')
