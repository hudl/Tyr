import os
import sys
from tyr.servers.mongo import MongoDataNode, MongoDataWarehousingNode, \
    MongoArbiterNode
import json
import time
from paramiko.client import AutoAddPolicy, SSHClient
import requests
import boto.ec2
import boto.route53
import logging
from tyr.utilities.stackdriver import (set_maintenance_mode,
                                       unset_maintenance_mode)


def timeit(method):

    def timed(*args, **kwargs):
        start = time.time()
        response = method(*args, **kwargs)
        end = time.time()

        log.debug('Executed {name} in {elapsed} seconds'.format(
                                                        name=method.__name__,
                                                        elapsed=end-start))

        return response

    return timed

log = logging.getLogger('Tyr.Utilities.ReplaceMongoServer')
if not log.handlers:
    log.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
            '%(asctime)s [%(name)s] %(levelname)s: %(message)s',
            datefmt='%H:%M:%S')
    ch.setFormatter(formatter)
    log.addHandler(ch)


class ReplicaSet(object):

    primary = None

    def __init__(self, member):

        log.debug('Determing the primary for the replica set')
        self.determine_primary(member)

    @timeit
    def determine_primary(self, member):

        log.debug('Using db.isMaster() to determine the primary')
        response = run_mongo_command(member, 'db.isMaster()')

        try:
            primary = response['primary'].split(':')[0]
        except TypeError as e:
            log.critical(str(e))
            log.critical('The response from MongoDB was not a JSON object.')
            sys.exit(1)
        except KeyError as e:
            log.critical(str(e))
            log.critical('The primary property was not defined.')
            sys.exit(1)
        except AttributeError as e:
            log.critical(str(e))
            log.critical('The primary property is not a string.')
            sys.exit(1)

        self.primary = primary

        log.debug('The primary is {primary}'.format(primary=self.primary))

    @property
    @timeit
    def status(self):

        log.debug('Retrieving the replica set\'s status using rs.status()')
        status = run_mongo_command(self.primary, 'rs.status()')

        log.debug('The status is {status}'.format(status=status))

        return status

    @property
    @timeit
    def arbiter(self):

        log.debug('Retrieving the replica set\'s arbiter')

        arbiter = None

        for member in self.status['members']:
            if member['stateStr'] == 'ARBITER':
                arbiter = member['name'][:-6]

        if arbiter is None:
            log.debug('The replica set does not have an arbiter')
        else:
            log.debug('The arbiter is {arbiter}'.format(arbiter=arbiter))

        return arbiter

    @timeit
    def failover(self):

        log.debug('Re-determining the replica set primary')
        self.determine_primary(self.primary)

        log.debug('Preparing to fail over the replica set')

        member = self.primary

        log.debug('Telling the primary to step down')
        run_mongo_command(self.primary, 'rs.stepDown()')

        log.debug('Sleeping for 120 seconds while an election takes place')
        time.sleep(120)

        log.debug('Determing the new primary')
        self.determine_primary(member)

    @timeit
    def add_member(self, address, arbiter=False, hidden=False,
                   accessible=None):

        log.debug('Re-determining the replica set primary')
        self.determine_primary(self.primary)

        log.debug('Checking if mongod is running on {address}'.format(
                                                        address=address))

        if accessible is None:
            output = run_command(address, 'pgrep mongod')
        else:
            output = run_command(accessible, 'pgrep mongod')

        if len(output) == 0:
            log.debug('mongod is not running on {address}'.format(
                                                        address=address))
            log.debug('Starting the mongo service on {address}'.format(
                                                        address=address))
            run_command(address, 'sudo service mongod start')

        else:
            log.debug('mongod is already running on {address}'.format(
                                                        address=address))

        log.debug('Adding {address} to the replica set'.format(
                                                        address=address))

        name = '{address}:27018'.format(address=address)

        command = 'rs.add(\'{name}\')'.format(name=name)

        if arbiter:
            command = 'rs.addArb(\'{name}\')'.format(name=name)

        if hidden:
            ids = [int(member['_id']) for member in self.status['members']]

            id_ = max(ids) + 1

            command = ('rs.add({{_id:{id_}, host:\'{name}\', priority:0, '
                       'hidden: true}})').format(id_=id_, name=name)

        log.debug('Using the command {command}'.format(command=command))
        response = run_mongo_command(self.primary, command)

        log.debug('Received response {response}'.format(response=response))

        if response['ok'] == 0:
            log.critical('The response was not okay')
            sys.exit(1)

    @timeit
    def remove_member(self, address, clean=False):

        log.debug('Re-determining the replica set primary')
        self.determine_primary(self.primary)

        log.debug('Stopping the mongo service on {address}'.format(
                                                            address=address))
        run_command(address, 'sudo service mongod stop')

        log.debug('Removing {address} from the replica set'.format(
                                                            address=address))

        name = '{address}:27018'.format(address=address)

        command = 'rs.remove(\'{name}\')'.format(name=name)

        log.debug('Using the command {command}'.format(command=command))
        response = run_mongo_command(self.primary, command)

        log.debug('Received response {response}'.format(response=response))

        log.debug('Sleeping for 20 seconds')
        time.sleep(20)

        isMember = False

        log.debug('Confirming that the node has been removed')

        for member in self.status['members']:
            if member['name'] == name:
                isMember = True
                break

        if isMember:
            log.critical('The node is still a member of the replica set')
            sys.exit(1)

        if clean:
            log.debug('Removing an mongo data from {address}'.format(
                                                        address=address))
            run_command(address, 'sudo rm -rf /volr/*')


