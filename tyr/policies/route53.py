allow_update_route53_stage = """{
    "Statement": [
        {
            "Sid": "Stmt1367531520220",
            "Action": [
                "route53:ChangeResourceRecordSets"
             ],
             "Effect": "Allow",
             "Resource": [
                "arn:aws:route53:::hostedzone/Z3ETV7KVCRERYL"
             ]
        }
     ]
}"""

allow_update_route53_stage_private = """{
    "Statement": [
        {
            "Sid": "Stmt1367531520221",
            "Action": [
                "route53:ChangeResourceRecordSets"
             ],
             "Effect": "Allow",
             "Resource": [
                "arn:aws:route53:::hostedzone/Z24UEMQ8K6Z50Z"
             ]
        }
     ]
}"""

allow_update_route53_prod = """{
    "Statement": [
        {
            "Sid": "Stmt1367531520222",
            "Action": [
                "route53:ChangeResourceRecordSets"
             ],
             "Effect": "Allow",
             "Resource": [
                "arn:aws:route53:::hostedzone/ZDQ066NWSBGCZ"
             ]
        }
     ]
}"""

allow_update_route53_prod_private = """{
    "Statement": [
        {
            "Sid": "Stmt1367531520323",
            "Action": [
                "route53:ChangeResourceRecordSets"
             ],
             "Effect": "Allow",
             "Resource": [
                "arn:aws:route53:::hostedzone/Z1LKTAOOYM3H8T"
             ]
        }
     ]
}"""

allow_update_route53_thor = """{
    "Statement": [
        {
            "Sid": "Stmt1367531520224",
            "Action": [
                "route53:ChangeResourceRecordSets"
             ],
             "Effect": "Allow",
             "Resource": [
                "arn:aws:route53:::hostedzone/ZAH3O4H1900GY"
             ]
        }
     ]
}"""

allow_update_route53_thor_private = """{
    "Statement": [
        {
            "Sid": "Stmt1367531520225",
            "Action": [
                "route53:ChangeResourceRecordSets"
             ],
             "Effect": "Allow",
             "Resource": [
                "arn:aws:route53:::hostedzone/ZXXFTW7F1WFIS"
             ]
        }
     ]
}"""
