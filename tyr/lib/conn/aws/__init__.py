#!/usr/bin/env python
# -*- coding: utf8 -*-

import hashlib
import boto3

clients = {}
resources = {}


def client(service_name, region_name, aws_access_key_id=None,
           aws_secret_access_key=None):
    """
    Retrieve a client for access a Amazon Web Services service. Clients are
    maintained in a dictionary, stored with their service name, region name,
    and the credentials used to access them. If a client with the specified
    arguments does not already exist, a new client will be created and stored
    for future use.

    :type service_name: string
    :param service_name: The name of the service the client should access
    :type region_name: string
    :param region_name: The name of the region the client should talk to
    :type aws_access_key_id: string
    :param aws_access_key_id: The access key ID used for access
    :type aws_secret_access_key: string
    :param aws_secret_access_key: The secret access key used for access
    """
    params = {
        'service_name': service_name,
        'region_name': region_name,
        'aws_access_key_id': aws_access_key_id,
        'aws_secret_access_key': aws_secret_access_key
    }

    key_template = 'client_{service_name}_{region_name}_{aws_access_key_id}_' \
                   '{aws_secret_access_key}'

    key_raw = key_template.format(**params).encode('utf-8')

    key = hashlib.sha512(key_raw).hexdigest()

    try:
        return clients[key]
    except KeyError:
        clients[key] = boto3.client(**params)
        return clients[key]


def resource(service_name, region_name, aws_access_key_id=None,
             aws_secret_access_key=None):
    """
    Retrieve a resource for accessing an Amazon Web Services service. Resources
    are maintained in a dictionary, stored with their service name, region
    name, and the credentials used to establish the connection. If a resource
    with the specified arguments does not already exist, a new resource will
    be created and stored for future use.

    :type service_name: string
    :param service_name: The name of the service the resource should access
    :type region_name: string
    :param region_name: The name of the region the resource should talk to
    :type aws_access_key_id: string
    :param aws_access_key_id: The access key ID used for access
    :type aws_secret_access_key: string
    :param aws_secret_access_key: The secret access key used for access
    """
    params = {
        'service_name': service_name,
        'region_name': region_name,
        'aws_access_key_id': aws_access_key_id,
        'aws_secret_access_key': aws_secret_access_key
    }

    key_template = 'resource_{service_name}_{region_name}_' \
                   '{aws_access_key_id}_{aws_secret_access_key}'

    key_raw = key_template.format(**params).encode('utf-8')

    key = hashlib.sha512(key_raw).hexdigest()

    try:
        return resources[key]
    except KeyError:
        resources[key] = boto3.resource(**params)
        return resources[key]
