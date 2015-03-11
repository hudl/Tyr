from exceptions import *
import boto.ec2
import boto.route53
import logging
import sys
import string
import random
import os.path
import chef
import time
from paramiko.client import AutoAddPolicy, SSHClient

class Server(object):

    def __init__(self, dry=None, verbose=None, size=None, cluster=None,
                    environment=None, ami=None, region=None, role=None,
                    keypair=None, availability_zone=None, security_groups=None,
                    block_devices=None, chef_path=None, role_policies=None):

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
        self.chef_path = chef_path
        self.role_policies = role_policies

    def establish_logger(self):

        try:
            return self.log
        except:
            pass

        log = logging.getLogger(self.__class__.__name__)
        log.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
                '%(asctime)s [%(name)s] %(levelname)s: %(message)s',
                datefmt='%H:%M:%S')
        ch.setFormatter(formatter)
        log.addHandler(ch)

        self.log = log

    def configure(self):

        if self.dry is None:
            self.dry = False

        self.log.info('Using dry value "{dry}"'.format(dry = self.dry))

        if self.verbose is None:
            self.verbose = False

        self.log.info('Using verbose value "{verbose}"'.format(
                        verbose = self.verbose))

        if self.size is None:
            self.log.warn('No Instance Type provided')
            self.size = 'm3.medium'

        self.log.info('Using Instance Type "{size}"'.format(size = self.size))

        if self.cluster is None:
            self.log.warn('No cluster provided')
            raise InvalidCluster('A cluster must be specified.')

        self.log.info('Using Cluster "{cluster}"'.format(
                        cluster = self.cluster))

        if self.environment is None:
            self.log.warn('No environment provided')
            self.environment = 'test'

        self.environment = self.environment.lower()

        self.log.info('Using Environment "{environment}"'.format(
                        environment = self.environment))

        if self.region is None:
            self.log.warn('No region provided')
            self.region = 'us-east-1'

        valid = lambda r: r in [region.name for region in boto.ec2.regions()]

        if not valid(self.region):

            error = '"{region}" is not a valid EC2 region'.format(
                        region=self.region)
            raise RegionDoesNotExist(error)

        self.log.info('Using EC2 Region "{region}"'.format(
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
            self.log.error(str(e))
            if 'Invalid id' in str(e):
                error = '"{ami}" is not a valid AMI'.format(ami = self.ami)
                raise InvalidAMI(error)

        self.log.info('Using EC2 AMI "{ami}"'.format(ami = self.ami))

        if self.role is None:
            self.log.warn('No IAM Role provided')
            self.role = self.environment[0] + '-' + self.cluster

        self.log.info('Using IAM Role "{role}"'.format(role = self.role))

        if self.role_policies is None:
            self.log.warn('No IAM Role Policies provided')
            self.role_policies = {}

        self.log.info('Using IAM Role Policies {policies}'.format(
                                            policies = self.role_policies))

        self.resolve_iam_role()

        if self.keypair is None:
            self.log.warn('No EC2 Keypair provided')
            self.keypair = 'stage-key'
            if self.environment == 'prod':
                self.keypair = 'bkaiserkey'

        valid = lambda k: k in [pair.name for pair in
                self.ec2.get_all_key_pairs()]

        if not valid(self.keypair):
            error = '"{keypair}" is not a valid EC2 keypair'.format(
                        keypair = self.keypair)
            raise InvalidKeyPair(error)

        self.log.info('Using EC2 Key Pair "{keypair}"'.format(
                        keypair = self.keypair))

        if self.availability_zone is None:
            self.log.warn('No EC2 availability zone provided')
            self.availability_zone = 'c'

        if len(self.availability_zone) == 1:
            self.availability_zone = self.region+self.availability_zone

        valid = lambda z: z in [zone.name for zone in self.ec2.get_all_zones()]

        if not valid(self.availability_zone):
            error = '"{zone}" is not a valid EC2 availability zone'.format(
                    zone = self.availability_zone)
            raise InvalidAvailabilityZone(error)

        self.log.info('Using EC2 Availability Zone "{zone}"'.format(
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

        if self.chef_path is None:
            self.log.warn('No Chef path provided')
            self.chef_path = '~/.chef'

        self.chef_path = os.path.expanduser(self.chef_path)

        self.log.info('Using Chef path "{path}"'.format(
                                path = self.chef_path))



    def next_index(self, template='{envcl}-{zone}-', supplemental={}, cap=99):

        try:
            return self.index
        except Exception:
            pass

        supplemental['envcl'] = self.envcl
        template = template+'*'

        name_filter = template.format(**supplemental)

        filters = {
            'tag:Name': name_filter,
            'instance-state-name': 'running'
        }

        reservations = self.ec2.get_all_instances(filters=filters)

        instances = []

        for reservation in reservations:
            instances.extend(reservation.instances)

        names = [instance.tags['Name'] for instance in instances]

        indexes = [name.split('-')[-1] for name in names]
        indexes = [int(index) for index in indexes if index.isdigit()]

        index = -1

        for i in range(cap):
            if (i+1) not in indexes:
                index = i+1
                break

        index = str(index)

        if cap > 9:
            if len(index) < 2:
                index = '0' + index

        self.index = index

        return index

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

        self.unique_name = self.build_name()

        return self.unique_name

    def build_name(self, template='{envcl}-{zone}-{index}', supplemental={},
                    search_prefix='{envcl}-{zone}-', cap=99):

        supplemental['zone'] = self.availability_zone[-1:]
        supplemental['envcl'] = self.envcl

        index = self.next_index(search_prefix, supplemental, cap)

        supplemental['index'] = index

        name = template.format(**supplemental)

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
        tags['Group'] = self.cluster.split('-')[0]
        tags['Role'] = 'Role'+self.cluster.split('-')[1].capitalize()

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
                self.log.error(str(e))
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
                self.log.error(str(e))
                raise e

        role_policies = self.iam.list_role_policies(self.role)
        response = role_policies['list_role_policies_response']
        result = response['list_role_policies_result']
        policies = result['policy_names']

        self.log.info('Existing policies: {policies}'.format(policies=policies))

        for policy, document in self.role_policies.iteritems():

            self.log.info('Processing policy "{policy}"'.format(policy=policy))

            if policy not in policies:

                self.log.info('Policy "{policy}" does not exist'.format(
                                        policy = policy))

                try:
                    self.iam.put_role_policy(self.role, policy, document)

                    self.log.info('Added policy "{policy}"'.format(
                                        policy = policy))
                except Exception, e:
                    self.log.error(str(e))
                    raise e

            else:

                self.log.info('Policy "{policy}" already exists'.format(
                                        policy = policy))

                if document == self.iam.get_role_policy(self.role, policy):

                    self.log.info('Policy "{policy}" is accurate'.format(
                                        policy = policy))

                else:

                    self.log.warn('Policy "{policy}" has been modified'.format(
                                        policy = policy))

                    try:
                        self.iam.delete_role_policy(self.role, policy)

                        self.log.info('Removed policy "{policy}"'.format(
                                            policy = policy))
                    except Exception, e:
                        self.log.error(str(e))
                        raise e

                    try:
                        self.iam.put_role_policy(self.role, policy, document)

                        self.log.info('Added policy "{policy}"'.format(
                                            policy = policy))
                    except Exception, e:
                        self.log.error(str(e))
                        raise e

    def establish_ec2_connection(self):

        self.log.info('Using EC2 Region "{region}"'.format(
                        region=self.region))
        self.log.info("Attempting to connect to EC2")

        try:
            self.ec2 = boto.ec2.connect_to_region(self.region)

            if self.verbose:
                self.log.info('Established connection to EC2')
        except Exception, e:
            self.log.error(str(e))
            raise e

    def establish_iam_connection(self):

        try:
            self.iam = boto.connect_iam()
            self.log.info('Established connection to IAM')
        except Exception, e:
            self.log.error(str(e))
            raise e

    def establish_route53_connection(self):

        try:
            self.route53 = boto.route53.connect_to_region(self.region)
            self.log.info('Established connection to Route53')
        except Exception, e:
            self.log.error(str(e))
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

        self.log.info('Successfully launched EC2 instance')

        self.instance = reservation.instances[0]

        if wait:
            self.log.info('Waiting until the instance is running to return')

            state = self.instance.state

            while not(state == 'running'):
                try:
                    self.instance.update()
                    state = self.instance.state
                except Exception:
                    self.log.error(str(e))
                    pass

            self.log.info('The instance is running')
            return

    def tag(self):
        self.ec2.create_tags([self.instance.id], self.tags)
        self.log.info('Tagged instance with {tags}'.format(tags = self.tags))

    def route(self):
        zone_address = self.hostname[len(self.name)+1:]

        self.log.info('Using Zone Address {address}'.format(
                            address = zone_address))

        try:
            zone = self.route53.get_zone(zone_address)
            self.log.info('Retrieved zone from Route53')
        except Exception, e:
            self.log.error(str(e))
            raise e

        name = self.hostname + '.'
        self.log.info('Using record name {name}'.format(name = name))
        self.log.info('Using record value {value}'.format(
                        value = self.instance.public_dns_name))

        if zone.get_cname(name) is None:
            self.log.info('The CNAME record does not exist')
            try:
                zone.add_cname(name, self.instance.public_dns_name)
                self.log.info('Created new CNAME record')
            except Exception, e:
                self.log.error(str(e))
                raise e
        else:
            self.log.info('The CNAME record already exists')
            zone.update_cname(name, self.instance.public_dns_name)
            self.log.info('Updated the CNAME record')

    @property
    def connection(self):

        try:
            connection = self.ssh_connection

            self.log.info('Determining is SSH transport is still active')
            transport = connection.get_transport()

            if not transport.is_active():
                self.log.warn('SSH transport is no longer active')
                self.log.info('Proceeding to re-establish SSH connection')
                raise Exception()

            else:
                self.log.info('SSH transport is still active')
                return connection
        except Exception:
            pass

        connection = SSHClient()
        connection.set_missing_host_key_policy(AutoAddPolicy())

        self.log.info('Attempting to establish SSH connection')

        while True:
            try:
                connection.connect(self.hostname,
                        username = 'ec2-user')
                break
            except Exception:
                self.log.warn('Unable to establish SSH connection')
                time.sleep(10)

        self.log.info('Successfully established SSH connection')

        self.ssh_connection = connection

        return connection

    def run(self, command):

        with self.connection as conn:

            state = {
                        'in': None,
                        'out': None,
                        'err': None
                    }

            stdin, stdout, stderr = conn.exec_command(command)

            try:
                state['in'] = stdin.read()
            except IOError:
                pass

            try:
                state['out'] = stdout.read()
            except IOError:
                pass

            try:
                state['err'] = stderr.read()
            except IOError:
                pass

            return state

    def bake(self):

        chef_path = os.path.expanduser(self.chef_path)
        self.chef_api = chef.autoconfigure(chef_path)

        chef_api = self.chef_api

        try:
            node = chef.Node(self.name, api=chef_api)
            node.delete()

            self.log.info('Removed previous chef node "{node}"'.format(
                                node = self.name))
        except chef.exceptions.ChefServerNotFoundError:
            pass
        except Exception as e:
            self.log.error(str(e))
            raise e

        try:
            client = chef.Client(self.name, api=chef_api)
            client = client.delete()

            self.log.info('Removed previous chef client "{client}"'.format(
                                client = self.name))
        except chef.exceptions.ChefServerNotFoundError:
            pass
        except Exception as e:
            self.log.error(str(e))
            raise e

    def baked(self):

        self.log.info('Determining status of "{node}"'.format(
                                            node = self.hostname))

        self.log.info('Waiting for Chef Client to start')

        while True:
            r = self.run('ls -l /var/log')

            if 'chef-client.log' in r['out']:
                break
            else:
                time.sleep(10)

        self.log.info('Chef Client has started')

        self.log.info('Waiting for Chef Client to finish')

        while True:
            r = self.run('pgrep chef-client')

            if len(r['out']) > 0:
                time.sleep(10)
            else:
                break

        self.log.info('Chef Client has finished')

        self.log.info('Determining Node state')

        r = self.run('tail /var/log/chef-client.log')

        if 'Chef Run complete in' in r['out']:
            self.log.info('Chef Client was successful')
            return True
        else:
            self.log.info('Chef Client was not successful')
            self.log.debug(r['out'])
            return False

    def autorun(self):

        self.establish_logger()
        self.configure()
        self.launch(wait=True)
        self.tag()
        self.route()
        self.bake()
