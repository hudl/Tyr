#!/usr/bin/env python
# -*- coding: utf8 -*-

import os
import hashlib
import boto3
import requests

clients = {}
resources = {}

def profile(name):
    if name is not None: return name

    try:
        requests.get('http://169.254.169.254/latest/meta-data/', timeout=1)
    except Exception:
        name = os.getenv('AWS_DEFAULT_PROFILE', 'hudl')

    return name


def client(service_name, profile_name=None, region_name='us-east-1',
           aws_access_key_id=None, aws_secret_access_key=None):
    profile_name = profile(profile_name)

    params = {
        'profile_name': profile_name,        
        'service_name': service_name,
        'region_name': region_name,
        'aws_access_key_id': aws_access_key_id,
        'aws_secret_access_key': aws_secret_access_key
    }

    key_template = 'client_{profile_name}_{service_name}_{region_name}_' \
                   '{aws_access_key_id}_{aws_secret_access_key}'

    key_raw = key_template.format(**params).encode('utf-8')

    key = hashlib.sha512(key_raw).hexdigest()

    try:
        return clients[key]
    except KeyError:
        del params['profile_name']
        clients[key] = boto3.Session(profile_name=profile_name).client(**params)
        return clients[key]


def resource(service_name, profile_name=None, region_name='us-east-1',
             aws_access_key_id=None, aws_secret_access_key=None):
    profile_name = profile(profile_name)

    params = {
        'profile_name': profile_name,        
        'service_name': service_name,
        'region_name': region_name,
        'aws_access_key_id': aws_access_key_id,
        'aws_secret_access_key': aws_secret_access_key
    }

    key_template = 'resource_{profile_name}_{service_name}_{region_name}_' \
                   '{aws_access_key_id}_{aws_secret_access_key}'

    key_raw = key_template.format(**params).encode('utf-8')

    key = hashlib.sha512(key_raw).hexdigest()

    try:
        return resources[key]
    except KeyError:
        del params['profile_name']
        resources[key] = boto3.Session(profile_name=profile_name).resource(**params)
        return resources[key]