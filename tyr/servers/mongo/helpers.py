REPLICA_SET_MOD = {
    'monolith': lambda x: 'RS{}'.format(x),
    'exchanges': lambda x: 'RS{}'.format(x),        
    'clips': lambda x: 'CLIPS',
    'feed': lambda x: 'FEED-RS{}'.format(x),
    'highlights': lambda x: {1: 'highlights_0-backup', 2: 'highlights_1-backup', 3: 'highlights-rs3-backup'}[x],
    'hudlrd': lambda x: 'predator-rs{}'.format(x),
    'leroy': lambda x: 'LEROY',
    'overwatch': lambda x: 's-overwatch',
    'push': lambda x: 'PUSH',
    'recruit': lambda x: 'REC',
    'statistics': lambda x: 'STATS'
}

CONFIG_MOD = {
    'highlights': 'configHighlights'
}