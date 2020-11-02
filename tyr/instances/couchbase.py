#!/usr/bin/env python
# -*- coding: utf-8 -*-

from superkwargs import kwarg
from infrakit.tyr.instance import Instance


class CouchbaseNode(Instance):

    @kwarg('server_type', default='cache')
    @kwarg('chef_runlist', default=['recipe[role_couchbase::default]'])
    @kwarg('couchbase_username', required=True)
    @kwarg('couchbase_password', required=True)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def chef_node_attributes(self):
        a = super().chef_node_attributes

        a.update({
            'couchbase': {
                'server': {
                    'username': self.couchbase_username,
                    'password': self.couchbase_password
                }
            }
        })

        return a