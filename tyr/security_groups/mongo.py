rule = '.-.+-mongo'

definition = {
    'rules': [
        {
            'port': '27017 - 27019',
            'source': [
                '{env}-{group}-mongo',
                '{env}-{group}-web'
            ]
        }
    ]
}
