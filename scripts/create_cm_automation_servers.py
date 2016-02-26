#!/usr/bin/env python
import sys
from tyr.servers.mongo import AutomationAgent
import logging
import json
import argparse

log = logging.getLogger('Tyr.Scripts.MongoAutomationServers')
log.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S')
ch.setFormatter(formatter)
log.addHandler(ch)

ACCEPTED_JSON_STRUCT = """
{
  "servers": [
    {
      "group": "foundation",
      "server_type": "mongo",
      "availability_zone": "c",
      "instance_type": "m3.medium",
      "environment": "stage",
      "chef_path": "/Users/steve.schmidt/hudl_work/hudl-chef-repo/.chef/",
      "data_volume_size": 5,
      "data_volume_iops": 0,
      "journal_volume_size": 5,
      "journal_volume_iops": 0,
      "log_volume_size": 1,
      "log_volume_iops": 0,
      "mongodb_cm_group": "stage",
      "mongodb_type": "data"
    },
    {
      "group": "foundation",
      "server_type": "mongo",
      "availability_zone": "d"
      "instance_type": "m3.medium",
      "environment": "stage",
      "chef_path": "/Users/steve.schmidt/hudl_work/hudl-chef-repo/.chef/",
      "data_volume_size": 5,
      "data_volume_iops": 0,
      "journal_volume_size": 5,
      "journal_volume_iops": 0,
      "log_volume_size": 1,
      "log_volume_iops": 0,
      "mongodb_cm_group": "stage",
      "mongodb_type": "data"
    },
    {
      "group": "foundation",
      "server_type": "mongo",
      "availability_zone": "e",
      "instance_type": "m3.medium",
      "environment": "stage",
      "chef_path": "/Users/steve.schmidt/hudl_work/hudl-chef-repo/.chef/",
      "data_volume_size": 5,
      "data_volume_iops": 0,
      "journal_volume_size": 5,
      "journal_volume_iops": 0,
      "log_volume_size": 1,
      "log_volume_iops": 0,
      "mongodb_cm_group": "stage",
      "mongodb_type": "data"
    },
  ]
}
"""

JSON_CLUSTER = """
{
  "servers": [
    {
      "group": "foundation",
      "server_type": "mongo-router",
      "availability_zone": "c",
      "instance_type": "m3.medium",
      "environment": "stage",
      "chef_path": "/Users/steve.schmidt/hudl_work/hudl-chef-repo/.chef/",
      "mongodb_cm_group": "stage",
      "mongodb_type": "router"
    },
    {
      "group": "foundation",
      "server_type": "mongo-config",
      "availability_zone": "c",
      "instance_type": "m3.medium",
      "environment": "stage",
      "chef_path": "/Users/steve.schmidt/hudl_work/hudl-chef-repo/.chef/",
      "data_volume_size": 5,
      "data_volume_iops": 0,
      "journal_volume_size": 5,
      "journal_volume_iops": 0,
      "log_volume_size": 1,
      "log_volume_iops": 0,
      "mongodb_cm_group": "stage",
      "mongodb_type": "config"
    },
    {
      "group": "foundation",
      "server_type": "mongo",
      "availability_zone": "c",
      "instance_type": "m3.medium",
      "environment": "stage",
      "chef_path": "/Users/steve.schmidt/hudl_work/hudl-chef-repo/.chef/",
      "data_volume_size": 5,
      "data_volume_iops": 0,
      "journal_volume_size": 5,
      "journal_volume_iops": 0,
      "log_volume_size": 1,
      "log_volume_iops": 0,
      "mongodb_cm_group": "stage",
      "mongodb_type": "data"
    },
    {
      "group": "foundation",
      "server_type": "mongo",
      "availability_zone": "d"
      "instance_type": "m3.medium",
      "environment": "stage",
      "chef_path": "/Users/steve.schmidt/hudl_work/hudl-chef-repo/.chef/",
      "data_volume_size": 5,
      "data_volume_iops": 0,
      "journal_volume_size": 5,
      "journal_volume_iops": 0,
      "log_volume_size": 1,
      "log_volume_iops": 0,
      "mongodb_cm_group": "stage",
      "mongodb_type": "data"
    }
  ]
}

Setup: 1 Router, 1 Config RS, 1 data node per RS
"""


