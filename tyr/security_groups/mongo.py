rule = '.-.+-mongo'

definition = {
    'rules': [
        {
            'port': '27017 - 27019',
            'source': [
                '{env}-{group}-mongo',
                '{env}-{group}-web',
                {
                    'rule': '[ts]-.+-mongo',
                    'value': 'thors'
                },
                {
                    'rule': 'p-.+-mongo',
                    'value': '{env}-mms'
                }
            ]
        }
    ]
}
