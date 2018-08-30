import time
import logging
from tyr.servers.cache import CacheServer
import requests
import boto.ec2
import socket
import boto.route53
from tyr.utilities.replace_mongo_server import set_maintenance_mode
import sys
import os

def timeit(method):

    def timed(*args, **kwargs):
        start = time.time()
        response = method(*args, **kwargs)
        end = time.time()

        log.debug('Executed {name} in {elapsed} seconds'.format(
                                                        name = method.__name__,
                                                        elapsed = end-start))

        return response

    return timed

log = logging.getLogger('Tyr.Utilities.ReplaceCouchbaseServer')
if not log.handlers:
    log.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
            '%(asctime)s [%(name)s] %(levelname)s: %(message)s',
            datefmt='%H:%M:%S')
    ch.setFormatter(formatter)
    log.addHandler(ch)

class Cluster(object):

    def __init__(self, member, username='Administrator', password=None):
        self.member = member
        self.username = username
        self.password = password

    @timeit
    def request(self, path, method='GET', payload=None,
                success=lambda r: r.status_code == 200, retry=True):

        uri = 'http://{hostname}:8091{path}'.format(hostname = self.member,
                                                        path = path)

        log.debug('Using URI {uri}'.format(uri=uri))

        auth = (self.username, self.password)

        log.debug('Using HTTP auth {auth}'.format(auth=auth))

        log.debug('Using HTTP method {method}'.format(method=method))

        if method == 'GET':
            r = requests.get(uri, auth=auth)

        elif method == 'POST':
            r = requests.post(uri, auth=auth, data=payload)

        while not success(r):

            log.error('Failed to make the request to {uri}'.format(uri=uri))
            log.debug('Received status code {code}'.format(code=r.status_code))
            log.debug('Received response {body}'.format(body=r.text))

            if not retry:
                break

            log.debug('Retrying in 10 seconds')
            time.sleep(10)

        return (r, success(r))

    @property
    @timeit
    def pool(self):

        r = self.request('/pools/')[0]

        pools = r.json()['pools']

        return pools[0]['name']

    @property
    @timeit
    def bucket(self):

        path = '/pools/{pool}/buckets/'.format(pool = self.pool)

        r = self.request(path)[0]

        buckets = r.json()

        return buckets[0]['name']

    @timeit
    def rebalance(self, ejected_nodes=None, known_nodes=None):

        if ejected_nodes:
            ejected_nodes = ','.join(ejected_nodes)
        else:
            ejected_nodes = ''

        if known_nodes:
            known_nodes = ','.join(known_nodes)
        else:
            known_nodes = ','.join([node['otpNode'] for node in  self.nodes])

        data = {
                'ejectedNodes': ejected_nodes,
                'knownNodes': known_nodes
        }

        r = self.request('/controller/rebalance', method='POST', payload=data)

    @property
    @timeit
    def is_rebalancing(self):

        r = self.request('/pools/{pool}/rebalanceProgress/'.format(
                                                        pool = self.pool))[0]

        progress = r.json()

        return (progress['status'] == 'running')

    @property
    @timeit
    def nodes(self):

        r = self.request('/pools/nodes/')[0]

        response = r.json()

        conn = boto.ec2.connect_to_region('us-east-1')

        for node in response['nodes']:

            if node['hostname'].split('.')[0] == '10':
                reservations = conn.get_all_instances(filters={
                            'private-ip-address': node['hostname'].split(':')[0]
                                                              })

                instance = reservations[0].instances[0]

                yield {
                        'otpNode': node['otpNode'],
                        'address': {
                            'public': instance.public_dns_name,
                            'private': node['hostname'].split(':')[0]
                        }
                      }

            else:
                yield {
                        'otpNode': node['otpNode'],
                        'address': {
                            'public': node['hostname'].split(':')[0],
                            'private': node['hostname'].split(':')[0],
                        }
                      }

    @timeit
    def add_node(self, hostname):

        payload = {
                    'hostname': hostname,
                    'user': self.username,
                    'password': self.password
                  }

        r = self.request('/controller/addNode/', method='POST',
                            payload=payload)[0]

        log.info('{hostname} successfully added as {otpNode}'.format(
                                                hostname = hostname,
                                                otpNode = r.json()['otpNode']))

    @timeit
    def remove_node(self, hostname):

        log.warn('The removal of an active node from a cluster should be ' \
                    'performed using rebalance() with the ejected_nodes ' \
                    'argument')

        payload = {
                    'otpNode': 'ns_1@{hostname}'.format(hostname=hostname)
                  }

        r = self.request('/controller/ejectNode/', method='POST',
                            payload=payload)

