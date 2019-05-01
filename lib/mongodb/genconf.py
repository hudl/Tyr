#!/usr/bin/env python
# -*- coding: utf-8 -*-

from superkwargs import kwarg, superkwarg
from jinja2 import Template
from infrakit.mongodb.rs_mods import REPLICA_SET_MODS


class NodeStub(object):
    def __init__(self, environment, service, replica_set):
        self.environment = environment
        self.service = service
        self.replica_set = replica_set


@kwarg('environment', choices=['prod', 'stage', 'thor'])
@kwarg('service')
@kwarg('subrole', choices=['data', 'config', 'router'])
@kwarg('replica_set')
@kwarg('configDB')
@superkwarg(inject=True)
def generate_mongodb_config(**kwargs):
    stub = NodeStub(environment, service, replica_set)

    with open('/etc/infrakit/zuun/mongodb.conf.j2') as f:
        template = Template(f.read())

    if subrole == 'router':
        return template.render(
            port=27017,
            replication=False,
            storage=False,
            configDB=configDB
        )
    elif subrole == 'config':
        try:
            replica_set_name = REPLICA_SET_MODS[service]['config'](stub)

            return template.render(
                port=27019,
                replication=True,
                storage=True,
                replica_set_name=replica_set_name,
                configsvr=True
            )
        except KeyError:
            return template.render(
                port=27019,
                replication=False,
                storage=True,
                configsvr=True
            )
    elif subrole == 'data':
        try:
            replica_set_name = REPLICA_SET_MODS[service]['data'](stub)
        except KeyError:
            replica_set_name = f'{service}-rs{replica_set}'

        params = {}

        if service in REPLICA_SET_MODS and 'config' in REPLICA_SET_MODS[service]:
            params['recoverShardingState'] = 'false'

        if params == {}:
            params = None

        return template.render(
            port=27018,
            replication=True,
            storage=True,
            replica_set_name=replica_set_name,
            params=params
        )