#!/usr/bin/env python
# -*- coding: utf8 -*-

import hashlib
import paramiko
from typing import NamedTuple

clients = {}

class ExecResp(NamedTuple):
    stdin: str
    stdout: str
    stderr: str

class SSHClientWrapper(paramiko.SSHClient):
    def exec(self, *args, **kwargs):
        out = list(super().exec_command(*args, **kwargs))

        for x in range(3):
            try:
                out[x] = out[x].read().decode('utf-8')
            except IOError:
                out[x] = None

        return ExecResp(stdin=out[0], stdout=out[1], stderr=out[2])

def client(ip_address, username='ec2-user', port=22, environment=None, ssh_key_path=None):
    if ssh_key_path is None and environment is not None:
        ssh_key_path = {
            'thor': '/root/.ssh/stage-key',
            'stage': '/root/.ssh/stage-key',
            'prod': '/root/.ssh/bkaiser-key'
        }[environment]

    key = hashlib.sha512(
        f'client_{ip_address}_{port}_{username}_{ssh_key_path}'.encode('utf-8')
    ).hexdigest()

    try:
        return clients[key]
    except KeyError:
        client = SSHClientWrapper()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(ip_address, key_filename=ssh_key_path, username=username, port=port)

        clients[key] = client

        return client
