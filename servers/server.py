from exceptions import *
import boto.ec2
import logging
import sys

class Server(object):

    log = logging.getLogger('Servers.Server')
    log.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
            '%(asctime)s [%(name)s] %(levelname)s: %(message)s',
            datefmt='%H:%M:%S')
    ch.setFormatter(formatter)
    log.addHandler(ch)

    def __init__(self, dry=None, verbose=None, size=None, cluster=None,
                    environment=None, ami=None, region=None, role=None,
                    keypair=None, availability_zone=None):

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

    def configure(self):

        if self.dry is None:
            self.dry = False

        if self.verbose is None:
            self.verbose = False

        if self.size is None:
            self.size = 'm3.medium'

        if self.cluster is None:
            raise InvalidCluster('A cluster must be specified.')

        if self.environment is None:
            self.environment = 'test'

        if self.region is None:
            self.region = 'us-east-1'

        valid = lambda r: r in [region.name for region in boto.ec2.regions()]

        if not valid(self.region):

            error = '\'{region}\' is not a valid EC2 region'.format(
                        region=self.region)
            raise RegionDoesNotExist(error)

        self.establish_ec2_connection()

        if self.ami is None:
            self.ami = 'ami-146e2a7c'

        try:
            self.ec2.get_all_images(image_ids=[self.ami])
        except Exception, e:
            if 'Invalid id' in str(e):
                error = '\'{ami}\' is not a valid AMI'.format(ami = self.ami)
                raise InvalidAMI(error)

        if self.role is None:
            raise InvalidRole('An IAM role must be specified.')

        if self.keypair is None:
            self.keypair = 'stage-key'
            if self.environment == 'prod':
                self.keypair = 'bkaiserkey'

        valid = lambda k: k in [pair.name for pair in
                self.ec2.get_all_key_pairs()]

        if not valid(self.keypair):
            error = '\'{keypair}\' is not a valid EC2 keypair'.format(
                        keypair = self.keypair)
            raise InvalidKeyPair(error)

        if self.availability_zone is None:
            self.availability_zone = 'c'

    def establish_ec2_connection(self):

        self.log.info('Using EC2 Region \'{region}\''.format(
                        region=self.region))
        self.log.info("Attempting to connect to EC2")

        try:
            self.ec2 = boto.ec2.connect_to_region(self.region)

            if self.verbose:
                self.log.info('Established connection to EC2')
        except Exception, e:
            raise e

    def autorun(self):

        try:
            self.configure()
        except Exception, e:
            self.log.error('{exception} - {message}'.format(
                            exception = type(e).__name__,
                            message = str(e)))
            sys.exit(1)
