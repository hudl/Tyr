security_groups = {
    't-performancecenter-mongo': {
        'name': 't-performancecenter-mongo',
        'rules': [
            {
                'ip_protocol': 'tcp',
                'from_port': 27017,
                'to_port': 27019,
                'src_group': 't-performancecenter-mongo'
            }
        ]
    }
}
