#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from superkwargs import superkwarg, kwarg, exceptions, typing
from infrakit.logging import logger
from infrakit.tyr.instance import Instance


class MongoNode(Instance):
    
    @kwarg('server_type', default='mongo')
    @kwarg('chef_runlist', default=['role[rolemongo]', 'recipe[zuun::configure]'])
    @kwarg('mongodb_version', default='3.2.9')
    @kwarg('zuun_deployment', default=None)
    @kwarg('data_volume_size', default=1)
    @kwarg('data_volume_iops', default=None)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if self.zuun_deployment is None:
            self.zuun_deployment = f'{self.environment[0]}-{self.group}'

    @property
    def volumes(self):
        v = super().volumes

        v.extend([
            {
                'device': {
                    'path': '/dev/xvdc',
                    'size': 8,
                    'iops': 24,
                    'name': 'mongodb-swap'
                },
                'mount': {
                    'path': '/media/ephemeral0',
                    'user': 'root',
                    'group': 'root'                    
                }
            },
            {
                'device': {
                    'path': '/dev/xvdf',
                    'size': self.data_volume_size,
                    'iops': self.data_volume_iops,
                    'name': 'mongodb-data'                    
                },
                'mount': {
                    'path': '/volr',
                    'user': 'mongod',
                    'group': 'mongod',
                    'chown': True                    
                }
            },            
            {
                'device': {
                    'path': '/dev/xvdg',
                    'size': 15,
                    'iops': None,
                    'name': 'mongodb-journal'
                },
                'mount': {
                    'path': '/volr/journal',
                    'user': 'mongod',
                    'group': 'mongod'                    
                }
            },                
            {
                'device': {
                    'path': '/dev/xvdh',
                    'size': 10,
                    'iops': None,
                    'name': 'mongodb-logs'
                },
                'mount': {
                    'path': '/mongologs',
                    'user': 'mongod',
                    'group': 'mongod'                    
                }
            }        
        ])

        return v