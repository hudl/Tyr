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

allow_mongo_backup_snapshot = """{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": [
                "ec2:CreateTags",
                "ec2:DescribeTags",
                "ec2:CreateSnapshot",
                "ec2:DescribeInstances"
            ],
            "Sid": "Stmt1372359394000",
            "Resource": [
                "*"
            ],
            "Effect": "Allow"
        }
    ]
}"""

allow_mongo_snapshot_cleanup = """{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": [
                "ec2:DescribeSnapshots",
                "ec2:DeleteSnapshot"
            ],
            "Sid": "Stmt1372440398000",
            "Resource": [
                "*"
            ],
            "Effect": "Allow"
        }
    ]
}"""
