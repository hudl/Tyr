#!/usr/bin/env python
# -*- coding: utf-8 -*-

BACKUP_TAG_MOD = {
    'overwatch': {
        'data': lambda x: 'p-overwatch-backup'
    },
    'monolith': {
        'data': lambda x: 'rs{}-backup'.format(x),
        'config': lambda x: 'cfg-backup'
    },
    'statistics': {
        'data': lambda x: 'stats-backup',
    },
    'highlights': {
        'data': lambda x: {1: 'highlights_0-backup',
                           2: 'highlights_1-backup',
                           3: 'highlights-rs3-backup'}[x]
    },
    'leroy': {
        'data': lambda x: 'leroy-backup'
    },
    'recruit': {
        'data': lambda x: 'rec-backup'
    },
    'clips': {
        'data': lambda x: 'clips-backup'
    },
    'hudlrd': {
        'data': lambda x: 'predator-rs{}-backup'.format(x)
    },
    'push': {
        'data': lambda x: 'push-backup'
    },
    'users': {
        'data': lambda x: 'users-rs{}-sanitized'.format(x)
    }
}