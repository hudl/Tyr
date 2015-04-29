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

    def request(self, path, method='GET', payload=None):

        uri = 'http://{hostname}:8091{path}'.format(hostname = self.member,
                                                        path = path)

        auth = (self.username, self.password)

        if method == 'GET':
            return requests.get(uri, auth=auth)

        elif method == 'POST':
            return requests.post(uri, auth=auth, data=payload)

    @property
    def pool(self):

        r = self.request('/pools/')

        while r.status_code != 200:

            log.error('Received {code} from the API'.format(code=r.status_code))
            log.debug('Re-trying in 10 seconds')

            time.sleep(10)

            r = self.request('/pools/')

        pools = r.json()['pools']

        return pools[0]['name']

    @property
    def bucket(self):

        path = '/pools/{pool}/buckets/'.format(pool = self.pool)

        r = self.request(path)

        while r.status_code != 200:

            log.error('Received {code} from the API'.format(code=r.status_code))
            log.debug('Re-trying in 10 seconds')

            time.sleep(10)

            r = self.request(path)

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
            known_nodes = ''

        data = {
                'ejectedNodes': ejected_nodes,
                'knownNodes': known_nodes
        }

        r = self.request('/controller/rebalance', method='POST', payload=data)

        while r.status_code != 200:

            log.error('Received {code} from the API'.format(code=r.status_code))
            log.debug('Re-trying in 10 seconds')

            time.sleep(10)

            r = self.request('/controller/rebalance', method='POST',
                                payload=data)

    @property
    def is_rebalancing(self):

        r = self.request('/pools/{pool}/rebalanceProgress/'.format(
                                                            pool = self.pool))

        while r.status_code != 200:

            log.error('Received {code} from the API'.format(code=r.status_code))
            log.debug('Re-trying in 10 seconds')

            time.sleep(10)

            r = self.request('/pools/{pool}/rebalanceProgress/'.format(
                                                            pool = self.pool))

        progress = r.json()

        return (progress['status'] == 'running')

    @property
    def nodes(self):

        r = self.request('/pools/{pool}/nodes/'.format(pool=self.pool))

        while r.status_code != 200:

            log.error('Received {code} from the API'.format(code=r.status_code))
            log.debug('Re-trying in 10 seconds')

            time.sleep(10)
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

        r = self.request('/controller/addNode/', method='POST', payload=payload)

        if r.status_code > 400:

            log.error('Received {code} from the API'.format(code=r.status_code))
            log.debug('Re-trying in 10 seconds')

            time.sleep(10)

            r = self.request('/controller/addNode/', method='POST',
                                payload=payload)

        log.info('{hostname} successfully added as {otpNode}'.format(
                                                hostname = hostname,
                                                otpNode = r.json()['otpNode']))

    def remove_node(self, hostname):

        payload = {
                    'otpNode': 'ns_1@{hostname}'.format(hostname=hostname)
                  }

        r = self.request('/controller/ejectNode/', method='POST',
                            payload=payload)

        while r.status_code > 400:

            log.error('Received {code} from the API'.format(code=r.status_code))
            log.debug('Re-trying in 10 seconds')

            time.sleep(10)

            r = self.request('/controller/ejectNode/', method='POST',
                             payload=payload)

            log.info('{hostname} successfully removed'.format(
                                                hostname = hostname))

def replace_couchbase_server(member, group=None, environment=None,
                                availability_zone=None, couchbase_username=None,
                                couchbase_password=None, replace=True,
                                reroute=True, terminate=False):

    cluster = Cluster(member, username=couchbase_username,
                        password=couchbase_password)

    node = CacheServer(group=group, environment=environment,
                        availability_zone=availability_zone,
                        couchbase_username=couchbase_username,
                        couchbase_password=couchbase_password,
                        bucket_name = cluster.bucket)
    node.autorun()

    cluster.add_node(node.hostname)

    cluster.rebalance(known_nodes=cluster.nodes)

    while cluster.is_rebalancing:
        pass

    if not replace:
        return

    cluster.member = node.hostname

    cluster.remove_node(member)

    cluster.rebalance(known_nodes=cluster.nodes, ejected_nodes=member)

    while cluster.is_rebalancing:
        pass
