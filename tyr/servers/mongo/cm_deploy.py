#!/usr/bin/env python

import os
import re
import sys
from api_base import ApiBase


class MongoCMDeployment(object):

    MONGO_CM_GROUP_IDS = {
        'community': '550061d0e4b0b14c45cdb727',
        'foundation': '550061e6e4b00b29326c05f1',
        'stage': '56cb432fe4b0669903374adf',
        'teamsports': '55006205e4b03a0ab47a0308'
    }

    try:
        MONGOCM_API_USER = os.environ['MONGOCM_API_USER']
        MONGOCM_API_KEY = os.environ['MONGOCM_API_KEY']
    except Exception as e:
        err_msg = ('Make sure the following environment variables are set: '
                   'MONGOCM_API_USER and MONGOCM_API_KEY\n'
                   'The api key is a public api key associated with the '
                   'MongoCM Group.'
                   )
        print err_msg
        sys.exit(1)

    def __init__(self, mongodb_version='2.6.9', hostnames=None, rs=None,
                 is_shard=False, mongocm_group=None):

        self.mongodb_version = mongodb_version
        self.hostnames = hostnames
        self.rs = rs
        self.is_shard = is_shard
        self.base_url = 'https://cloud.mongodb.com/api/public/v1.0'
        self.mongocm_group_id = self.MONGO_CM_GROUP_IDS[mongocm_group]
        self.api_user = self.MONGOCM_API_USER
        self.api_key = self.MONGOCM_API_KEY
        self.api_base = ApiBase(self.base_url, self.mongocm_group_id,
                                self.api_user, self.api_key)

        if self.rs is None:
            print 'Must pass RS Name!'
            sys.exit(1)

    def get_args_ver(self):
        args_ver = ''
        if re.match('^2\.4.+$', self.mongodb_version):
            args_ver = 'args2_4'
        else:
            args_ver = 'args2_6'

        return args_ver

    def create_config(self):
        configuration = {}
        configuration['options'] = {"downloadBase":
                                    "/var/lib/mongodb-mms-automation"}
        configuration['mongoDbVersions'] = [{"name": self.mongodb_version}]
        configuration['backupVersions'] = []
        configuration['monitoringVersions'] = []
        args_ver = self.get_args_ver()
        process_lst = []
        rs_lst = []

        for num in range(0, len(self.hostnames)):
            process_lst.append({
                args_ver: {
                    "net": {"port": 27018},
                    "replication": {"replSetName": self.rs},
                    "storage": {"dbPath": '/volr/{rs_n}'.format(rs_n=self.rs)},
                    "systemLog": {
                        "destination": "file",
                        "path": '/mongologs/mongodb.log'
                    }
                },
                "hostname": self.hostnames[num],
                "logRotate": {
                    "sizeThresholdMB": 1000,
                    "timeThresholdHrs": 24
                },
                "name": "{rs_n}_{n}".format(rs_n=self.rs, n=num),
                "processType": "mongod",
                "version": self.mongodb_version,
                "authSchemaVersion": 3
            })

            rs_lst.append({
                "_id": self.rs,
                "members": [
                    {
                        "_id": num,
                        "host": "{rs_n}_{h}".format(rs_n=self.rs,
                                                    h=self.hostnames[num]
                                                    )
                    }
                ]
            })

        configuration.update({'processes': process_lst})
        configuration.update({'replicaSets': rs_lst})
        configuration['roles'] = []
        configuration['sharding'] = []

        return configuration

    def post_automation_config(self):
        config = self.create_config()
        url = "%s/groups/%s/automationConfig" % (self.base_url,
                                                 self.mongocm_group_id)
        return self.api_base.put(url, config)


if __name__ == "__main__":
    deployment = MongoCMDeployment(mongodb_version='2.6.9',
                                   hostnames=['testhost0', 'testhost1'],
                                   rs='testrs',
                                   mongocm_group='stage')

    deployment.post_automation_config()
