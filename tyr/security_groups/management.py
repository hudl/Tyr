rule = 'management'

definition = {
    'rules': [
        {
            'port': 22,
            'source': [
                'p-ops-vpn',
                '216.229.9.101/32',
                '76.84.137.182/32',
            ]
        },
        {
            'port': 3389,
            'source': [
                'p-ops-vpn',
                '216.229.9.101/32',
                '76.84.137.182/32',
            ]
        },
        {
            'port': '27017 - 28019',
            'source': [
                'p-ops-vpn',
                '67.253.162.102/32'
            ]
        },
        {
            'port': 1433,
            'source': '216.229.9.101/32'
        }
    ]
}
