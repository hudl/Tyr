#!/usr/bin/env python
# -*- coding: utf8 -*-

from tyr.lib.logging.logger import Logger
from tyr.lib.logging.handlers.stdout import stdout_handler


def get_logger(path, **kwargs):
    """
    Returns an instance of Logger configured with the specified path and
    with any additional keyword arguments bound as constant values.

    :type path: string
    :param string: The path from where the logging is occuring. For example,
                   the path to a module or function.
    """
    handlers = [stdout_handler]
    logger = Logger(path, values=kwargs, handlers=handlers)

    return logger
