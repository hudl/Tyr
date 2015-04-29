import time
import logging

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

