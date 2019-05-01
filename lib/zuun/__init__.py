#!/usr/bin/env python
# -*- coding: utf-8 -*-

from infrakit.conn.chef import client
from chef import DataBag, DataBagItem


def list_deployments():    
    data_bag = DataBag('zuun', api=client())

    return [k.split('_')[1] for k in data_bag.keys() if k != 'config']


def fetch_deployment(name, blank_if_invalid=False):
    if name in list_deployments():
        return dict(DataBagItem('zuun', f'deployment_{name}', api=client()))

    if blank_if_invalid:
        return {}

    raise Exception('Invalid deployment name')


def update_deployment(name, conf):
    if name not in list_deployments():
        DataBagItem.create('zuun', f'deployment_{name}', api=client(), **conf)
    else:
        deployment = DataBagItem('zuun', f'deployment_{name}', api=client())
        deployment.update(conf)
        deployment.save()