#!/usr/bin/env python
# -*- coding: utf8 -*-

import os


def data_file(path):
    root = os.path.abspath(os.path.dirname(__file__))
    path = os.path.join(root, '..', '..', 'data', path)

    return open(path, 'r')
