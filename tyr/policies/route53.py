allow_update_route53_stage = """{
    "Statement": [
        {
            "Sid": "Stmt1367531520227",
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

allow_update_route53_prod = """{
    "Statement": [
        {
            "Sid": "Stmt1367531520227",
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

# We'll just put this here for now in case it's ever needed
allow_update_route53_thor = """{
    "Statement": [
        {
            "Sid": "Stmt1367531520227",
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
