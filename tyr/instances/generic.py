#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import random
import string
from chef import Node as ChefNode
from superkwargs import superkwarg, kwarg, exceptions, typing
from libh.conn.aws import client as aws_client
from libh.conn.chef import client as chef_client
from libh.logging import logger


class Instance(object):
    DEFAULT_SUBNET_ID_BY_ENV = {
        'prod': 'subnet-e7156e90',
        'thor': 'subnet-9f2e60c4'
    }

    DEFAULT_DNS_ZONE_BY_ENV = {
        'prod': 'app.hudl.com',
        'thor': 'app.thorhudl.com',
        'stage': 'app.staghudl.com'
    }

    DEFAULT_CHEF_SERVER_BY_ENV = {
        'stage': 'https://chef12-ec2.app.hudl.com/organizations/hudl',
        'thor': 'https://chef12-server.app.hudl.com/organizations/hudl',
        'prod': 'https://chef12-vpc.app.hudl.com/organizations/hudl',
    }
    DEFAULT_FALLBACK_CHEF_SERVER = 'https://chef12.app.hudl.com/organizations/hudl'

    DEFAULT_KEYPAIR_BY_ENV = {
        'prod': 'bkaiserkey'
    }
    DEFAULT_FALLBACK_KEYPAIR = 'stage-key'

    @kwarg('environment', default='thor', choices=['thor', 'stage', 'prod'])
    @kwarg('group', required=True)
    @kwarg('server_type', required=True)
    @kwarg('role', default=lambda kw: f'{kw["environment"][0]}-{kw["group"]}-{kw["server_type"]}')
    @kwarg('instance_profile', default=lambda kw: kw['role'])
    @kwarg('subrole', default=None)
    @kwarg('availibility_zone', default='c')
    @kwarg('subnet_id', default=lambda kw: Instance.DEFAULT_SUBNET_ID_BY_ENV.get(kw['environment']))
    @kwarg('dns_zone', default=lambda kw: Instance.DEFAULT_DNS_ZONE_BY_ENV.get(kw['environment']))
    @kwarg('instance_type', default=lambda kw: 't2.medium' if kw.get('subnet_id') else 'm3.medium')
    @kwarg('ami_id', default='ami-6869aa05')
    @kwarg('region', default='us-east-1')
    @kwarg('chef_runlist', default=['role[rolebase]'])
    @kwarg('chef_run_attempts', default=1)
    @kwarg('chef_attrs', default={})
    @kwarg('chef_server', default=lambda kw: Instance.DEFAULT_CHEF_SERVER_BY_ENV.get(kw['environment'], Instance.DEFAULT_FALLBACK_CHEF_SERVER))
    @kwarg('keypair', default=lambda kw: Instance.DEFAULT_KEYPAIR_BY_ENV.get(kw['environment'], Instance.DEFAULT_FALLBACK_KEYPAIR))
    @kwarg('security_groups', default=lambda kw: ['management', 'chef-nodes', kw['role'],  f'{kw["environment"][0]}-{kw["server_type"]}-management', f'{kw["environment"][0]}-{kw["group"]}-management'])
    @kwarg('ec2_tags', default={})
    @kwarg('chef_version', default='12.14')
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.ec2 = aws_client('ec2', region_name=self.region)
        self.log = logger('tyr')

    @property
    def user_data(self):
        template = """Content-Type: multipart/mixed; boundary="===============0035287898381899620=="
MIME-Version: 1.0
--===============0035287898381899620==
Content-Type: text/cloud-config; charset="us-ascii"
MIME-Version: 1.0
Content-Transfer-Encoding: 7bit
Content-Disposition: attachment; filename="cloud-config.txt"
#cloud-config
repo_upgrade: none
repo_releasever: 2016.03
--===============0035287898381899620==
Content-Type: text/x-shellscript; charset="us-ascii"
MIME-Version: 1.0
Content-Transfer-Encoding: 7bit
Content-Disposition: attachment; filename="user-script.txt"
#!/bin/bash
sed -i '/requiretty/d' /etc/sudoers
hostname {hostname}
sed -i 's/^releasever=latest/# releasever=latest/' /etc/yum.conf
yum clean all
mkdir /etc/chef
touch /etc/chef/client.rb
mkdir -p /etc/chef/ohai/hints
touch /etc/chef/ohai/hints/ec2.json
/usr/bin/aws s3 cp s3://hudl-chef-artifacts/chef-client/validation.pem  /etc/chef/validation.pem
echo 'chef_server_url "{chef_server_url}"
node_name "{name}"
environment "{chef_env}"
validation_client_name "hudl-validator"
ssl_verify_mode :verify_none' > /etc/chef/client.rb
/usr/bin/aws s3 cp s3://hudl-chef-artifacts/chef-client/encrypted_data_bag_secret /etc/chef/encrypted_data_bag_secret
# This is our own copy of the Chef OmniTruck installation script, see
# this README for details on why - https://github.com/hudl/hudl-chef-omnitruck-installer/blob/master/README.md
/usr/bin/aws s3 cp s3://hudl-chef-artifacts/chef-client/install.sh install.sh
chmod u+x install.sh
sudo ./install.sh -v {chef_version}
yum install -y gcc
printf "%s" "{attributes}" > /etc/chef/attributes.json
cp /var/tmp/attributes.json /etc/chef/attributes.json

# See CHANGELOG.md for version 2.3.0 for more details about the following two lines
/opt/chef/embedded/bin/gem install bundler -v '= 1.17.3'
/opt/chef/embedded/bin/gem uninstall bundler --version 1.12.5

chef_client_runs=0
until [ $chef_client_runs -ge {chef_run_attempts} ]
do

    if [ $chef_client_runs -ge 1 ]; then
        chef-client -L /var/log/chef-client.log && break
    else
        chef-client -r '{run_list}' -L /var/log/chef-client.log -j /etc/chef/attributes.json \
            && break
    fi
    chef_client_runs=$[$chef_client_runs+1]
    sleep 60
done
--===============0035287898381899620==--
"""
        chef_attributes = self.chef_node_attributes
        chef_attributes.update(self.chef_attrs)
        chef_attributes['volumes'] = self.volumes

        return template.format(
            hostname=self.hostname,
            name=self.name,
            chef_env=self.environment,
            chef_server_url=self.chef_server,
            attributes=json.dumps(chef_attributes).replace('"', '\\"'),
            run_list=','.join(self.chef_runlist),
            chef_run_attempts=self.chef_run_attempts,
            chef_version=self.chef_version
        )

    @property
    def tags(self):
        t = {
            'Role': f'Role{self.server_type.capitalize()}',
            'Group': self.group,
            'Environment': self.environment,
            'Name': self.name
        }

        t.update(self.ec2_tags)

        return t

    @property
    def location(self):
        region_abbreviation = {
            'us-east-1': 'use1'
        }

        if self.subnet_id is None:
            return region_abbreviation[self.region] + self.availibility_zone
        else:
            r = self.ec2.describe_subnets(SubnetIds=[self.subnet_id])

            return region_abbreviation[self.region] + r['Subnets'][0]['AvailabilityZone'][-1]

    @property
    def name_template(self):
        if self.subrole is None:
            return f'{self.role}-{self.location}'
        else:
            return f'{self.role}-{self.subrole}-{self.location}'

    @property
    def name(self):
        try:
            return self.resolved_name
        except AttributeError:
            chef = chef_client()

            while True:
                rand = ''.join(
                    random.choices(string.ascii_lowercase + string.digits, k=6)
                )

                name = f'{self.name_template}-{rand}'

                if name not in ChefNode.list(api=chef).names and \
                        len(self.ec2.describe_instances(
                            Filters=[
                                {
                                    'Name': 'tag:Name',
                                    'Values': [name]
                                }
                            ]
                        )['Reservations']) == 0:
                    break

            self.log.info('Resolved instance name', name=name,
                          hostname=f'{name}.{self.dns_zone}')

            self.resolved_name = name
            return name

    @property
    def hostname(self):
        return f'{self.name}.{self.dns_zone}'

    @property
    def volumes(self):
        return []

    @property
    def chef_node_attributes(self):
        return {}

    @property
    def run_instance_input(self):
        _input = {
            'MaxCount': 1,
            'MinCount': 1,
            'ImageId': self.ami_id,
            'InstanceType': self.instance_type,
            'KeyName': self.keypair,
            'IamInstanceProfile': {
                'Name': self.instance_profile
            },
            'UserData': self.user_data,
            'TagSpecifications': [
                {
                    'ResourceType': 'instance',
                    'Tags': [{'Key': k, 'Value': v} for k, v in self.tags.items()]
                }
            ]
        }

        if self.subnet_id is None:
            _input['Placement'] = {
                'AvailabilityZone': f'{self.region}{self.availibility_zone}'
            }
            _input['SecurityGroups'] = self.security_groups
        else:
            _input['SubnetId'] = self.subnet_id

            r = self.ec2.describe_security_groups(
                Filters=[
                    {
                        'Name': 'vpc-id',
                        'Values': [self.ec2.describe_subnets(SubnetIds=[self.subnet_id])['Subnets'][0]['VpcId']]
                    }
                ],
                MaxResults=1000
            )

            _input['SecurityGroupIds'] = [g['GroupId'] for g in r['SecurityGroups']
                                          if g['GroupName'] in self.security_groups]

        return _input

    def provision(self):
        _input = self.run_instance_input

        self.log.info(
            'Preparing to provision EC2 instance',
            name=self.name,
            image_id=self.ami_id,
            instance_type=self.instance_type,
            keyname=self.keypair,
            iam_profile=self.instance_profile,
            placement=_input.get('SubnetId', _input.get(
                'Placement', {}).get('AvailabilityZone')),
            security_groups=_input.get(
                'SecurityGroupIds', _input.get('SecurityGroups'))
        )

        r = self.ec2.run_instances(**_input)

        self.log.info('EC2 instance provisioned',
                      instance_id=r['Instances'][0]['InstanceId'])

        return r['Instances'][0]
