from .. import Server

class MongoArbiterNode(Server):

    log = logging.getLogger('Servers.MongoArbiterNode')
    log.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
            '%(asctime)s [%(name)s] %(levelname)s: %(message)s',
            datefmt = '%H:%M:%S')
    ch.setFormatter(formatter)
    log.addHandler(ch)
