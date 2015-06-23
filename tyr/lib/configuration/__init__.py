#!/usr/bin/env python
# -*- coding: utf8 -*-

from tyr.lib.configuration.configuration import Configuration


def get_conf(path, **kwargs):
    """
    Convenience method for retrieving a configuration.

    :type path: string
    :param path: The path for the configuration
    """
    return Configuration(path, **kwargs)
