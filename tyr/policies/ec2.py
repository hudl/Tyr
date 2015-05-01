allow_volume_control = """{
    "Statement": [
        {
            "Sid": "Stmt1367531520227",
            "Action": [
                "ec2:AttachVolume",
                "ec2:CreateVolume",
                "ec2:DescribeVolumeAttribute",
                "ec2:DescribeVolumeStatus",
                "ec2:DescribeVolumes",
                "ec2:EnableVolumeIO",
                "ec2:DetachVolume"
             ],
             "Effect": "Allow",
             "Resource": [
                "*"
             ]
        }
     ]
}"""

allow_describe_instances = """{
    "Statement": [
        {
            "Sid": "Stmt1367531529529",
            "Action": [
                "ec2:DescribeInstances"
             ],
             "Effect": "Allow",
             "Resource": [
                "*"
             ]
        }
     ]
}"""

allow_describe_tags = """{
    "Statement": [
        {
            "Sid": "Stmt1367531520228",
            "Action": [
                "ec2:DescribeTags"
             ],
             "Effect": "Allow",
             "Resource": [
                "*"
             ]
        }
     ]
}"""
