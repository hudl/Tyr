allow_upload_to_s3_fulla = """{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "Stmt1421959713000",
            "Effect": "Allow",
            "Action": [
                "s3:AbortMultipartUpload",
                "s3:CreateBucket",
                "s3:ListBucketMultipartUploads",
                "s3:PutObject"
            ],
            "Resource": [
                "arn:aws:s3:::ds-fulla/*"
            ]
        }
    ]
}"""

allow_download_scripts_s3_fulla = """{
    "Version":"2012-10-17",
    "Statement":[
        {
            "Sid":"Stmt1408567829000",
            "Effect":"Allow",
            "Action":[
                "s3:ListBucket"
            ],
            "Resource":[
                "arn:aws:s3:::ds-fulla/*"
            ]
        },
        {
            "Sid":"Stmt1408567479000",
            "Effect":"Allow",
            "Action":[
                "s3:GetObject"
            ],
            "Resource":[
                "arn:aws:s3:::ds-fulla/*"
            ]
        }
    ]
}"""

allow_download_script_s3_stage_updater = """{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "Stmt1408567829000",
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::hudl-config/s-mongo/*"
            ]
        },
        {
            "Sid": "Stmt1408567479000",
            "Effect": "Allow",
            "Action": [
                "s3:GetObject"
            ],
            "Resource": [
                "arn:aws:s3:::hudl-config/s-mongo/*"
            ]
        }
    ]
}"""

allow_get_nginx_config = """{
    "Statement": [
        {
            "Sid": "Stmt1367531520229",
            "Action": [
                "s3:GetObject"
             ],
             "Effect": "Allow",
             "Resource": [
                "arn:aws:s3:::hudl-sparkplug/*"
             ]
        }
     ]
}"""

allow_get_hudl_config = """{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "Stmt1434721994000",
            "Effect": "Allow",
            "Action": [
                "s3:GetBucketAcl",
                "s3:GetBucketCORS",
                "s3:GetBucketLocation",
                "s3:GetBucketLogging",
                "s3:GetBucketNotification",
                "s3:GetBucketPolicy",
                "s3:GetBucketRequestPayment",
                "s3:GetBucketTagging",
                "s3:GetBucketVersioning",
                "s3:GetBucketWebsite",
                "s3:GetLifecycleConfiguration",
                "s3:GetObject",
                "s3:GetObjectAcl",
                "s3:GetObjectTorrent",
                "s3:GetObjectVersion",
                "s3:GetObjectVersionAcl",
                "s3:GetObjectVersionTorrent",
                "s3:ListAllMyBuckets",
                "s3:ListBucket",
                "s3:ListBucketMultipartUploads",
                "s3:ListBucketVersions",
                "s3:ListMultipartUploadParts"
            ],
            "Resource": [
                "arn:aws:s3:::hudl-config/*"
            ]
        }
    ]
}
"""
