#!/usr/bin/env python
# -*- coding: utf-8 -*-

REPLICA_SET_MODS = {
    'monolith': {
        'data': lambda n: 'RS{}'.format(n.replica_set)
    },        
    'exchanges': {
        'data': lambda n: 'RS{}'.format(n.replica_set)
    },
    'clips': {
        'data': lambda n: 'CLIPS'
    },
    'feed': {
        'data': lambda n: 'FEED-RS{}'.format(n.replica_set)
    },
    'highlights': {
        'data': lambda n: {1: 'highlights_0', 2: 'highlights_1', 3: 'highlights-rs3'}[n.replica_set],
        'config': lambda n: 'configHighlights'
    },
    'hudlrd': {
        'data': lambda n: 'predator-rs{}'.format(n.replica_set)
    },
    'leroy': {
        'data': lambda n: 'LEROY'
    },
    'overwatch': {
        'data': lambda n: '{}-overwatch'.format(n.environment[0])
    },
    'push': {
        'data': lambda n: 'PUSH'
    },
    'recruit': {
        'data': lambda n: 'REC'
    },
    'statistics': {
        'data': lambda n: 'STATS'
    }
}