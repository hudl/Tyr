import os
import sys
from tyr.servers.mongo import MongoDataNode, MongoDataWarehousingNode, MongoArbiterNode
import json
import time
from paramiko.client import AutoAddPolicy, SSHClient
import requests
import boto.ec2

def clear():

    os.system('cls' if os.name == 'nt' else 'clear')

def exit(code):

    print '\nExiting.'
    sys.exit(code)

def confirm():

    print '\a'

    response = ''

    while response != 'y' and response != 'n':
        response = raw_input('\nContinue? (y/n) ')

    if response == 'y': return True
    elif response == 'n': exit(1)

class ReplicaSet(object):

    primary = None

    def __init__(self, member):

        self.determine_primary(member)

    def determine_primary(self, member):

        response = run_mongo_command(member, 'db.isMaster()')
        primary = response['primary'].split(':')[0]

        print '\nUsing primary {primary}\n'.format(primary = primary)

        self.primary = primary

    @property
    def status(self):

        status = run_mongo_command(self.primary, 'rs.status()')

        print '\nReceived status:\n\n{status}\n'.format(status = status)

        return status

    @property
    def arbiter(self):

        arbiter = None

        for member in self.status['members']:
            if member['stateStr'] == 'ARBITER':
                arbiter = member['name'][:-6]

        print '\nThe arbiter is {arbiter}'.format(arbiter = arbiter)

        return arbiter

    def failover(self):

        member = self.primary

        run_mongo_command(self.primary, 'rs.stepDown()')

        time.sleep(120)

        self.determine_primary(member)

    def add_member(self, address, arbiter=False):

        name = '{address}:27018'.format(address = address)

        command = 'rs.add(\'{name}\')'.format(name = name)

        if arbiter:
            command = 'rs.addArb(\'{name}\')'.format(name = name)

        response = run_mongo_command(self.primary, command)

        if response['ok'] == 0:
            raise Exception(response['errmsg'])

    def remove_member(self, address, arbiter=False):

        name = '{address}:27018'.format(address = address)

        command = 'rs.remove(\'{name}\')'.format(name = name)

        response = run_mongo_command(self.primary, command)

        time.sleep(20)

        isMember = False

        for member in self.status['members']:
            if member['name'] == name:
                isMember = True
                break

        if isMember:
            raise Exception('Failed to remove the member:\n{error}'.format(
                                                            error = response))

        if arbiter:

            run_command(address, 'sudo service mongod stop')
            run_command(address, 'sudo rm -rf /volr/*')
            run_command(address, 'sudo service mongod start')

def run_command(address, command):

    connection = SSHClient()
    connection.set_missing_host_key_policy(AutoAddPolicy())

    while True:
        try:
            connection.connect(address,
                                username = 'ec2-user')
            break
        except Exception:
                print 'Unable to establish SSH connection'
                time.sleep(10)

    print 'Successfully established SSH connection'
    print 'Running "{command}" on "{address}"'.format(command=command,
                                                        address=address)

    stdin, stdout, sterr = connection.exec_command(command)

    return stdout.read()

    try:
        return json.loads(output.split('\n')[2])
    except ValueError:
        return output.split('\n')[2]

def run_mongo_command(address, command):

    template = 'mongo --port 27018 --eval "JSON.stringify({command})"'
    command = template.format(command = command)

    response = run_command(address, command)

    try:
        return json.loads(response.split('\n')[2])
    except ValueError:
        return response

