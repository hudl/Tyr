generic_user_data = """#!/bin/bash

# We don't want to use the latest Amazon Linux repos
/bin/sed -i 's/^releasever/# releasever/' /etc/yum.conf
/usr/bin/yum clean all

META_URL='http://169.254.169.254/latest/meta-data'
MY_INSTANCE_ID=`/usr/bin/curl -s $META_URL/instance-id`
MY_AZ=`/usr/bin/curl -s $META_URL/placement/availability-zone`
MY_REGION="${{MY_AZ%?}}"
MY_TAGS=`/usr/bin/aws ec2 describe-tags --region=$MY_REGION --output=text --filters Name=resource-id,Values=$MY_INSTANCE_ID`
MY_HOSTNAME=`/bin/echo "$MY_TAGS"|awk 'tolower($2) ~ /name/ {{ print tolower($5) }}'`
MY_ROLE=`/bin/echo "$MY_TAGS"|awk 'tolower($2) ~ /role/ {{ print $5 }}'`
MY_ENV=`/bin/echo "$MY_TAGS"|awk 'tolower($2) ~ /environment/ {{ print tolower($5) }}'`

# Our Route 53 zone IDs are hardcoded here.  We can adjust this if we want to
# give nodes the ability to grab their own zone id with list-hosted-zones
# Currently the following IAM Role policy is necessary:
# ChangeResourceRecordSets on arn:aws:route53:::hostedzone/$ROUTE53_ZONE
# This will prevent staging servers from ever updating production
if [ $MY_ENV == "stage" ]; then
  MY_DOMAIN=app.staghudl.com
  ROUTE53_ZONE=Z3ETV7KVCRERYL
  PRIVATE_ZONE=Z24UEMQ8K6Z50Z
elif [ $MY_ENV == "prod" ]; then
  MY_DOMAIN=app.hudl.com
  ROUTE53_ZONE=ZDQ066NWSBGCZ
  PRIVATE_ZONE=Z1LKTAOOYM3H8T
elif [ $MY_ENV == "test" ]; then
  MY_DOMAIN=thorhudl.com
  ROUTE53_ZONE=ZAH3O4H1900GY
  PRIVATE_ZONE=ZXXFTW7F1WFIS
else
  exit 1
fi

if [ -z "$MY_ROLE" ]
then
  ROLE='role[RoleBase]'
else
  ROLE="role[$MY_ROLE]"
fi

# Set the hostname corrently
hostname $MY_HOSTNAME.$MY_DOMAIN

# Let's add our hostname to Route 53 DNS
mkdir '/root/route53'

cat << 'EOF' > /root/route53/upsert.sh
#!/bin/bash
META_URL='http://169.254.169.254/latest/meta-data'
PUBLIC_HOSTNAME=`curl -s $META_URL/public-hostname`
LOCAL_HOSTNAME=`curl -s $META_URL/local-hostname`

cat << EOT > /root/route53/upsert.json
{{
"Comment": "Creating CNAMEs for $HOSTNAME in public $MY_DOMAIN",
"Changes": [
  {{
    "Action": "UPSERT",
    "ResourceRecordSet": {{
      "Name": "$HOSTNAME.",
      "Type": "CNAME",
      "TTL": 60,
      "ResourceRecords": [
        {{
          "Value": "$LOCAL_HOSTNAME"
        }}
      ]
    }}
  }},
  {{
    "Action": "UPSERT",
    "ResourceRecordSet": {{
      "Name": "$HOSTNAME.external.",
      "Type": "CNAME",
      "TTL": 60,
      "ResourceRecords": [
        {{
          "Value": "$PUBLIC_HOSTNAME"
        }}
      ]
    }}
  }}
]
}}
EOT

cat << EOT > /root/route53/upsert_vpc.json
{{
"Comment": "Creating CNAME for $HOSTNAME in private $MY_DOMAIN",
"Changes": [
  {{
    "Action": "UPSERT",
    "ResourceRecordSet": {{
      "Name": "$HOSTNAME.",
      "Type": "CNAME",
      "TTL": 60,
      "ResourceRecords": [
        {{
          "Value": "$LOCAL_HOSTNAME"
        }}
      ]
    }}
  }}
]
}}
EOT

EOF

cat << EOF >> /root/route53/upsert.sh
/usr/bin/aws route53 change-resource-record-sets --region $MY_REGION --hosted-zone-id $ROUTE53_ZONE --change-batch file:///root/route53/upsert.json >> /root/route53/upsert.log 2>&1
/usr/bin/aws route53 change-resource-record-sets --region $MY_REGION --hosted-zone-id $PRIVATE_ZONE --change-batch file:///root/route53/upsert_vpc.json >> /root/route53/upsert.log 2>&1
EOF

chmod +x /root/route53/upsert.sh
/root/route53/upsert.sh
# /root/route53/upsert.sh can be run at any time to generate a new .json file
# and upsert that record into Route 53.  This may be something to run every
# time a node is started.  Useful if a node is stopped and started and the
# public ec2 address changes
cat << EOF >> /etc/rc.local
/root/route53/upsert.sh
EOF

sed -i '/requiretty/d' /etc/sudoers
mkdir /etc/chef
touch /etc/chef/client.rb
echo '{validation_key}' > /etc/chef/validation.pem
echo "
chef_server_url '{chef_server}'
node_name '$MY_HOSTNAME'
environment '$MY_ENV'
validation_client_name 'chef-validator'
" > /etc/chef/client.rb
curl -L https://www.opscode.com/chef/install.sh | bash;
chef-client --server '{chef_server}' --environment $MY_ENV --node-name $MY_HOSTNAME -r "$ROLE" -L {logfile}
"""
