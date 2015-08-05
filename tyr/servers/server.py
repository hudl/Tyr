from exceptions import *
import boto.ec2
import boto.route53
import boto.ec2.networkinterface
import logging
import os
import chef
import time
from boto.ec2.networkinterface import NetworkInterfaceSpecification
import json
from boto.ec2.networkinterface import NetworkInterfaceCollection
import urllib
from boto.vpc import VPCConnection
from paramiko.client import AutoAddPolicy, SSHClient
from tyr.policies import policies
from tyr.utilities.stackdriver import (set_maintenance_mode,
                                       unset_maintenance_mode)


class Server(object):

    NAME_TEMPLATE = '{envcl}-{location}-{index}'
    NAME_SEARCH_PREFIX = '{envcl}-{location}-'
    NAME_AUTO_INDEX = True

    IAM_ROLE_POLICIES = []

    CHEF_RUNLIST = ['role[RoleBase]']
    STACKDRIVER_API_KEY  = os.environ.get('STACKDRIVER_API_KEY', False)
    STACKDRIVER_USERNAME = os.environ.get('STACKDRIVER_USERNAME', False)

    def __init__(self, group=None, server_type=None, instance_type=None,
                 environment=None, ami=None, region=None, role=None,
                 keypair=None, availability_zone=None, security_groups=None,
                 block_devices=None, chef_path=None, subnet_id=None,
                 dns_zones=None):

        self.instance_type = instance_type
        self.group = group
        self.server_type = server_type
        self.environment = environment
        self.ami = ami
        self.region = region
        self.role = role
        self.keypair = keypair
        self.availability_zone = availability_zone
        self.security_groups = security_groups
        self.block_devices = block_devices
        self.chef_path = chef_path
        self.dns_zones = dns_zones
        self.subnet_id = subnet_id
        self.vpc_id = None

    def establish_logger(self):

        try:
            return self.log
        except:
            pass

        log = logging.getLogger(self.__class__.__name__)

        if not log.handlers:
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

        if self.instance_type is None:
            self.log.warn('No Instance Type provided')
            self.instance_type = 't2.medium'

        self.log.info('Using Instance Type "{instance_type}"'.format(
                                            instance_type=self.instance_type))

        if self.group is None:
            self.log.warn('No group provided')
            raise InvalidCluster('A group must be specified.')

        self.log.info('Using group "{group}"'.format(
                        group=self.group))

        if self.server_type is None:
            self.log.warn('No type provided')
            raise InvalidCluster('A type must be specified.')

        self.log.info('Using type "{server_type}"'.format(
                        server_type=self.server_type))

        if self.environment is None:
            self.log.warn('No environment provided')
            self.environment = 'test'

        self.environment = self.environment.lower()

        self.log.info('Using Environment "{environment}"'.format(
                        environment=self.environment))

        if self.region is None:
            self.log.warn('No region provided')
            self.region = 'us-east-1'

        valid = lambda r: r in [region.name for region in boto.ec2.regions()]

        if not valid(self.region):

            error = '"{region}" is not a valid EC2 region'.format(
                        region=self.region)
            raise RegionDoesNotExist(error)

        self.log.info('Using EC2 Region "{region}"'.format(
                        region=self.region))

        self.establish_ec2_connection()
        self.establish_iam_connection()
        self.establish_route53_connection()

        if self.ami is None:
            self.log.warn('No AMI provided')
            self.ami = 'ami-1ecae776'

        try:
            self.ec2.get_all_images(image_ids=[self.ami])
        except Exception, e:
            self.log.error(str(e))
            if 'Invalid id' in str(e):
                error = '"{ami}" is not a valid AMI'.format(ami=self.ami)
                raise InvalidAMI(error)

        self.log.info('Using EC2 AMI "{ami}"'.format(ami=self.ami))

        if self.role is None:
            self.log.warn('No IAM Role provided')
            self.role = self.envcl

        self.log.info('Using IAM Role "{role}"'.format(role=self.role))

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
                        keypair=self.keypair)
            raise InvalidKeyPair(error)

        self.log.info('Using EC2 Key Pair "{keypair}"'.format(
                        keypair=self.keypair))

        if self.subnet_id is None:
            if self.availability_zone is None:
                self.log.warn('No EC2 availability zone provided,'
                              ' using zone c')
                self.availability_zone = 'c'
        else:
            if self.availability_zone is not None:
                self.log.warn('Both availability zone and subnet set, '
                              'using availability zone from subnet')

            self.vpc_id = self.get_subnet_vpc_id(self.subnet_id)
            self.log.info("Using VPC {vpc_id}".format(vpc_id=self.vpc_id))
            self.availability_zone = self.get_subnet_availability_zone(
                                        self.subnet_id)
            self.log.info("Using VPC, using availability zone " +
                          "{availability_zone}".format(
                           availability_zone=self.availability_zone))

        if len(self.availability_zone) == 1:
            self.availability_zone = self.region+self.availability_zone

        valid = lambda z: z in [zone.name for zone in self.ec2.get_all_zones()]

        if not valid(self.availability_zone):
            error = '"{zone}" is not a valid EC2 availability zone'.format(
                    zone=self.availability_zone)
            raise InvalidAvailabilityZone(error)

        self.log.info('Using EC2 Availability Zone "{zone}"'.format(
                        zone=self.availability_zone))

        if self.security_groups is None:
            self.log.warn('No EC2 security groups provided')

            self.security_groups = ['management', 'chef-nodes']
            self.security_groups.append(self.envcl)

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
                        devices=self.block_devices))

        if self.chef_path is None:
            self.log.warn('No Chef path provided')
            self.chef_path = '~/.chef'

        self.chef_path = os.path.expanduser(self.chef_path)

        self.log.info('Using Chef path "{path}"'.format(
                                path=self.chef_path))

        if self.dns_zones is None:
            self.log.warn('No DNS zones specified')
            self.dns_zones = [
                {
                    'id': {
                        'prod': 'ZDQ066NWSBGCZ',
                        'stage': 'Z3ETV7KVCRERYL',
                        'test': 'ZAH3O4H1900GY'
                    },
                    'records': [
                        {
                            'type': 'CNAME',
                            'name': '{name}.external.{dns_zone}.',
                            'value': '{dns_name}',
                            'ttl': 60
                        },
                        {
                            'type': 'CNAME',
                            'name': '{hostname}.',
                            'value': '{private_dns_name}',
                            'ttl': 60
                        }
                    ]
                },
                {
                    'id': {
                        'prod': 'Z1LKTAOOYM3H8T',
                        'stage': 'Z24UEMQ8K6Z50Z',
                        'test': 'ZXXFTW7F1WFIS'
                    },
                    'records': [
                        {
                            'type': 'CNAME',
                            'name': '{hostname}.',
                            'value': '{private_dns_name}',
                            'ttl': 60
                        }
                    ]
                }
            ]

    @property
    def location(self):

        region_map = {
                'ap-northeast-1': 'apne1',
                'ap-southeast-1': 'apse1',
                'ap-southeast-2': 'apse2',
                'eu-central-1': 'euc1',
                'eu-west-1': 'euw1',
                'sa-east-1': 'sae1',
                'us-east-1': 'use1',
                'us-west-1': 'usw1',
                'us-west-2': 'usw2',
        }

        return '{region}{zone}'.format(region=region_map[self.region],
                                       zone=self.availability_zone[-1:])

    def next_index(self, supplemental={}):

        try:
            return self.index
        except Exception:
            pass

        template = self.NAME_SEARCH_PREFIX+'*'

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

        for i in range(99):
            if (i+1) not in indexes:
                index = i+1
                break

        self.index = str(index)

        if len(self.index) == 1:
            self.index = '0'+self.index

        return self.index

    @property
    def envcl(self):

        template = '{environment}-{group}-{server_type}'
        envcl = template.format(environment=self.environment[0],
                                group=self.group,
                                server_type=self.server_type)

        self.log.info('Using envcl {envcl}'.format(envcl=envcl))

        return envcl

    @property
    def name(self):

        try:
            return self.unique_name
        except Exception:
            pass

        template = self.NAME_TEMPLATE

        supplemental = self.__dict__.copy()

        supplemental['envcl'] = self.envcl
        supplemental['location'] = self.location

        if self.NAME_AUTO_INDEX:

            index = self.next_index(supplemental)
            supplemental['index'] = index

        self.unique_name = template.format(**supplemental)

        self.log.info('Using node name {name}'.format(name=self.unique_name))

        return self.unique_name

    @property
    def hostname(self):

        template = '{name}.thorhudl.com'

        if self.environment == 'stage':
            template = '{name}.app.staghudl.com'
        elif self.environment == 'prod':
            template = '{name}.app.hudl.com'

        hostname = template.format(name=self.name)

        self.log.info('Using hostname {hostname}'.format(hostname=hostname))

        return hostname

    @property
    def user_data(self):

        template = """#!/bin/bash
sed -i '/requiretty/d' /etc/sudoers
hostname {hostname}
mkdir /etc/chef
touch /etc/chef/client.rb
mkdir -p /etc/chef/ohai/hints
touch /etc/chef/ohai/hints/ec2.json
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

        return template.format(hostname=self.hostname,
                               validation_key=validation_key,
                               name=self.name,
                               logfile='/var/log/chef-client.log')

    @property
    def tags(self):

        tags = {}
        tags['Name'] = self.name
        tags['Environment'] = self.environment
        tags['Group'] = self.group
        tags['Role'] = 'Role'+self.server_type.capitalize()

        self.log.info('Using instance tags {tags}'.format(tags=tags))

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
named {name} of size {size}""".format(path=d['path'], name=d['name'],
                                      size=d['size']))
                else:
                    self.log.info("""Created new ephemeral device at {path}
named {name}""".format(path=d['path'], name=d['name']))

            else:
                self.log.info("""Created new EBS device at {path} of size
{size}""".format(path=d['path'], size=d['size']))

        return bdm

    def get_subnet_vpc_id(self, subnet_id):
        vpc_conn = VPCConnection()
        subnets = vpc_conn.get_all_subnets(
            filters={'subnet_id': subnet_id})
        if len(subnets) == 1:
            vpc_id = subnets[0].vpc_id
            return vpc_id
        elif len(subnets) == 0:
            raise NoSubnetReturned("No subnets returned")
        else:
            raise Exception("More than 1 subnet returned")

    def resolve_security_groups(self):
        filters = {}
        self.log.info("Resolving security groups")

        # If the server is being spun up in a vpc, search only that vpc
        exists = lambda s: s in [group.name for group in
                                 self.ec2.get_all_security_groups()
                                 if self.vpc_id == group.vpc_id]

        for index, group in enumerate(self.security_groups):

            if not exists(group):
                self.log.info('Security Group {group} does not exist'.format(
                                group=group))
                if self.subnet_id is None:
                    self.ec2.create_security_group(group, group)
                else:
                    vpc_conn = VPCConnection()
                    vpc_conn.create_security_group(
                        group, group, vpc_id=self.vpc_id)
                self.log.info('Created security group {group}'.format(
                                group=group))
            else:
                self.log.info('Security Group {group} already exists'.format(
                                group=group))

    def resolve_iam_role(self):

        role_exists = False
        profile_exists = False

        try:
            profile = self.iam.get_instance_profile(self.role)
            profile_exists = True
        except Exception, e:
            if '404 Not Found' in str(e):
                pass
            else:
                self.log.error(str(e))
                raise e

        if not profile_exists:
            try:
                instance_profile = self.iam.create_instance_profile(self.role)
                self.log.info('Created IAM Profile {profile}'.format(
                                profile=self.role))

            except Exception, e:
                self.log.error(str(e))
                raise e

        try:
            role = self.iam.get_role(self.role)
            role_exists = True
        except Exception, e:
            if '404 Not Found' in str(e):
                pass
            else:
                self.log.error(str(e))
                raise e

        if not role_exists:

            try:
                role = self.iam.create_role(self.role)
                self.log.info('Created IAM Role {role}'.format(role=self.role))
                self.iam.add_role_to_instance_profile(self.role, self.role)
                self.log.info('Attached Role {role}'
                              ' to Profile {profile}'.format(
                                role=self.role, profile=self.role))

            except Exception, e:
                self.log.error(str(e))
                raise e

        role_policies = self.iam.list_role_policies(self.role)
        response = role_policies['list_role_policies_response']
        result = response['list_role_policies_result']
        existing_policies = result['policy_names']

        self.log.info('Existing policies: '
                      '{policies}'.format(policies=existing_policies))

        for policy_template in self.IAM_ROLE_POLICIES:
            policy = policy_template.format(environment=self.environment)

            self.log.info('Processing policy "{policy}"'.format(policy=policy))

            if policy not in existing_policies:

                rolePolicy = policies[policy]

                if rolePolicy is None:
                    self.log.info("No policy defined for {policy}".format(
                                  policy=policy))
                    continue  # Go to the next policy

                self.log.info('Policy "{policy}" does not exist'.format(
                                        policy=policy))

                try:
                    self.iam.put_role_policy(self.role, policy,
                                             rolePolicy)

                    self.log.info('Added policy "{policy}"'.format(
                                        policy=policy))
                except Exception, e:
                    self.log.error(str(e))
                    raise e

            else:

                self.log.info('Policy "{policy}" already exists'.format(
                                        policy=policy))

                tyr_copy = json.loads(policies[policy])

                aws_copy = self.iam.get_role_policy(self.role, policy)
                aws_copy = aws_copy['get_role_policy_response']
                aws_copy = aws_copy['get_role_policy_result']
                aws_copy = aws_copy['policy_document']
                aws_copy = urllib.unquote(aws_copy)
                aws_copy = json.loads(aws_copy)

                if tyr_copy == aws_copy:
                    self.log.info('Policy "{policy}" is accurate'.format(
                                        policy=policy))

                else:

                    self.log.warn('Policy "{policy}" has been modified'.format(
                                        policy=policy))

                    try:
                        self.iam.delete_role_policy(self.role, policy)

                        self.log.info('Removed policy "{policy}"'.format(
                                            policy=policy))
                    except Exception, e:
                        self.log.error(str(e))
                        raise e

                    try:
                        self.iam.put_role_policy(self.role, policy,
                                                 policies[policy])

                        self.log.info('Added policy "{policy}"'.format(
                                            policy=policy))
                    except Exception, e:
                        self.log.error(str(e))
                        raise e

    def establish_ec2_connection(self):

        self.log.info('Using EC2 Region "{region}"'.format(
                        region=self.region))
        self.log.info("Attempting to connect to EC2")

        try:
            self.ec2 = boto.ec2.connect_to_region(self.region)
            self.log.info('Established connection to EC2')
        except Exception, e:
            self.log.error(str(e))
            raise e

    def get_subnet_availability_zone(self, subnet_id):
        self.log.info(
            "getting zone for subnet {subnet_id}".format(subnet_id=subnet_id))
        vpc_conn = VPCConnection()
        filters = {'subnet-id': subnet_id}
        subnets = vpc_conn.get_all_subnets(filters=filters)

        if len(subnets) == 1:
            availability_zone = subnets[0].availability_zone

            log_message = 'Subnet {subnet_id} is in ' \
                          'availability zone {availability_zone}'
            self.log.info(log_message.format(
                            subnet_id=subnet_id,
                            availability_zone=availability_zone))
            return availability_zone

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

    def get_security_group_ids(self, security_groups, vpc_id=None):
            security_group_ids = []
            for group in security_groups:
                filters = {'group-name': group}

                security_groups = [group for group in
                                   self.ec2.get_all_security_groups(
                                    filters=filters)
                                   if self.vpc_id == group.vpc_id]

                if len(security_groups) == 1:
                    security_group_ids.append(security_groups[0].id)
                elif len(security_groups) == 0:
                    raise NoSecurityGroupsReturned(
                        "No security group returned.")
                else:
                    raise MultipleSecurityGroupsReturned(
                        "More than 1 security group returned")

            return security_group_ids

    def launch(self, wait=False):
        self.security_group_ids = self.get_security_group_ids(
            self.security_groups, self.vpc_id)

        self.log.info(
            "Using Security group ids: {ids}".format(
                ids=self.security_group_ids))

        parameters = {
                'image_id': self.ami,
                'instance_profile_name': self.role,
                'key_name': self.keypair,
                'instance_type': self.instance_type,
                'block_device_map': self.blockdevicemapping,
                'user_data': self.user_data}

        if self.subnet_id is None:
            parameters.update({
                'placement': self.availability_zone,
                'security_group_ids': self.security_group_ids,
            })
        else:
            interface = NetworkInterfaceSpecification(
                subnet_id=self.subnet_id,
                groups=self.security_group_ids,
                associate_public_ip_address=True)
            interfaces = NetworkInterfaceCollection(
                interface)
            parameters.update({
                'network_interfaces': interfaces
            })

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
                    pass

            self.log.info('The instance is running')
            return

    def tag(self):
        self.ec2.create_tags([self.instance.id], self.tags)
        self.log.info('Tagged instance with {tags}'.format(tags=self.tags))

    def route(self, wait=False):

        for dns_zone in self.dns_zones:

            self.log.info('Routing Hosted Zone {zone}'.format(zone=dns_zone))

            for z in self.route53.get_zones():
                if z.id == dns_zone['id'][self.environment]:
                    zone = z
                    break

            self.log.info('Using Zone Address {zone}'.format(zone=zone.name))

            for record in dns_zone['records']:

                self.log.info('Processing DNS record {record}'.format(
                                                                record=record))

                formatting_params = {
                    'hostname': self.hostname,
                    'name': self.name,
                    'instance_id': self.instance.id,
                    'vpc_id': self.instance.vpc_id,
                    'ip_address': self.instance.ip_address,
                    'dns_name': self.instance.dns_name,
                    'private_ip_address': self.instance.private_ip_address,
                    'private_dns_name': self.instance.private_dns_name,
                    'dns_zone': self.hostname[len(self.name)+1:]
                }

                record['name'] = record['name'].format(**formatting_params)
                record['value'] = record['value'].format(**formatting_params)

                self.log.info('Adding DNS record {record}'.format(
                                                            record=record))

                existing_records = zone.find_records(name=record['name'],
                                                     type=record['type'])

                if existing_records:
                    self.log.info('The DNS record already exists')
                    zone.delete_record(existing_records)
                    self.log.info('The existing DNS record was deleted')

                try:
                    status = zone.add_record(record['type'], record['name'],
                                             record['value'],
                                             ttl=record['ttl'])

                    if wait:
                        while status.update() != 'INSYNC':
                            self.log.debug('Waiting for DNS '
                                           'change to propagate')
                            time.sleep(10)

                    self.log.info('Added new DNS record')
                except Exception, e:
                    self.log.error(str(e))
                    raise e

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
                keys = ['~/.ssh/stage', '~/.ssh/prod']
                keys = [os.path.expanduser(key) for key in keys]

                connection.connect(self.instance.private_dns_name,
                                   username='ec2-user',
                                   key_filename=keys)
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

    def terminate(self):
        """
        Terminate a node from AWS
        """

        address = self.instance.private_ip_address
        instance_id = self.instance.id

        self.log.info('The instance ID is {id_}'.format(id_=instance_id))

        set_maintenance_mode(instance_id)

        self.log.info('Terminating node at {address}'.format(address=address))
        response = self.ec2.terminate_instances(instance_ids=[instance_id])

        self.log.info('Received the response {response}'.format(response=response))

        terminated = [instance.id for instance in response]

        if instance_id in terminated:
            self.log.info('Successfully terminated {instance}'.format(
                                                        instance=instance_id))
        else:
            self.log.info('Failed to terminate {instance}'.format(
                                                    instance=instance_id))

    def bake(self):

        chef_path = os.path.expanduser(self.chef_path)
        self.chef_api = chef.autoconfigure(chef_path)

        with self.chef_api:
            try:
                node = chef.Node(self.name)
                node.delete()

                self.log.info('Removed previous chef node "{node}"'.format(
                                node=self.name))
            except chef.exceptions.ChefServerNotFoundError:
                pass
            except Exception as e:
                self.log.error(str(e))
                raise e

            try:
                client = chef.Client(self.name)
                client = client.delete()

                self.log.info('Removed previous chef client "{client}"'.format(
                                client=self.name))
            except chef.exceptions.ChefServerNotFoundError:
                pass
            except Exception as e:
                self.log.error(str(e))
                raise e

            node = chef.Node.create(self.name)

            self.chef_node = node

            self.log.info('Created new Chef Node "{node}"'.format(
                                node=self.name))

            self.chef_node.chef_environment = self.environment

            self.log.info('Set the Chef Environment to "{env}"'.format(
                        env=self.chef_node.chef_environment))

            self.chef_node.run_list = self.CHEF_RUNLIST

            self.log.info('Set Chef run list to {list}'.format(
                                            list=self.chef_node.run_list))

            self.chef_node.save()
            self.log.info('Saved the Chef Node configuration')

    def baked(self):

        self.log.info('Determining status of "{node}"'.format(
                                            node=self.hostname))

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
