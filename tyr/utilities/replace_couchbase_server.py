import time
import logging
from tyr.servers.cache import CacheServer
import requests
import boto.ec2

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
    def pool(self):

        r = self.request('/pools/')[0]

        pools = r.json()['pools']

        return pools[0]['name']

    @property
    def bucket(self):

        path = '/pools/{pool}/buckets/'.format(pool = self.pool)

        r = self.request(path)[0]

        buckets = r.json()

        return buckets[0]['name']

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
    def is_rebalancing(self):

        r = self.request('/pools/{pool}/rebalanceProgress/'.format(
                                                        pool = self.pool))[0]

        progress = r.json()

        return (progress['status'] == 'running')

    @property
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

    def remove_node(self, hostname):

        log.warn('The removal of an active node from a cluster should be ' \
                    'performed using rebalance() with the ejected_nodes ' \
                    'argument')

        payload = {
                    'otpNode': 'ns_1@{hostname}'.format(hostname=hostname)
                  }

        r = self.request('/controller/ejectNode/', method='POST',
                            payload=payload)

def replace_couchbase_server(member, group=None, environment=None,
                                availability_zone=None, couchbase_username=None,
                                couchbase_password=None, replace=True,
                                reroute=True, terminate=False):

    public_address = member

    if member.split('.')[0] == '10':

        conn = boto.ec2.connect_to_region('us-east-1')

        reservations = conn.get_all_instances(filters={
                                                    'private-ip-address': member
                                                       })

        instance = reservations[0].instances[0]

        public_address = instance.public_dns_name

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

    cluster.rebalance(ejected_nodes=['ns_1@{member}'.format(member=member)])

    while cluster.is_rebalancing:
        pass
