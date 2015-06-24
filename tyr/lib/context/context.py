#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tyr.lib.logging


class Context(object):
    environment = None
    logger = None
    config_root = None

    def __init__(self, environment, config_root='/etc', logger=None):
        self.environment = environment
        self.config_root = config_root

        if logger is None:
            self.logger = tyr.lib.logging.get_logger(None)
