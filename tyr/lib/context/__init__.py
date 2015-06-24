#!/usr/bin/env python
# -*- coding: utf-8 -*-

from tyr.lib.context.context import Context


def get_context(environment, logger=None):
    """
    Convenience method for creating a context.

    :type environment: string
    :param environment: The current environment
    :type logger: tyr.lib.logging.logger.Logger
    :param logger: A logger for the current context
    """
    return Context(environment, logger)