def read_json(json_file):
    try:
        json_result = json.load(open(json_file))
    except Exception as error:
        log.error("Issue reading JSON file: {error}".format(error=error))
        sys.exit(1)

    return json_result


def update_dict(server_dict):
    default_dict = {
                        "group": None,
                        "server_type": 'mongo',
                        "instance_type": None,
                        "environment": None,
                        "ami": None,
                        "region": None,
                        "role": None,
                        "keypair": None,
                        "availability_zone": None,
                        "security_groups": None,
                        "block_devices": None,
                        "chef_path": None,
                        "subnet_id": None,
                        "dns_zones": None,
                        "data_volume_size": None,
                        "data_volume_iops": None,
                        "journal_volume_size": None,
                        "journal_volume_iops": None,
                        "log_volume_size": None,
                        "log_volume_iops": None,
                        "mongodb_automation_agent": True,
                        "mongodb_cm_group": None,
                        "mongodb_type": None
                   }

    diff_dict = set(default_dict.keys()) - set(server_dict.keys())

    for k in diff_dict:
        server_dict[k] = default_dict[k]

    check_dict = set(server_dict.keys()) - set(default_dict.keys())
    if check_dict:
        for k in check_dict:
            log.error("An invalid instance parameter was used: {k}".format(
                k=k))
            log.error("Please check the JSON deployment file to correct the above issue!")
        sys.exit(1)

    return server_dict

def build_mongo_servers():
    parser = argparse.ArgumentParser()
    json_file_help_msg = "JSON input file with server deployment options"
    parser.add_argument("--json_file", help=json_file_help_msg)
    parser.add_argument("--cluster_example", help="See JSON for Stage Cluster Deploy",
                        action="store_true")
    parser.add_argument("--rs_example", help="See JSON for Stage RS Deploy",
                        action="store_true")
    args = parser.parse_args()

    if args.cluster_example:
        print JSON_CLUSTER
        sys.exit(0)

    if args.rs_example:
        print ACCEPTED_JSON_STRUCT
        sys.exit(0)

    if not args.json_file:
        log.error("Must specify a JSON input file!")
        sys.exit(1)

    json_result = read_json(args.json_file)

    try:
        for server in json_result['servers']:
            server = update_dict(server)
            node = AutomationAgent(group=server['group'],
                                   server_type=server['server_type'],
                                   instance_type=server['instance_type'],
                                   environment=server['environment'],
                                   ami=server['ami'],
                                   region=server['region'],
                                   role=server['role'],
                                   keypair=server['keypair'],
                                   availability_zone=server['availability_zone'],
                                   security_groups=server['security_groups'],
                                   block_devices=server['block_devices'],
                                   chef_path=server['chef_path'],
                                   subnet_id=server['subnet_id'],
                                   dns_zones=server['dns_zones'],
                                   data_volume_size=server['data_volume_size'],
                                   data_volume_iops=server['data_volume_iops'],
                                   journal_volume_size=server['journal_volume_size'],
                                   journal_volume_iops=server['journal_volume_iops'],
                                   log_volume_size=server['log_volume_size'],
                                   log_volume_iops=server['log_volume_iops'],
                                   mongodb_cm_group=server['mongodb_cm_group'],
                                   mongodb_type=server['mongodb_type']
                                   )
            node.autorun()
            node.bake()
    except KeyError as key_msg:
        error_msg = ("Invalid JSON format presented!\n"
                     "The JSON document should look similar to the "
                     "following:\n"
                     "{json_struct}".format(json_struct=ACCEPTED_JSON_STRUCT))
        log.debug(key_msg)
        log.error(error_msg)
        sys.exit(1)

if __name__ == '__main__':
    build_mongo_servers()
