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
