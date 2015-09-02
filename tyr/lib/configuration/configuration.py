#!/usr/bin/env python
# -*- coding: utf8 -*-

import json
import os.path


class Configuration(object):
    _kwargs = {}
    _config = {}

    def __init__(self, context, path, **kwargs):

        self.path = path
        self._kwargs = kwargs
        self._context = context
        self._load()

    def reload(self):
        """
        Reload the configuration. Useful if any configuration files have
        been changed since the initial load.
        """

        self._load()

    def _load(self):
        """
        Loads and builds the configuration given a path, environment and any
        overrides, provided as path and additional keyword arguments in
        __init__.
        """

        components = self.path.split('.')

        conf_paths = []

        for index, component in enumerate(components):
            tree = [self._context.config_root]
            tree.extend(components[0:index+1])

            general = tree.copy()
            environment_specific = tree.copy()

            general.append('conf.json')
            environment_specific.append('{environment}.json'.format(
                environment=self._context.environment))

            conf_paths.append(os.path.join(*general))
            conf_paths.append(os.path.join(*environment_specific))

        for conf_path in conf_paths:
            if os.path.exists(conf_path) and os.path.isfile(conf_path):
                with open(conf_path, 'r') as f:
                    config = json.load(f)
                    self._config.update(config)

        self._config.update(self._kwargs)

    def __getattr__(self, name):
        """
        Retrieve a key as an attribute.

        :type name: string
        :param name: The name of the key to return
        """
        return self._config[name]

    def __getitem__(self, key):
        """
        Retrieve a key as a dictionary item.

        :type key: string
        :param key: The key to return
        """
        return self._config[key]

    def __setitem__(self, key, value):
        """
        Set a key as a dictionary item.

        :type key: string
        :param key: The key to set
        :param value: The value to set
        """
        self._config[key] = value

    def __delitem__(self, key):
        """
        Delete a key from the configuration.

        :type key: string
        :param key: The key to delete
        """
        del self._config[key]

    def __iter__(self):
        """
        Retrieve an iterator with the defined keys.
        """
        return iter(list(self._config))

    def keys(self):
        """
        Retrieve a list of the defined keys.
        """
        return list(self._config)
