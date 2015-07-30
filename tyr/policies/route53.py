allow_update_route53_prod = """{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "Stmt1427729386000",
            "Effect": "Allow",
            "Action": [
                "route53:ChangeResourceRecordSets"
            ],
            "Resource": [
                "arn:aws:route53:::hostedzone/ZDQ066NWSBGCZ",
                "arn:aws:route53:::hostedzone/Z1LKTAOOYM3H8T"
            ]
        }
    ]
}"""

allow_update_route53_stage = """{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "Stmt1427729386000",
            "Effect": "Allow",
            "Action": [
                "route53:ChangeResourceRecordSets"
            ],
            "Resource": [
                "arn:aws:route53:::hostedzone/Z3ETV7KVCRERYL",
                "arn:aws:route53:::hostedzone/Z24UEMQ8K6Z50Z"
            ]
        }
    ]
}"""

allow_update_route53_test = """{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "Stmt1427729386000",
            "Effect": "Allow",
            "Action": [
                "route53:ChangeResourceRecordSets"
            ],
            "Resource": [
                "arn:aws:route53:::hostedzone/ZAH3O4H1900GY",
                "arn:aws:route53:::hostedzone/ZXXFTW7F1WFIS"
            ]
        }
    ]
}"""
