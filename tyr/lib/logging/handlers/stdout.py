#!/usr/bin/env python
# -*- coding: utf8 -*-

from termcolor import cprint

color_level_map = {
    'debug': 'blue',
    'info': 'green',
    'warning': 'yellow',
    'error': 'red',
    'critical': 'magenta'
}


def stdout_handler(values):
    """
    A handler for Logger which formats and prints events to stdout.

    :type values: dict
    :param values: A dictionary optionally containing the event and any tags
    """
    if 'event' in list(values):
        template = '{timestamp} [{level}] {path}: {event} [{tags}]'
    else:
        template = '{timestamp} [{level}] {path}: [{tags}]'

    level = values['level']

    params = {}

    params['timestamp'] = str(values.pop('timestamp'))
    params['level'] = values.pop('level').upper()
    params['path'] = values.pop('path')

    if 'event' in list(values):
        params['event'] = values.pop('event')

    params['tags'] = ''

    for key in list(values):
        params['tags'] = '{tags}\t{key}={value}'.format(
            tags=params['tags'],
            key=key,
            value=values[key])

    params['tags'] = params['tags'].lstrip()

    cprint(template.format(**params), color_level_map[level])
