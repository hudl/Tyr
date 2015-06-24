#!/usr/bin/env python
# -*- coding: utf8 -*-

from tyr.lib.configuration.configuration import Configuration


def get_conf(path, context, **kwargs):
    """
    Convenience method for retrieving a configuration.

    :type path: string
    :param path: The path for the configuration
    :type context: tyr.lib.context.context.Context
    :param context: The context currently being used
    """
    return Configuration(path, context, **kwargs)
