#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from superkwargs import superkwarg, kwarg, exceptions, typing
from libh.mongodb.rs_mods import REPLICA_SET_MODS
from tyr.instances.mongo_node import MongoNode


class MongoRouterNode(MongoNode):
    
    @kwarg('subrole', default='router')
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    
    @property
    def chef_node_attributes(self):
        a = super().chef_node_attributes

        a.update({
            'zuun': {
                'deployment': self.zuun_deployment,
                'role': 'router'
            }
        })

        return a
