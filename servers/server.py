from exceptions import *
import boto.ec2
import sys

class Server(object):

    def __init__(self, dry, verbose, size, cluster, environment, ami,
                    region, role, keypair, availability_zone):

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