@timeit
def run_command(address, command):

    connection = SSHClient()
    connection.set_missing_host_key_policy(AutoAddPolicy())

    while True:
        try:
            keys = ['~/.ssh/stage', '~/.ssh/prod']
            keys = [os.path.expanduser(key) for key in keys]

            connection.connect(address, username='ec2-user',
                               key_filename=keys)
            break
        except Exception:
            log.warn('Unable to establish an SSH connection')
            log.debug('Retrying in 10 seconds')
            time.sleep(10)

    log.debug('Established an SSH connection')
    log.debug('Running {command} on {address}'.format(command=command,
                                                      address=address))

    stdin, stdout, stderr = connection.exec_command(command)

    try:
        stdin = stdin.read()
    except IOError:
        stdin = None

    try:
        stdout = stdout.read()
    except IOError:
        stdout = None

    try:
        stderr = stderr.read()
    except IOError:
        stderr = None

    log.debug('STDIN: {stdin}'.format(stdin=stdin))
    log.debug('STDOUT: {stdout}'.format(stdout=stdout))
    log.debug('STDERR: {stderr}'.format(stderr=stderr))

    return stdout


@timeit
def run_mongo_command(address, command):

    log.debug('Running the mongo command {command} on {address}'.format(
                                                        command=command,
                                                        address=address))

    template = 'mongo --port 27018 --eval "JSON.stringify({command})"'
    command = template.format(command=command)

    response = run_command(address, command)

    log.debug('Received response {response}'.format(response=response))

    try:
        return json.loads(response.split('\n')[2])
    except ValueError:
        return response


@timeit
def launch_server(environment, group, subnet_id, instance_type,
                  availability_zone, replica_set, data_volume_size,
                  data_volume_iops, mongodb_package_version, node_type,
                  replica_set_template):

    log.debug('Preparing to launch a new node')

    node = None

    if node_type == 'data':
        node = MongoDataNode(group=group, instance_type=instance_type,
                             environment=environment,
                             subnet_id=subnet_id,
                             availability_zone=availability_zone,
                             replica_set=replica_set,
                             data_volume_size=data_volume_size,
                             data_volume_iops=data_volume_iops,
                             mongodb_version=mongodb_package_version)

    elif node_type == 'datawarehousing':
        node = MongoDataWarehousingNode(group=group,
                                        instance_type=instance_type,
                                        environment=environment,
                                        subnet_id=subnet_id,
                                        availability_zone=availability_zone,
                                        replica_set=replica_set,
                                        data_volume_size=data_volume_size,
                                        mongodb_version=mongodb_package_version
                                        )
    elif node_type == 'arbiter':
        node = MongoArbiterNode(group=group, instance_type=instance_type,
                                environment=environment,
                                subnet_id=subnet_id,
                                availability_zone=availability_zone,
                                replica_set=replica_set,
                                mongodb_version=mongodb_package_version)

    if replica_set_template is not None:
        node.REPLICA_SET_TEMPLATE = replica_set_template

    log.debug('Launching the node using autorun()')
    node.autorun()

    log.debug('Waiting until chef-client has finished running to proceed')
    baked = node.baked()

    if baked:
        return node

    else:
        log.critical('chef-client failed to finish running')
        sys.exit(1)