def launch_server(environment, group, instance_type, availability_zone,
                    replica_set, data_volume_size, data_volume_iops,
                    mongodb_package_version, node_type, interactive,
                    replica_set_template):

    clear()

    mongodb_node_type = 'MongoDB Data Node'

    if node_type == 'datawarehousing':
        mongodb_node_type = 'MongoDB Data Warehousing Node'

    print 'We\'re going to create a server with the following properties:\n'
    print 'Node Type: {node_type}'.format(node_type = mongodb_node_type)
    print 'Environment: {environment}'.format(environment = environment)
    print 'Group: {group}'.format(group = group)
    print 'Instance Type: {instance_type}'.format(instance_type = instance_type)
    print 'Availability Zone: {zone}'.format(zone = availability_zone)
    print 'Replica Set: {replica_set}'.format(replica_set = replica_set)
    print 'Replica Set Name: {replica_set_template}'.format(
                                    replica_set_template = replica_set_template)
    print 'Data Volume Size: {size}'.format(size = data_volume_size)
    print 'Data Volume IOPS: {iops}'.format(iops = data_volume_iops)
    print 'MongoDB Package Version: {version}'.format(
                                            version = mongodb_package_version)

    if interactive:
        confirm()

    print '\n'

    node = None

    if node_type == 'data':
        node = MongoDataNode(group = group, instance_type = instance_type,
                                environment = environment,
                                availability_zone = availability_zone,
                                replica_set = replica_set,
                                data_volume_size = data_volume_size,
                                data_volume_iops = data_volume_iops,
                                mongodb_version = mongodb_package_version)

    elif node_type == 'datawarehousing':
        node = MongoDataWarehousingNode(group = group, instance_type = instance_type,
                                environment = environment,
                                availability_zone = availability_zone,
                                replica_set = replica_set,
                                data_volume_size = data_volume_size,
                                mongodb_version = mongodb_package_version)
    elif node_type == 'arbiter':
        node = MongoArbiterNode(group = group, instance_type = instance_type,
                                environment = environment,
                                availability_zone = availability_zone,
                                replica_set = replica_set,
                                mongodb_version = mongodb_package_version)

    if replica_set_template is not None:
        node.REPLICA_SET_TEMPLATE = replica_set_template

    node.autorun()

    clear()

    print 'Awesome work, {user}!'.format(user = os.getlogin())

    print '\nNow we\'re going to SSH into the server and wait until chef client has finished. Ready?'

    if interactive:
        confirm()

    print '\n'

    baked = node.baked()

    if baked:

        return node

    else:

        print '\nIt looks like chef failed to finish running.'
        exit(1)

def registered_in_stackdriver(stackdriver_username, stackdriver_api_key, instance_id):

    headers = headers = {
            'x-stackdriver-apikey': stackdriver_api_key,
            'Content-Type': 'application/json'
    }

    template = 'https://api.stackdriver.com/v0.2/instances/{id_}'

    endpoint = template.format(id_ = instance_id)

    r = requests.get(endpoint, headers=headers)

    return r.status_code != 404

def set_maintenance_mode(stackdriver_username, stackdriver_api_key, instance_id, interactive):

    clear()

    print 'The next step is to put the server into maintenance mode in StackDriver.'

    if interactive:
        confirm()

    while not registered_in_stackdriver(stackdriver_username,
                                        stackdriver_api_key, instance_id):

        print 'Not yet listed in Stackdriver...'
        time.sleep(10)

    headers = {
        'x-stackdriver-apikey': stackdriver_api_key,
        'Content-Type': 'application/json'
    }

    template = 'https://api.stackdriver.com/v0.2/instances/{id_}/maintenance/'
    endpoint = template.format(id_ = instance_id)

    body = {
        'username': stackdriver_username,
        'reason': "Waiting for MongoDB node to finish syncing.",
        'maintenance': True
    }

    data = json.dumps(body)

    r = requests.put(endpoint, data=data, headers=headers)

    if r.status_code != 200:

        print 'Failed to put the node into maintenance mode. Received code {code}'.format(
                                                    code = r.status_code)

        exit(1)

    else:

        print 'Placed the node in maintenance mode.'

    if interactive:
        confirm()

