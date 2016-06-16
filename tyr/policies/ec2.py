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

allow_create_tags = """{
    "Statement": [
        { "Sid": "Stmt1357615676069",
          "Action": [
            "ec2:CreateTags"
          ],
          "Effect": "Allow",
          "Resource": [
            "*"
          ]
        }
    ]
}"""

allow_web_initialization_prod = """{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "s3:GetObject"
      ],
      "Sid": "Stmt1370289990000",
      "Resource": [
        "arn:aws:s3:::hudl-config/common/*",
        "arn:aws:s3:::hudl-config/p-mv-web/*"
      ],
      "Effect": "Allow"
    },
    {
      "Action": [
        "s3:ListBucket"
      ],
      "Sid": "Stmt1370290042000",
      "Condition": {
        "StringLike": {
          "s3:prefix": "p-mv-web/*"
        }
      },
      "Resource": [
        "arn:aws:s3:::hudl-config"
      ],
      "Effect": "Allow"
    },
    {
      "Action": [
        "cloudwatch:DescribeAlarms",
        "cloudwatch:DescribeAlarmsForMetric",
        "cloudwatch:ListMetrics",
        "cloudwatch:PutMetricAlarm",
        "cloudwatch:PutMetricData",
        "cloudwatch:SetAlarmState",
        "route53:ChangeResourceRecordSets"
      ],
      "Sid": "Stmt1370290134000",
      "Resource": [
        "*"
      ],
      "Effect": "Allow"
    }
  ]
}"""


allow_web_initialization_stage = """{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "s3:GetObject"
      ],
      "Sid": "Stmt1370289990000",
      "Resource": [
        "arn:aws:s3:::hudl-config/common/*",
        "arn:aws:s3:::hudl-config/s-mv-web/*"
      ],
      "Effect": "Allow"
    },
    {
      "Action": [
        "s3:ListBucket"
      ],
      "Sid": "Stmt1370290042000",
      "Condition": {
        "StringLike": {
          "s3:prefix": "s-mv-web/*"
        }
      },
      "Resource": [
        "arn:aws:s3:::hudl-config"
      ],
      "Effect": "Allow"
    },
    {
      "Action": [
        "cloudwatch:DescribeAlarms",
        "cloudwatch:DescribeAlarmsForMetric",
        "cloudwatch:ListMetrics",
        "cloudwatch:PutMetricAlarm",
        "cloudwatch:PutMetricData",
        "cloudwatch:SetAlarmState",
        "route53:ChangeResourceRecordSets"
      ],
      "Sid": "Stmt1370290134000",
      "Resource": [
        "*"
      ],
      "Effect": "Allow"
    }
  ]
}"""

allow_outpost_sns_test = """{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "Stmt1390578067000",
      "Effect": "Allow",
      "Action": [
        "sns:ListSubscriptions",
        "sns:ListSubscriptionsByTopic",
        "sns:Publish",
        "sns:Subscribe"
      ],
      "Resource": [
        "arn:aws:sns:us-east-1:761584570493:alyx3",
        "arn:aws:sns:us-east-1:761584570493:t-config-changes",
        "arn:aws:sns:us-east-1:761584570493:t-outpost"
      ]
    },
    {
      "Sid": "Stmt1390578067001",
      "Effect": "Allow",
      "Action": [
        "sns:ConfirmSubscription",
        "sns:Unsubscribe"
      ],
      "Resource": [
        "arn:aws:sns:us-east-1:761584570493:*"
      ]
    },
    {
      "Sid": "Stmt1442579118000",
      "Effect": "Allow",
      "Action": [
          "autoscaling:CompleteLifecycleAction"
      ],
      "Resource": [
          "*"
      ]
    }
  ]
}"""

allow_outpost_sns_prod = """{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "Stmt1390578067000",
      "Effect": "Allow",
      "Action": [
        "sns:ListSubscriptions",
        "sns:ListSubscriptionsByTopic",
        "sns:Publish",
        "sns:Subscribe"
      ],
      "Resource": [
        "arn:aws:sns:us-east-1:761584570493:alyx3",
        "arn:aws:sns:us-east-1:761584570493:p-config-changes",
        "arn:aws:sns:us-east-1:761584570493:p-outpost"
      ]
    },
    {
      "Sid": "Stmt1390578067001",
      "Effect": "Allow",
      "Action": [
        "sns:ConfirmSubscription",
        "sns:Unsubscribe"
      ],
      "Resource": [
        "arn:aws:sns:us-east-1:761584570493:*"
      ]
    },
    {
      "Sid": "Stmt1442579118000",
      "Effect": "Allow",
      "Action": [
          "autoscaling:CompleteLifecycleAction"
      ],
      "Resource": [
          "*"
      ]
    }
  ]
}"""

allow_outpost_sns_stage = """{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "Stmt1390578067000",
            "Effect": "Allow",
            "Action": [
                "sns:ListSubscriptions",
                "sns:ListSubscriptionsByTopic",
                "sns:Publish",
                "sns:Subscribe"
            ],
            "Resource": [
                "arn:aws:sns:us-east-1:761584570493:alyx3",
                "arn:aws:sns:us-east-1:761584570493:stage-config-changes",
                "arn:aws:sns:us-east-1:761584570493:s-outpost"
            ]
        },
        {
            "Sid": "Stmt1390578067001",
            "Effect": "Allow",
            "Action": [
                "sns:ConfirmSubscription",
                "sns:Unsubscribe"
            ],
            "Resource": [
                "arn:aws:sns:us-east-1:761584570493:*"
            ]
        },
        {
            "Sid": "Stmt1442579118000",
            "Effect": "Allow",
            "Action": [
                "autoscaling:CompleteLifecycleAction"
            ],
            "Resource": [
                "*"
            ]
        }
    ]
}"""


allow_set_cloudwatch_alarms = """{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "Stmt1399496077000",
      "Effect": "Allow",
      "Action": [
        "cloudwatch:DescribeAlarms",
        "cloudwatch:PutMetricAlarm"
      ],
      "Resource": [
        "*"
      ]
    }
  ]
}"""

allow_remove_cloudwatch_alarms = """{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "Stmt1399498965000",
      "Effect": "Allow",
      "Action": [
        "cloudwatch:DeleteAlarms"
      ],
      "Resource": [
        "*"
      ]
    }
  ]
}"""

allow_deploy_web_updates = """{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "Stmt1408567829000",
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::hudl-web-updates"
      ]
    },
    {
      "Sid": "Stmt1408567479000",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject"
      ],
      "Resource": [
        "arn:aws:s3:::hudl-web-updates*"
      ]
    }
  ]
}"""

allow_describe_snapshots = """{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "Stmt1435655131000",
            "Effect": "Allow",
            "Action": [
                "ec2:DescribeSnapshotAttribute",
                "ec2:DescribeSnapshots"
            ],
            "Resource": [
                "*"
            ]
        }
    ]
}"""

allow_lifecycle_nginx_stage = """{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "Stmt1465948914000",
            "Effect": "Allow",
            "Action": [
                "autoscaling:CompleteLifecycleAction"
            ],
            "Resource": [
                "*"
            ]
        }
    ]
}"""