@timeit
def wait_for_sync(node):

    log.debug('Waiting for the node to finish syncing')

    while True:

        status = run_mongo_command(node.instance.private_dns_name,
                                   'rs.status()')

        if status['ok'] != 1:

            log.debug('The replica set is not okay')
            log.debug('Trying again in 30 seconds')

            time.sleep(30)

            continue

        state = ''

        for member in status['members']:
            try:
                if member['self']:
                    state = member['stateStr']
                    break
            except KeyError:
                pass

        if state == 'SECONDARY':
            break

        log.debug('The node has not finished syncing yet')
        log.debug('Trying again in 60 seconds')
        time.sleep(60)

    log.debug('The node has finished syncing')


@timeit
def stop_decommissioned_node(address, terminate=False):

    log.debug('Stopping or terminating the node at {address}'.format(
                                                        address=address))

    log.debug('Retrieving the instance ID')
    command = 'curl http://169.254.169.254/latest/meta-data/instance-id'
    instance_id = run_command(address, command)

    log.debug('The instance ID is {id_}'.format(id_=instance_id))

    set_maintenance_mode(instance_id)

    log.debug('Establishing a connection to AWS EC2 us-east-1')
    conn = boto.ec2.connect_to_region('us-east-1')

    if terminate:
        log.debug('Terminating {instance}'.format(instance=instance_id))
        response = conn.terminate_instances(instance_ids=[instance_id])
    else:
        log.debug('Stopping `{instance}'.format(instance=instance_id))
        response = conn.stop_instances(instance_ids=[instance_id])

    log.debug('Received the response {response}'.format(response=response))

    terminated = [instance.id for instance in response]

    if instance_id in terminated:
        if terminate:
            log.debug('Successfully terminated {instance}'.format(
                                                        instance=instance_id))
        else:
            log.debug('Successfully stopped {instance}'.format(
                                                        instance=instance_id))
    else:
        if terminate:
            log.debug('Failed to terminate {instance}'.format(
                                                        instance=instance_id))
        else:
            log.debug('Failed to stop {instance}'.format(
                                                        instance=instance_id))


