from exceptions import *
import boto.ec2
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
        return template.format(environment = self.environment[0],
                               cluster = self.cluster)
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

        return name

    @property
    def hostname(self):

        template = '{name}.thorhudl.com'

        if self.environment == 'stage':
            template = '{name}.app.staghudl.com'
        elif self.environment == 'prod':
            template = '{name}.app.hudl.com'

        return template.format(name = self.name)

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

        return tags

    @property
    def blockdevicemapping(self):

        bdm = boto.ec2.blockdevicemapping.BlockDeviceMapping()

        for d in self.block_devices:

            device = boto.ec2.blockdevicemapping.BlockDeviceType()

            if 'size' in d.keys():
                device.size = d['size']

            if d['type'] == 'ephemeral':
                device.ephemeral_name = d['name']

            bdm['/dev/'+d['path']] = device

        return bdm

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

    def autorun(self):

        self.configure()
