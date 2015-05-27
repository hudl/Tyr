rule = 'management'

definition = {
    'rules': [
        {
            'port': 22,
            'source': [
                'p-ops-vpn',
                '@hudl-lincoln-east',
                '@hudl-lincoln-west',
                '@hudl-boston'
                '@hudl-omaha'
            ]
        },
        {
            'port': 3389,
            'source': [
                'p-ops-vpn',
                '@hudl-lincoln-east',
            ]
        },
        {
            'port': '27017 - 28019',
            'source': [
                'p-ops-vpn'
            ]
        },
        {
            'port': 1433,
            'source': [
                '@hudl-lincoln-east'
            ]
        }
    ]
}
