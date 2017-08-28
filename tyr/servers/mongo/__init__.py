REPLICA_SET_MOD = {
    'monolith': {
        'rs': lambda x: 'RS{}'.format(x),
    },
    'exchanges': {
        'rs': lambda x: 'RS{}'.format(x),
    },
    'clips': {
        'rs': lambda x: 'CLIPS'
    },
    'feed': {
        'rs': lambda x: 'FEED-RS{}'.format(x)
    },
    'highlights': {
        'rs': lambda x: {1: 'highlights_0-backup', 2: 'highlights_1-backup', 3: 'highlights-rs3-backup'}[x],
        'cfg': lambda x: 'configHighlights'
    },
    'hudlrd': {
        'rs': lambda x: 'predator-rs{}'.format(x)
    },
    'leroy': {
        'rs': lambda x: 'LEROY'
    },
    'overwatch': {
        'rs': lambda x: 's-overwatch'
    },
    'push': {
        'rs': lambda x: 'PUSH'
    },
    'recruit': {
        'rs': lambda x: 'REC'
    },
    'statistics': {
        'rs': lambda x: 'STATS'
    }
}

from data import MongoDataNode
from arbiter import MongoArbiterNode
from config import MongoConfigNode
from zuun import ZuunConfig
