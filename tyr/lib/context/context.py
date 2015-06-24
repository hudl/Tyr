#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tyr.lib.logging


class Context(object):
    environment = None
    logger = None

    def __init__(self, environment, logger=None):
        self.environment = environment

        if logger is None:
            self.logger = tyr.lib.logging.get_logger(None)