def unset_maintenance_mode(stackdriver_username, stackdriver_api_key, instance_id, interactive):

    clear()

    print 'The next step is to take the server out off maintenance mode in StackDriver.'

    if interactive:
        confirm()

    headers = {
        'x-stackdriver-apikey': stackdriver_api_key,
        'Content-Type': 'application/json'
    }

    template = 'https://api.stackdriver.com/v0.2/instances/{id_}/maintenance/'
    endpoint = template.format(id_ = instance_id)

    body = {
        'username': stackdriver_username,
        'reason': "MongoDB node finished syncing.",
        'maintenance': False
    }

    data = json.dumps(body)

    r = requests.put(endpoint, data=data, headers=headers)

    if r.status_code != 200:

        print 'Failed to remove the node from maintenance mode. Received code {code}'.format(
                                                    code = r.status_code)

        exit(1)

    else:

        print 'Removed the node from maintenance mode.'

    if interactive:
        confirm()

def add_to_replica_set(replica_set, node, interactive):

    clear()

    print 'Now we\'re going to add the new server to the replica set.'

    if interactive:
        confirm()

    replica_set.add_member(node.hostname)

    print '\nThe server has been added to the replica set. Onto the next step...'

    if interactive:
        confirm()

def remove_arbiter_from_replica_set(replica_set, address, interactive):

    clear()

    print 'In this part we\'ll be be removing the arbiter, from the replica set.'
    print 'We\'re using {address} as the arbiter'.format(address = address)

    if interactive:
        confirm()

    replica_set.remove_member(address, arbiter=True)

    print 'The arbiter has been successfully removed. Great job!'

    if interactive:
        confirm()

def wait_for_sync(node, interactive):

    clear()

    print 'This next step is pretty simple - wait for the server to finish syncing.'
    print 'We\'ll check the status every ten minutes and let you know when it\'s ready.'

    if interactive:
        confirm()

    while True:

        status = run_mongo_command(node.instance.public_dns_name, 'rs.status()')

        if status['ok'] != 1:

            print 'There was a problem getting the replica set status'
            exit(1)

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

        print 'Not finished yet...'
        time.sleep(600)

    print '\nLooks like the server finished syncing. Awesome work {user}!'.format(
                                                        user = os.getlogin())

    if interactive:
        confirm()

def add_arbiter_to_replica_set(replica_set, arbiter, interactive):

    clear()

    print 'In this part we\'ll be re-adding the arbiter to the replica set.'

    if interactive:
        confirm()

    replica_set.add_member(arbiter, arbiter=True)

    print 'Awesome, the arbiter is back in the replica set!'

    if interactive:
        confirm()

def remove_decommissioned_node(replica_set, decommission, interactive):

    clear()

    print 'Now we\'re going to remove the decommissioned node from the replica set. Almost done!'

    if interactive:
        confirm()

    replica_set.remove_member(decommission)

    print 'The server has been removed.'

    if interactive:
        confirm()

def terminate_decommissioned_node(address, interactive):

    clear()

    command = 'curl http://169.254.169.254/latest/meta-data/instance-id'

    instance_id = run_command(address, command)

    print 'Final step - terminating the old instance - {instance_id}.'.format(
                                                    instance_id = instance_id)

    if interactive:
        confirm()

    conn = boto.ec2.connect_to_region('us-east-1')

    response = conn.terminate_instances(instance_ids=[instance_id])

    if instance_id in response:

        print 'Successfully terminated the instance!'

