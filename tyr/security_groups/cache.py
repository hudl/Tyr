rule = '.-.+-cache'

definition = {
    'rules': [
        {
            'port': '11209 - 11211',
            'source': [
                {
                    'value': 'thors',
                    'rule': '[ts]-.+-cache'
                },
                '{env}-{group}-cache',
                {
                    'value': '{env}-web',
                    'rule': '[sp]-.+-cache'
                },
                {
                    'value': '{env}-mv-web',
                    'rule': '[sp]-.+-cache'
                }
            ]
        },
        {
            'port': '21100 - 21199',
            'source': [
                {
                    'value': 'thors',
                    'rule': '[ts]-.+-cache'
                },
                '{env}-{group}-cache'
            ]
        },
        {
            'port': 4369,
            'source': '{env}-{group}-cache'
        },
        {
            'port': '8091 - 8092',
            'source': [
                '{env}-{group}-cache',
                {
                    'rule': '[sp]-.+-cache',
                    'value': '{env}-web'
                },
                {
                    'rule': '[sp]-.+-cache',
                    'value': '{env}-mv-web'
                },
                {
                    'rule': 's-.+-cache',
                    'value': 'thors'
                },
                {
                    'rule': 's-.+-cache',
                    'value': '{env}-queues-job'
                },
                {
                    'rule': 'p-.+-cache',
                    'value': '{env}-queueproc-jobs'
                }
            ]
        },
        {
            'port': '11210 - 11211',
            'source': [
                {
                    'rule': '[ts]-.+-cache',
                    'value': '216.229.9.101/32'
                },
                {
                    'rule': '[ts]-.+-cache',
                    'value': '24.106.8.210/32'
                }
                {
                    'rule': '[ts]-.+-cache',
                    'value': '74.51.218.230/32'
                },
                {
                    'rule': '[ts]-.+-cache',
                    'value': '75.69.151.220/32'
                }
            ]
        }
    ]
}