@timeit
def replace_server(environment=None, group=None, subnet_id=None,
                   instance_type=None, availability_zone=None,
                   replica_set_index=None, data_volume_size=None,
                   data_volume_iops=None, mongodb_package_version=None,
                   member=None, replace=False, node_type='data',
                   reroute=False, replica_set_template=None, terminate=False,
                   prompt_before_replace=True):

    if member is None:

        log.critical('No existing member defined.')
        sys.exit(1)

    replica_set = ReplicaSet(member)

    if replica_set.primary[:2] == 'ip':

        log.warn('The replica set\'s primary address is private')
        log.debug('The replica set\'s primary is {primary}'.format(
                                                primary=replica_set.primary))
        log.info('To continue, the replica set must be failed over')

        log.debug('Connecting to AWS EC2 us-east-1')
        conn = boto.ec2.connect_to_region('us-east-1')
        log.debug('Connected to AWS EC2 us-east-1')

        components = replica_set.primary.split('-')
        old_primary = replica_set.primary

        private_ip = '.'.join([components[1], components[2], components[3],
                               components[4]])

        log.debug('Using the private IP address {ip} for the primary'.format(
                                                            ip=private_ip))

        log.debug('Filtering AWS instances by private IP address')
        reservations = conn.get_all_instances(
                                    filters={'private-ip-address': private_ip})

        instance = reservations[0].instances[0]
        log.debug('Found instance {id_}'.format(id_=instance.id))

        public_address = None

        if 'Name' in instance.tags:

            public_address = instance.tags['Name']

            log.debug('The tag Name exists on the instance')
            log.debug('Building public address from the instance\s name')

            if environment == 'test':
                public_address += '.thorhudl.com'
            elif environment == 'stage':
                public_address += '.app.staghudl.com'
            elif environment == 'prod':
                public_address += '.app.hudl.com'

        else:

            log.debug('The tag Name could not be found on the instance')

            public_address = instance.private_dns_name

        log.debug('Proceeding using {address} to contact the primary'.format(
                                                    address=public_address))

        log.debug('Instructing the primary to step down')
        run_mongo_command(public_address, 'rs.stepDown()')

        log.debug('Sleeping for 120 seconds while an election takes place')
        time.sleep(120)

        log.debug('Determining the new primary')
        replica_set.determine_primary(member)

        log.debug('(Temporarily) removing the old primary from '
                  'the replica set')
        replica_set.remove_member(old_primary)

        log.debug('Sleeping for 120 seconds')
        time.sleep(120)

        log.debug('Adding the old primary back into the replica '
                  'set with the new address')
        replica_set.add_member(public_address)

    replica_set_name = replica_set.status['set']

    log.info('Using the replica set name {name}'.format(name=replica_set_name))

    if node_type == 'arbiter':

        log.info('The node being added is an arbiter')

        log.info('Launching the new node')
        node = launch_server(environment, group, subnet_id, instance_type,
                             availability_zone, replica_set_index,
                             data_volume_size, data_volume_iops,
                             mongodb_package_version, node_type,
                             replica_set_template=replica_set_name)

        log.info('Retreiving the replica set\'s current arbiter')
        arbiter = replica_set.arbiter

        if arbiter is not None:
            log.info('The current arbiter is {arbiter}'.format(
                                                        arbiter=arbiter))
            log.info('Removing the old arbiter from the replica set')
            replica_set.remove_member(arbiter, clean=True)
        else:
            log.info('The replica set does not have an arbiter')

        log.info('Adding the new arbiter to the replica set')
        replica_set.add_member(node.hostname, arbiter=True,
                               accessible=node.instance.private_dns_name)

        if replace:
            log.info('Terminating the previous arbiter')
            stop_decommissioned_node(member, terminate=terminate)

        return

    log.info('The node being added is a {type_} node'.format(type_=node_type))

    log.info('Launching the new node')
    node = launch_server(environment, group, subnet_id, instance_type,
                         availability_zone, replica_set_index,
                         data_volume_size, data_volume_iops,
                         mongodb_package_version, node_type,
                         replica_set_template=replica_set_name)

    log.info('Placing the new node in maintenance mode')
    set_maintenance_mode(node.instance.id)

    log.info('Adding the new node to the replica set')

    if node_type == 'datawarehousing':
        replica_set.add_member(node.hostname, hidden=True,
                               accessible=node.instance.private_dns_name)
    else:
        replica_set.add_member(node.hostname,
                               accessible=node.instance.private_dns_name)

    log.info('Retreiving the replica set\'s arbiter')
    arbiter = replica_set.arbiter

    if arbiter is not None:
        log.debug('The arbiter is {arbiter}'.format(arbiter=arbiter))
        log.info('(Temporarily) removing the arbiter from the replica set')
        replica_set.remove_member(arbiter, clean=True)
    else:
        log.debug('There is no arbiter')

    log.info('Waiting for the node to finish syncing')
    wait_for_sync(node)

    log.info('Removing the node from maintenance mode')
    unset_maintenance_mode(node.instance.id)

    if arbiter is not None:
        log.info('Adding the arbiter back into the replica set')
        replica_set.add_member(arbiter, arbiter=True)

    if replace:

        log.info('Preparing to remove the previous node')

        if prompt_before_replace:

            print '\a'
            _ = raw_input('Press enter to continue')

        if replica_set.primary == member:

            log.warn('The previous node is the primary')
            log.warn('The replica set will need to fail over to continue')
            log.info('Failing over the replica set')
            replica_set.failover()

        log.info('Removing the previous node from the replica set')
        replica_set.remove_member(member)

        log.info('Terminating the previous node')
        stop_decommissioned_node(member, terminate=terminate)

        if node_type == 'data' and reroute:
            log.info('Redirecting previous DNS entry')

            log.debug('Establishing a connect to AWS Route53 us-east-1')
            conn = boto.route53.connect_to_region('us-east-1')

            log.debug('Retrieving the zone app.staghudl.com.')
            zone = conn.get_zone('app.staghudl.com.')

            if environment == 'prod':
                log.debug('Retrieving the zone app.hudl.com.')
                zone = conn.get_zone('app.hudl.com.')

            if environment == 'test':
                log.debug('Retrieving the zone thorhudl.com.')
                zone = conn.get_zone('thorhudl.com.')

            if zone.get_cname(member+'.') is None:
                log.debug('An existing DNS record does not exist')
            else:
                log.debug('Updating the DNS CNAME record')
                zone.update_cname(member+'.', node.instance.private_dns_name)