def replace_server(environment = 'test', group = 'monolith',
                    instance_type = 'm3.medium', availability_zone = 'c',
                    replica_set_index = 1, data_volume_size = 400,
                    data_volume_iops = 2000, mongodb_package_version = '2.4.13',
                    member = None, replace = False, node_type = 'data',
                    interactive = True, replica_set_template=None):

    if member is None:

        print 'An existing replica set member is required.'
        exit(1)

    replica_set = ReplicaSet(member)

    if replica_set.primary[:2] == 'ip':

        print 'The replica set\'s primary is {primary}'.format(
                                                primary = replica_set.primary)

        print 'We\'ll need to failover in order to continue.'

        choice = None

        if interactive:

            print '\nHow should we proceed?'
            print '(a)utomatic failover'
            print '(m)anual failover'
            print '(q)uit'

            choice = raw_input('\nChoice: ')

        else:

            choice = 'a'

        if choice.lower() == 'a':

            conn = boto.ec2.connect_to_region('us-east-1')

            components = replica_set.primary.split('-')
            old_primary = replica_set.primary

            private_ip = '.'.join(components[1], components[2], components[3],
                                    components[4])

            reservations = conn.get_all_instances(
                                    filters={'private-ip-address': private_ip})

            instance = reservations[0].instances[0]

            public_address = None

            if 'Name' in instance.tags:

                public_address = instance.tags['Name']

                if environment == 'test':
                    public_address += '.thorhudl.com'
                elif environment == 'stage':
                    public_address += '.app.staghudl.com'
                elif environment == 'prod':
                    public_address += '.app.hudl.com'

            else:

                public_address = instance.public_dns_name

            run_mongo_command(public_address, 'rs.stepDown()')

            time.sleep(120)

            replica_set.determine_primary(member)

            replica_set.remove_member(old_primary)

            time.sleep(120)

            replica_set.add_member(public_address)

        elif choice.lower() == 'm':

            print '\n Continue once the primary has stepped down.'

            confirm()

            replica_set.determine_primary(member)

        else:

            exit(1)


    replica_set_name = replica_set.status['set']

    if node_type == 'arbiter':

        node = launch_server(environment, group, instance_type, availability_zone,
                                replica_set_index, data_volume_size, data_volume_iops,
                                mongodb_package_version, node_type, interactive,
                                replica_set_template=replica_set_name)

        arbiter = replica_set.arbiter

        if arbiter is not None:

            remove_arbiter_from_replica_set(replica_set, arbiter, interactive)

        add_arbiter_to_replica_set(replica_set, node.hostname, interactive)

        if replace:
            terminate_decommissioned_node(member, interactive)

        return

    stackdriver_api_key = os.environ.get('STACKDRIVER_API_KEY')

    if stackdriver_api_key is None:

        print 'The environment variable \'STACKDRIVER_API_KEY\' isn\'t set.'
        exit(1)

    stackdriver_username = os.environ.get('STACKDRIVER_USERNAME')

    if stackdriver_username is None:

        print 'The environment variable \'STACKDRIVER_USERNAME\' isn\'t set.'
        exit(1)

    node = launch_server(environment, group, instance_type, availability_zone,
                            replica_set_index, data_volume_size, data_volume_iops,
                            mongodb_package_version, node_type, interactive,
                            replica_set_template=replica_set_name)

    set_maintenance_mode(stackdriver_username, stackdriver_api_key,
                            node.instance.id, interactive)

    add_to_replica_set(replica_set, node, interactive)

    arbiter = replica_set.arbiter

    if arbiter is not None:

        remove_arbiter_from_replica_set(replica_set, arbiter, interactive)

    wait_for_sync(node, interactive)

    unset_maintenance_mode(stackdriver_username, stackdriver_api_key,
                            node.instance.id, interactive)

    if arbiter is not None:

        add_arbiter_to_replica_set(replica_set, arbiter, interactive)

    if replica_set.primary == member:

        choice = None

        if interactive:

            print 'The server you want to replace is the primary.'
            print 'The replica set will need to fail over.'

            print '\nHow should we proceed?'
            print '(a)utomatic failover'
            print '(m)anual failover'
            print '(q)uit'

            choice = raw_input('\nChoice: ')

        else:

            choice = 'a'

        if choice.lower() == 'a':

            replica_set.failover()

        elif choice.lower() == 'm':

            print '\n Continue once the primary has stepped down.'

            confirm()

            replica_set.determine_primary(member)

        else:

            exit(1)

    if replace:
        remove_decommissioned_node(replica_set, member, interactive)
        terminate_decommissioned_node(member, interactive)

    print 'All done!'
    print 'Here\'s the current state of the replica set:'
    print json.dumps(replica_set.status, indent=4, sort_keys=True)