@timeit
def replace_couchbase_server(member, group=None, environment=None,
                                availability_zone=None, couchbase_username=None,
                                couchbase_password=None, replace=True,
                                reroute=True, terminate=False):

    stackdriver_username = os.environ.get('STACKDRIVER_USERNAME')

    if not stackdriver_username:
        log.critical('The environment variable STACKDRIVER_USERNAME is ' \
                        'undefined')
        sys.exit(1)

    stackdriver_api_key = os.environ.get('STACKDRIVER_API_KEY')

    if not stackdriver_api_key:
        log.critical('The environment variable STACKDRIVER_API_KEY is ' \
                        'undefined')
        sys.exit(1)

    public_address = member

    conn = boto.ec2.connect_to_region('us-east-1')

    if member.split('.')[0] == '10':
        reservations = conn.get_all_instances(filters={
                                                    'private-ip-address': member
                                                       })

        instance = reservations[0].instances[0]

        public_address = instance.public_dns_name

    else:
        reservations = conn.get_all_instances(filters={
                                                'tag:Name': member.split('.')[0]
                                                      })

        instance = reservations[0].instances[0]

    cluster = Cluster(public_address, username=couchbase_username,
                        password=couchbase_password)

    node = CacheServer(group=group, environment=environment,
                        availability_zone=availability_zone,
                        couchbase_username=couchbase_username,
                        couchbase_password=couchbase_password,
                        bucket_name = cluster.bucket)
    node.autorun()

    cluster.add_node(node.hostname)

    cluster.rebalance()

    while cluster.is_rebalancing:
        pass

    if not replace:
        return

    cluster.member = node.hostname

    if reroute:

        conn = boto.route53.connect_to_region('us-east-1')

        zone = 'app.hudl.com.'

        if node.environment == 'stage':
            zone = 'app.staghudl.com.'
        elif node.environment == 'test':
            zone = 'thorhudl.com.'

        name = '{name}.{zone}'.format(name=instance.tags['Name'], zone=zone)

        zone = conn.get_zone(zone)

        status = zone.update_cname(name, node.hostname)

        while status.update() != 'INSYNC':
            log.debug('The DNS update is not in sync yet. Retrying in 10 ' \
                        'seconds')
            time.sleep(10)

        while socket.gethostbyname(name) != node.instance.ip_address:
            log.debug('The DNS update has not propagated out yet. Retrying ' \
                        'in 10 seconds.')
            time.sleep(10)

    cluster.rebalance(ejected_nodes=['ns_1@{member}'.format(member=member)])

    while cluster.is_rebalancing:
        pass

    set_maintenance_mode(stackdriver_username, stackdriver_api_key, instance.id)

    conn = boto.ec2.connect_to_region('us-east-1')

    if terminate:
        response = conn.terminate_instances(instance_ids=[instance.id])
    else:
        response = conn.stop_instances(instance_ids=[instance.id])

    if instance.id in [i.id for i in response]:
        if terminate:
            log.debug('Successfully terminated {instance}'.format(
                                                        instance=instance.id))
        else:
            log.debug('Successfully stopped {instance}'.format(
                                                        instance=instance.id))
    else:
        if terminate:
            log.debug('Failed to terminate {instance}'.format(
                                                        instance=instance.id))
        else:
            log.debug('Failed to stop {instance}'.format(
                                                        instance=instance.id))

    log.info('{old} has been replaced with {new}.'.format(old=member,
                                                            new=node.hostname))
