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

