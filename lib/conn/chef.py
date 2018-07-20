#!/usr/bin/env python
# -*- coding: utf8 -*-

import hashlib
from chef import ChefAPI

clients = {}


def client(conf='/root/.chef/knife.rb'):
    key = hashlib.sha512(
        f'client_conf_{conf}'.encode('utf-8')
    ).hexdigest()

    try:
        return clients[key]
    except KeyError:        
        clients[key] = ChefAPI.from_config_file(conf)
        return clients[key]
