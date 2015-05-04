security_groups = {
    '.-.+-cache': {
        'rules': [
            {
                'port': '11209 - 11211',
                'source': [
                    'thors',
                    '{env}-{group}-cache'
                ]
            },
            {
                'port': '21100 - 21199',
                'source': [
                    'thors',
                    '{env}-{group}-cache'
                ]
            },
            {
                'port': 4369,
                'source': '{env}-{group}-cache'
            },
            {
                'port': '8091 - 8092',
                'source': '{env}-{group}-cache'
            },
            {
                'port': '11210 - 11211',
                'source': [
                    '216.229.9.101/32',
                    '24.106.8.210/32',
                    '74.51.218.230/32',
                    '75.69.151.220/32'
                ]
            }
        ]
    }
}
