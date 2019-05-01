#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from superkwargs import superkwarg, kwarg, exceptions, typing
from infrakit.mongodb.rs_mods import REPLICA_SET_MODS
from infrakit.tyr.mongo_node import MongoNode


class MongoConfigNode(MongoNode):
    
    @kwarg('group', required=True)
    @kwarg('subrole', default='conf')
    @kwarg('replicated', default=lambda kw: True if kw['group'] == 'highlights' else False)
    @kwarg('data_volume_size', default=15)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if self.replicated:
            self.replica_set_name = REPLICA_SET_MODS[self.group]['config'](self)


    @property
    def tags(self):
        t = super().tags

        if self.replicated:
            t.update({
                'ReplicaSet': self.replica_set_name
            })

        return t

    @property
    def chef_node_attributes(self):
        a = super().chef_node_attributes

        if self.replicated:
            a.update({
                'mongodb': {
                    'replicaset_name': self.replica_set_name
                },
                'zuun': {
                    'deployment': self.zuun_deployment,
                    'role': 'config',
                    'replica_set': self.replica_set_name
                }
            })
        else:
            a.update({
                'zuun': {
                    'deployment': self.zuun_deployment,
                    'role': 'config'
                }
            })

        return a
