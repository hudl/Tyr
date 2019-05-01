#!/usr/bin/env python
# -*- coding: utf-8 -*-

from peche import setup
from peche.logging.handlers import StdoutColour
import peche.logging.levels

def logger(name):
    _, log = setup(f'infrakit.{name}')
    log.drop_handlers()
    log.level = peche.logging.levels.Level.Debug
    log.add_handler(StdoutColour)
    log.inspection = False

    return log