
allow_describe_elbs = """{
    "Statement": [
        {
            "Sid": "Stmt1367531520500",
            "Action": [
                "elasticloadbalancing:DescribeLoadBalancers",
                "elasticloadbalancing:DescribeInstanceHealth"
             ],
             "Effect": "Allow",
             "Resource": [
                "*"
             ]
        }
     ]
}"""

allow_modify_nginx_elbs_stage = """{
    "Statement": [
        {
            "Sid": "Stmt1367531520501",
            "Action": [
                "elasticloadbalancing:DeregisterInstancesFromLoadBalancer",
                "elasticloadbalancing:RegisterInstancesWithLoadBalancer"
             ],
             "Effect": "Allow",
             "Resource": [
                "arn:aws:elasticloadbalancing:us-east-1:761584570493:loadbalancer/recruit-stage",
                "arn:aws:elasticloadbalancing:us-east-1:761584570493:loadbalancer/hudl-stage",
                "arn:aws:elasticloadbalancing:us-east-1:761584570493:loadbalancer/recruit-stage-vpc",
                "arn:aws:elasticloadbalancing:us-east-1:761584570493:loadbalancer/hudl-stage-vpc"
             ]
        }
     ]
}"""

allow_modify_nginx_elbs_prod = """{
    "Statement": [
        {
            "Sid": "Stmt1367531520502",
            "Action": [
                "elasticloadbalancing:DeregisterInstancesFromLoadBalancer",
                "elasticloadbalancing:RegisterInstancesWithLoadBalancer"
             ],
             "Effect": "Allow",
             "Resource": [
                "arn:aws:elasticloadbalancing:us-east-1:761584570493:loadbalancer/recruit-prod",
                "arn:aws:elasticloadbalancing:us-east-1:761584570493:loadbalancer/hudl-primary",
                "arn:aws:elasticloadbalancing:us-east-1:761584570493:loadbalancer/recruit-prod-vpc",
                "arn:aws:elasticloadbalancing:us-east-1:761584570493:loadbalancer/hudl-primary-vpc"
             ]
        }
     ]
}"""
