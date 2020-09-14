#!/usr/bin/env python
# -*- coding: utf-8 -*-

from superkwargs import kwarg
from infrakit.tyr.instance import Instance


class RabbitMQNode(Instance):

    @kwarg('server_type', default='rabbit')
    @kwarg('chef_runlist', default=['recipe[role_rabbitmq::default]'])
    @kwarg('rabbitmq_username', required=True)
    @kwarg('rabbitmq_password', required=True)
    @kwarg('data_volume_size', default=100)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def chef_node_attributes(self):
        a = super().chef_node_attributes

        a.update({
            'rabbitmq': {
                'username': self.rabbitmq_username,
                'passwd': self.rabbitmq_password
            }
        })

        return a

    @property
    def volumes(self):
        v = super().volumes

        v.extend([
            {
                'device': {
                    'name': 'rabbitmq',
                    'path': '/dev/xvdf',
                    'size': self.data_volume_size
                },
                'mount': {
                    'path': '/mnt/rabbit',
                    'user': 'rabbitmq',
                    'group': 'rabbitmq'
                }
            }
        ])

        return v