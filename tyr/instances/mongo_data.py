#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from superkwargs import superkwarg, kwarg, exceptions, typing
from libh.mongodb.rs_mods import REPLICA_SET_MODS
from tyr.instances.mongo_node import MongoNode


class MongoDataNode(MongoNode):
    
    @kwarg('group', required=True)
    @kwarg('replica_set', default=lambda kw: 0 if kw['group'] == 'reports' else 1)
    @kwarg('subrole', default=lambda kw: 'rs' + str(kw['replica_set']))
    @kwarg('data_volume_size', default=100)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        try:
            self.replica_set_name = REPLICA_SET_MODS[self.group]['data'](self)
        except KeyError:
            self.replica_set_name = f'{self.group}-rs{self.replica_set}'


    @property
    def tags(self):
        t = super().tags

        t.update({
            'ReplicaSet': self.replica_set_name
        })

        return t

    @property
    def chef_node_attributes(self):
        a = super().chef_node_attributes

        a.update({
            'mongodb': {
                'replicaset_name': self.replica_set_name
            },
            'zuun': {
                'deployment': self.zuun_deployment,
                'role': 'data',
                'replica_set': self.replica_set_name
            }
        })

        return a
