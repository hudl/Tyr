from tyr.servers.server import Server
import re


class PostfixMaster(Server):

    SERVER_TYPE = 'postfix'
    CHEF_RUNLIST = ['role[RolePostfix]']
    ELASTIC_IP = ''

    def __init__(self, group=None, server_type=None, instance_type=None,
                 environment=None, ami=None, region=None, role=None,
                 keypair=None, availability_zone=None,
                 security_groups=None, block_devices=None,
                 chef_path=None, subnet_id=None,
                 platform=None, use_latest_ami=False,
                 ingress_groups_to_add=None, ports_to_authorize=None,
                 classic_link=False, chef_server_url=None,
                 mail_name=None):

        if server_type is None:
            server_type = self.SERVER_TYPE

        super(PostfixMaster, self).__init__(group, server_type, instance_type,
                                            environment, ami, region, role,
                                            keypair, availability_zone,
                                            security_groups, block_devices,
                                            chef_path, subnet_id,
                                            platform, use_latest_ami,
                                            ingress_groups_to_add,
                                            ports_to_authorize, classic_link,
                                            chef_server_url)

        try:
            if mail_name is not None:
                if re.match('^.+hudl\.com$', mail_name) is None:
                    self.mail_name = mail_name + '.hudl.com'
                else:
                    self.mail_name = mail_name
            else:
                raise Exception('Must pass existing mail server name!')
        except Exception, e:
            self.log.critical(str(e))
            raise e

    def set_chef_attributes(self):
        """
        Add the myhostname attribute for the main.cf postfix config
        """
        super(PostfixMaster, self).set_chef_attributes()
        self.CHEF_ATTRIBUTES['postfix'] = {}
        self.CHEF_ATTRIBUTES['postfix']['main'] = {'myhostname': self.mail_name}
        self.log.info('Set the mail hostname value in main.cf to '
                      '{mail_name}'.format(mail_name=self.mail_name))

    def configure(self):
        super(PostfixMaster, self).configure()

        if self.mail_name:
            self.ELASTIC_IP = self.check_mail_server()
            self.log.info('Found mail server!')
        else:
            self.log.critical('Must specify a mail server configured in '
                              'route53!')
            raise Exception('Must specify a mail server configured in '
                            'route53!')

    def check_mail_server(self):
        """
        Verify the mail server exists in DNS ans has an EIP

        :returns: str -- A string with the elastic IP.
        """

        hosted_zone = 'hudl.com'
        zone_obj = self.route53.get_zone(hosted_zone)
        try:
            a_record = zone_obj.get_a(self.mail_name)
            if a_record:
                a_record_str = str(a_record)
                pattern = '^.+{mail_name}.+A:(([0-9]{{1,3}}\.){{3}}[0-9]{{1,3}}).*?$'.format(
                          mail_name=self.mail_name)
                m = re.match(pattern, a_record_str)

                if m:
                    elastic_ip = m.group(1)
                    self.log.info('Using Elastic IP {elastic_ip}...'.
                                  format(elastic_ip=elastic_ip))
                else:
                    raise Exception('Unable to retrieve EIP from record!')
            else:
                raise Exception('Unable to find mail server {mail_name} in '
                                'route53!'.format(mail_name=self.mail_name))
        except Exception, e:
            self.log.critical(str(e))
            raise e

        return elastic_ip

    def assign_eip(self):
        """
        Assigns an EIP to an instance
        """

        instance_id = self.instance.id

        try:
            alloc_id = self.get_alloc_id()
            result = self.ec2.associate_address(instance_id=instance_id,
                                                public_ip=None,
                                                allocation_id=alloc_id,
                                                network_interface_id=None,
                                                private_ip_address=None,
                                                allow_reassociation=True,
                                                dry_run=False)
            if result:
                self.log.info('Successfully assigned EIP: {elastic_ip} '
                              'to {mail_name}'.
                              format(elastic_ip=self.ELASTIC_IP,
                                     mail_name=self.mail_name))
            else:
                raise Exception('Unable to assign EIP: {eip}! '
                                'Exiting...'.format(eip=self.ELASTIC_IP))
        except Exception, e:
            self.log.critical(str(e))
            self.terminate()
            raise e

    def get_alloc_id(self):
        """
        Determine the allocation ID for an EIP.

        :returns: str -- the allocation ID
        """

        alloc_id = None
        try:
            eip_addresses = self.ec2.get_all_addresses()

            for address_obj in eip_addresses:
                address_str = str(address_obj)
                ip = address_str.split(':')[1]
                if ip == self.ELASTIC_IP:
                    alloc_id = address_obj.allocation_id
                    break

            if alloc_id is None:
                raise Exception('The EIP associated with the DNS name for '
                                '{mail_name} does not have an allocation ID '
                                'associated with it. This issue can be '
                                'resolved by migrating the EIP from '
                                'EC2-Classic to EC2-VPC.'.
                                format(mail_name=self.mail_name))

        except Exception, e:
            self.log.critical(str(e))
            self.terminate()
            raise e

        return alloc_id

    def autorun(self):
        """
        Assign the EIP after the instance is up and configured.
        """
        super(PostfixMaster, self).autorun()

        if super(PostfixMaster, self).bake():
            self.assign_eip()
