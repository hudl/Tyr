#!/usr/bin/env python
# -*- coding: utf8 -*-

from tyr.lib.configuration.configuration import Configuration
import inspect


def get_conf(context, path=None, **kwargs):
    """
    Convenience method for retrieving a configuration.

    :type path: string
    :param path: The path for the configuration
    :type context: tyr.lib.context.context.Context
    :param context: The context currently being used
    """

    if path is None:
        path = inspect.stack()[1][1]
        path = path[:-3]
        path = path[path.find('tyr'):]
        path = path.replace('/', '.')
        path += '.{function}'.format(function=inspect.stack()[1][3])

    return Configuration(context, path, **kwargs)
