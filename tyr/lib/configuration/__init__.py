#!/usr/bin/env python
# -*- coding: utf8 -*-

from tyr.lib.configuration.configuration import Configuration


def get_conf(path, environment, **kwargs):
    """
    Convenience method for retrieving a configuration.

    :type path: string
    :param path: The path for the configuration
    :type environment: string
    :param environment: The environment currently being used
    """
    return Configuration(path, environment, **kwargs)
