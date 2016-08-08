#!/usr/bin/env python
# -*- coding: utf8 -*-

import chef
import os.path
import re
import requests
import time
from tyr.helpers import data_file
from tyr.servers.server import Server


class NginxServer(Server):

    SERVER_TYPE = 'nginx'

    CHEF_RUNLIST = ['role[RoleNginx]']

    IAM_ROLE_POLICIES = [
        'allow-describe-instances',
        'allow-describe-tags',
        'allow-create-tags',
        'allow-lifecycle-nginx-{environment}',
        'allow-describe-elbs',
        'allow-get-nginx-config',
        'allow-modify-nginx-elbs-{environment}'
    ]

    def __init__(self, group=None, server_type=None, instance_type=None,
                 environment=None, ami=None, region=None, role=None,
                 keypair=None, availability_zone=None, security_groups=None,
                 block_devices=None, chef_path=None, subnet_id=None,
                 dns_zones=None, platform=None, use_latest_ami=False,
                 ingress_groups_to_add=None, ports_to_authorize=None,
                 classic_link=False, add_route53_dns=True):

        if server_type is None:
            server_type = self.SERVER_TYPE

        self.chef_path = chef_path

        super(NginxServer, self).__init__(group, server_type, instance_type,
                                          environment, ami, region, role,
                                          keypair, availability_zone,
                                          security_groups, block_devices,
                                          chef_path, subnet_id, dns_zones,
                                          platform, use_latest_ami,
                                          ingress_groups_to_add,
                                          ports_to_authorize,
                                          classic_link, add_route53_dns)

    def configure(self):
        super(NginxServer, self).configure()

    @property
    def user_data(self):
        # read in userdata file
        user_data = None
        try:
            f = data_file('user_data_chef_provision')
            user_data = f.read()

            chef_path = os.path.expanduser(self.chef_path)
            validation_key_path = os.path.join(chef_path, 'chef-validator.pem')
            validation_key_file = open(validation_key_path, 'r')
            validation_key = validation_key_file.read()

            return user_data.format(validation_key=validation_key)

        except IOError:
            self.log.critical('chef-validator key not found!')
            exit(1)
