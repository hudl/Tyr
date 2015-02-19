from exceptions import *
import boto.ec2
import boto.route53
import logging
import sys
import string
import random
import os.path

class Server(object):

    log = logging.getLogger('Servers.Server')
    log.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
            '%(asctime)s [%(name)s] %(levelname)s: %(message)s',
            datefmt='%H:%M:%S')
    ch.setFormatter(formatter)
    log.addHandler(ch)

    def __init__(self, dry=None, verbose=None, size=None, cluster=None,
                    environment=None, ami=None, region=None, role=None,
                    keypair=None, availability_zone=None, security_groups=None,
                    block_devices=None):

        self.dry = dry
        self.verbose = verbose
        self.size = size
        self.cluster = cluster
        self.environment = environment
        self.ami = ami
        self.region = region
        self.role = role
        self.keypair = keypair
        self.availability_zone = availability_zone
        self.security_groups = security_groups
        self.block_devices = block_devices

    def configure(self):

        if self.dry is None:
            self.dry = False

        self.log.info('Using dry value \'{dry}\''.format(dry = self.dry))

        if self.verbose is None:
            self.verbose = False

        self.log.info('Using verbose value \'{verbose}\''.format(
                        verbose = self.verbose))

        if self.size is None:
            self.log.warn('No Instance Type provided')
            self.size = 'm3.medium'

        self.log.info('Using Instance Type \'{size}\''.format(size = self.size))

        if self.cluster is None:
            self.log.warn('No cluster provided')
            raise InvalidCluster('A cluster must be specified.')

        self.log.info('Using Cluster \'{cluster}\''.format(
                        cluster = self.cluster))

        if self.environment is None:
            self.log.warn('No environment provided')
            self.environment = 'test'

        self.log.info('Using Environment \'{environment}\''.format(
                        environment = self.environment))

        if self.region is None:
            self.log.warn('No region provided')
            self.region = 'us-east-1'

        valid = lambda r: r in [region.name for region in boto.ec2.regions()]

        if not valid(self.region):

            error = '\'{region}\' is not a valid EC2 region'.format(
                        region=self.region)
            raise RegionDoesNotExist(error)

        self.log.info('Using EC2 Region \'{region}\''.format(
                        region = self.region))

        self.establish_ec2_connection()
        self.establish_iam_connection()
        self.establish_route53_connection()

        if self.ami is None:
            self.log.warn('No AMI provided')
            self.ami = 'ami-146e2a7c'

        try:
            self.ec2.get_all_images(image_ids=[self.ami])
        except Exception, e:
            if 'Invalid id' in str(e):
                error = '\'{ami}\' is not a valid AMI'.format(ami = self.ami)
                raise InvalidAMI(error)

        self.log.info('Using EC2 AMI \'{ami}\''.format(ami = self.ami))

        if self.role is None:
            self.log.warn('No IAM Role provided')
            self.role = self.environment[0] + '-' + self.cluster

        self.log.info('Using IAM Role \'{role}\''.format(role = self.role))

        self.resolve_iam_role()

        if self.keypair is None:
            self.log.warn('No EC2 Keypair provided')
            self.keypair = 'stage-key'
            if self.environment == 'prod':
                self.keypair = 'bkaiserkey'

        valid = lambda k: k in [pair.name for pair in
                self.ec2.get_all_key_pairs()]

        if not valid(self.keypair):
            error = '\'{keypair}\' is not a valid EC2 keypair'.format(
                        keypair = self.keypair)
            raise InvalidKeyPair(error)

        self.log.info('Using EC2 Key Pair \'{keypair}\''.format(
                        keypair = self.keypair))

        if self.availability_zone is None:
            self.log.warn('No EC2 availability zone provided')
            self.availability_zone = 'c'

        if len(self.availability_zone) == 1:
            self.availability_zone = self.region+self.availability_zone

        valid = lambda z: z in [zone.name for zone in self.ec2.get_all_zones()]

        if not valid(self.availability_zone):
            error = '\'{zone}\' is not a valid EC2 availability zone'.format(
                    zone = self.availability_zone)
            raise InvalidAvailabilityZone(error)

        self.log.info('Using EC2 Availability Zone \'{zone}\''.format(
                        zone = self.availability_zone))

        if self.security_groups is None:
            self.log.warn('No EC2 security groups provided')

            self.security_groups = ['management', 'chef-nodes']
            self.security_groups.append(self.environment[0] + '-' +
                    self.cluster)

        self.log.info('Using security groups {groups}'.format(
                        groups=', '.join(self.security_groups)))

        self.resolve_security_groups()

        if self.block_devices is None:
            self.log.warn('No block devices provided')

            self.block_devices = [{
                                    'type': 'ephemeral',
                                    'name': 'ephemeral0',
                                    'path': 'xvdc'
                                  }]

        self.log.info('Using EC2 block devices {devices}'.format(
                        devices = self.block_devices))

    @property
    def envcl(self):

        template = '{environment}-{cluster}'
        envcl = template.format(environment = self.environment[0],
                                  cluster = self.cluster)

        self.log.info('Using envcl {envcl}'.format(envcl = envcl))

        return envcl

    @property
    def name(self):

        try:
            return self.unique_name
        except Exception:
            pass

        def generate_id(length=4):
            pool = string.ascii_lowercase + string.digits
            return ''.join(random.choice(pool) for _ in range(length))

        def build_name():
            template = '{envcl}-{id}'
            return template.format(envcl = self.envcl, id = generate_id())

        exists = lambda n: len(self.ec2.get_all_instances(
                                filters={'tag:Name': n})) > 0

        name = build_name()

        while exists(name):
            name = build_name()

        self.unique_name = name

        self.log.info('Using node name {name}'.format(name = name))

        return name

    @property
    def hostname(self):

        template = '{name}.thorhudl.com'

        if self.environment == 'stage':
            template = '{name}.app.staghudl.com'
        elif self.environment == 'prod':
            template = '{name}.app.hudl.com'

        hostname = template.format(name = self.name)

        self.log.info('Using hostname {hostname}'.format(hostname = hostname))

        return hostname

    @property
    def user_data(self):

        template = """#!/bin/bash
sed -i '/requiretty/d' /etc/sudoers
hostname {hostname}
echo '127.0.0.1 {fqdn} {hostname}' > /etc/hosts
mkdir /etc/chef
touch /etc/chef/client.rb
echo '{validation_key}' > /etc/chef/validation.pem
echo 'chef_server_url "http://chef.app.hudl.com/"
node_name "{name}"
validation_client_name "chef-validator"' > /etc/chef/client.rb
curl -L https://www.opscode.com/chef/install.sh | bash;
yum install -y gcc
chef-client -S 'http://chef.app.hudl.com/' -N {name} -L {logfile}"""

        validation_key_path = os.path.expanduser('~/.chef/chef-validator.pem')
        validation_key_file = open(validation_key_path, 'r')
        validation_key = validation_key_file.read()

        return template.format(hostname = self.hostname,
                                fqdn = self.hostname,
                                validation_key = validation_key,
                                name = self.name,
                                logfile = '/var/log/chef-client.log')

    @property
    def tags(self):

        tags = {}
        tags['Name'] = self.name
        tags['Environment'] = self.environment
        tags['Cluster'] = self.cluster

        self.log.info('Using instance tags {tags}'.format(tags = tags))

        return tags

    @property
    def blockdevicemapping(self):

        bdm = boto.ec2.blockdevicemapping.BlockDeviceMapping()

        self.log.info('Created new Block Device Mapping')

        for d in self.block_devices:

            device = boto.ec2.blockdevicemapping.BlockDeviceType()

            if 'size' in d.keys():
                device.size = d['size']

            if d['type'] == 'ephemeral':
                device.ephemeral_name = d['name']

            bdm['/dev/'+d['path']] = device

            if d['type'] == 'ephemeral':
                if 'size' in d.keys():
                    self.log.info("""Created new ephemeral device at {path} 
named {name} of size {size}""".format(path = d['path'], name = d['name'],
                                        size = d['size']))
                else:
                    self.log.info("""Created new ephemeral device at {path} 
named {name}""".format(path = d['path'], name = d['name']))

            else:
                self.log.info("""Created new EBS device at {path} of size 
{size}""".format(path = d['path'], size = d['size']))

        return bdm

    def resolve_security_groups(self):

        exists = lambda s: s in [group.name for group in
                self.ec2.get_all_security_groups()]

        for group in self.security_groups:
            if not exists(group):
                self.log.info('Security Group {group} does not exist'.format(
                                group = group))
                self.ec2.create_security_group(group, group)
                self.log.info('Created security group {group}'.format(
                                group = group))
            else:
                self.log.info('Security Group {group} already exists'.format(
                                group = group))

    def resolve_iam_role(self):

        try:
            instance_profile = self.iam.create_instance_profile(self.role)
            self.log.info('Created IAM Profile {profile}'.format(
                            profile = self.role))

        except Exception, e:
            if 'EntityAlreadyExists' in str(e):
                self.log.info('IAM Profile {profile} already exists'.format(
                            profile = self.role))
            else:
                raise e

        try:
            role = self.iam.create_role(self.role)
            self.log.info('Created IAM Role {role}'.format(role = self.role))
            self.iam.add_role_to_instance_profile(self.role, self.role)
            self.log.info('Attached Role {role} to Profile {profile}'.format(
                            role = self.role, profile = self.role))

        except Exception, e:
            if 'EntityAlreadyExists' in str(e):
                self.log.info('IAM Role {role} already exists'.format(
                                role = self.role))
            else:
                raise e

    def establish_ec2_connection(self):

        self.log.info('Using EC2 Region \'{region}\''.format(
                        region=self.region))
        self.log.info("Attempting to connect to EC2")

        try:
            self.ec2 = boto.ec2.connect_to_region(self.region)

            if self.verbose:
                self.log.info('Established connection to EC2')
        except Exception, e:
            raise e

    def establish_iam_connection(self):

        try:
            self.iam = boto.connect_iam()
            self.log.info('Established connection to IAM')
        except Exception, e:
            raise e

    def establish_route53_connection(self):

        try:
            self.route53 = boto.route53.connect_to_region(self.region)
            self.log.info('Established connection to Route53')
        except Exception, e:
            raise e

    def launch(self, wait=False):

        parameters = {
                'image_id': self.ami,
                'instance_profile_name': self.role,
                'key_name': self.keypair,
                'instance_type': self.size,
                'security_groups': self.security_groups,
                'block_device_map': self.blockdevicemapping,
                'user_data': self.user_data,
                'placement': self.availability_zone}

        reservation = self.ec2.run_instances(**parameters)

        self.instance = reservation.instances[0]

        if wait:
            state = self.instance.state

            while not(state == 'running'):
                try:
                    self.instance.update()
                    state = self.instance.state
                except Exception:
                    pass

            return

    def tag(self):
        self.ec2.create_tags([self.instance.id], self.tags)

    def route(self):
        zone_address = self.hostname[len(self.name)+1:]

        try:
            zone = self.route53.get_zone(zone_address)
        except Exception, e:
            raise e

        name = self.hostname + '.'

        if zone.get_cname(name) is None:
            try:
                zone.add_cname(name, self.instance.public_dns_name)
            except Exception, e:
                raise e
        else:
            zone.update_cname(name, self.instance.public_dns_name)

    def autorun(self):

        self.configure()
        self.launch(wait=True)
        self.tag()
        self.route()
