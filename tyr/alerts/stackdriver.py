#!/usr/bin/python
# -*- coding: utf8 -*-
import requests
import json
import logging
import re
import os


API_ENDPOINT = 'https://api.stackdriver.com/'
API_KEY = os.environ['STACKDRIVER_API_KEY']
LOGIN_URL = 'https://app.stackdriver.com/account/login/'
POST_ALERT_URL = "https://app.stackdriver.com/api/alerting/policy"

log = logging.getLogger('tyr.alerts.StackDriver')
if not log.handlers:
    log.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '%(asctime)s [%(name)s] %(levelname)s: %(message)s',
        datefmt='%H:%M:%S')
    ch.setFormatter(formatter)
    log.addHandler(ch)

LIST_POLICY_URL = "/v0.2/alerting/policies/"
LIST_GROUPS_URL = "/v0.2/groups/"
GET_POLICY_URL = "/v0.2/alerting/policies/{policy_id}/"
GET_GROUP_URL = "/v0.2/groups/{group_id}/"
LIST_GROUP_MEMBERS_URL = "/v0.2/groups/{group_id}/members/"


class StackDriver:

    def __init__(self):
        self.headers = {"x-stackdriver-apikey": API_KEY}
        self.read_config()
        self.policies = self.get_policy_list()
        self.groups = self.get_group_list()

    def exit_flush(self, code):
        logging.shutdown()
        exit(code)

    def read_config(self):
        with open(os.path.abspath(os.path.dirname(__file__)) +
                  '/../policies/stackdriver_conditions.json', 'r') as jsonfile:
            self.conditions = json.load(jsonfile)

        with open(os.path.abspath(os.path.dirname(__file__)) +
                  '/../policies/stackdriver_notifications.json',
                  'r') as jsonfile:
            self.notifications = json.load(jsonfile)

    def get_policy_list(self):
        r = requests.get(API_ENDPOINT + LIST_POLICY_URL, headers=self.headers)
        return r.json()

    def pretty_print_json(self, obj):
        print(json.dumps(obj, sort_keys=True,
                         indent=4, separators=(',', ': ')))

    def get_group_list(self):
        groups = requests.get(API_ENDPOINT + LIST_GROUPS_URL,
                              headers=self.headers)
        return groups.json()['data']

    def get_group_id_by_name(self, name):
        for group in self.groups:
            if group['name'] == name:
                log.debug('Retrieved group {id} for {group}'
                          .format(id=group['id'], group=name))
                return group['id']

    def get_group_by_id(self, id):
        group = requests.get(API_ENDPOINT + GET_GROUP_URL.format(group_id=id),
                             headers=self.headers).json()
        log.debug('Retrieved group {group} for {id}'
                  .format(id=group['id'], group=group['name']))
        return group

    def get_policies_applied_to_group(self, group):
        '''
        Get a list of policies applied to a group name
        '''
        group_id = self.get_group_id_by_name(group)
        pol_list = []
        for c in self.policies['data']:
            if c['condition']:
                for e in c['condition']['children']:
                    try:
                        if 'group' in e['options']['applies_to']:
                            if e['options']['group_id'] == group_id:
                                pol_list.append(e)
                    except KeyError:
                        pass
        return pol_list

    def test_condition_applied_to_group_name(self, policy, group):
        '''
        Test a policy condition is applied to a given group name
        '''
        pols = self.get_policies_applied_to_group(group)
        for pol in pols:
            try:
                if self.condition_subset_in_superset(policy, pol):
                    return True
                    break
            except KeyError:
                pass
        return False

    # t
    def get_all_groups_without_condition(self, policy):
        '''
        Return all groups that are missing a particular policy condition
        '''
        missing = []
        matches = []
        groups = self.groups
        for group in groups:
            if self.test_condition_applied_to_group_name(policy,
                                                         group['name']):
                matches.append(group)
                break
        for g in groups:
            if g not in matches:
                missing.append(g)
        return missing

    def get_all_groups_with_condition(self, policy):
        '''
        Return all groups that have a particular policy condition
        '''
        matches = []
        groups = self.groups
        for group in groups:
            if self.test_condition_applied_to_group_name(policy,
                                                         group['name']):
                matches.append(group)
                break
        return matches

    def test_general_conditions(self):
        '''
        Test whether a policy condition is applied everywhere it should be for
        general_ named conditions
        '''
        for name, pol in self.conditions.iteritems():
            if 'groups' in pol:
                groups = pol['groups']
                if name.startswith("general_"):
                    for group in groups:
                        if self.test_condition_applied_to_group_name(pol,
                                                                     group):
                            print("Policy {n} present in group {g}"
                                  .format(n=name, g=group))
                        else:
                            print("Policy {n} NOT present in group {g}"
                                  .format(n=name, g=group))

    def test_specific_conditions(self, classifier):
        '''
        Test whether a policy condition is applied everywhere it should be
        for x_ named conditions
        '''
        for name, pol in self.conditions.iteritems():
            if 'groups' in pol:
                groups = pol['groups']
                if name.startswith(classifier):
                    for group in groups:
                        if self.test_condition_applied_to_group_name(pol,
                                                                     group):
                            print("Policy {n} present in group {g}"
                                  .format(n=name, g=group))
                        else:
                            print("Policy {n} NOT present in group {g}"
                                  .format(n=name, g=group))

    def condition_subset_in_superset(self, subset, superset):
        log.debug(subset)
        log.debug(superset)
        match = True
        if not subset['condition_type'] == superset['condition_type']:
            log.debug("{o} not equal to {p}"
                      .format(o=subset['condition_type'],
                              p=superset['condition_type']))
            match = False
        for key, o in subset['options'].iteritems():
            log.debug("Testing key: " + key)
            if o != superset['options'][key]:
                match = False
                log.debug("{o} not equal to {p}"
                          .format(o=o, p=superset['options'][key]))
            else:
                log.debug("{o} IS equal to {p}"
                          .format(o=o, p=superset['options'][key]))
        log.debug(match)
        return match

    def create_csv_of_all_groups(self, filename):
        import csv
        with open(filename, 'wb') as csvfile:
            writer = csv.writer(csvfile, dialect='excel')
            writer.writerow(['group', 'policy_name', 'condition_type'
                             'metric_name', 'metric_type', 'threshold',
                             'window', 'process'])
            keys = ['metric_name', 'metric_type',
                    'threshold', 'window', 'process']
            for group in self.groups:
                pols = self.get_policies_applied_to_group(group['name'])
                for pol in pols:
                    opts_list = []
                    opts_list.append(group['name'])
                    opts_list.append(pol['name'])
                    opts_list.append(pol['condition_type'])
                    for key in keys:
                        try:
                            if pol['options'][key]:
                                opts_list.append(pol['options'][key])
                        except KeyError:
                                opts_list.append(' ')
                    writer.writerow(opts_list)

    # TODO: This is not yet complete
    def create_policy_for_group(self,
                                conditions,
                                group,
                                condition_type='or',
                                notification_type='general_'):
        '''
        Create a new stackdriver alert policy from a template and apply to
        a specified group name
        '''
        name = 'test'
        conditions_template = []
        for c in conditions:
            copy = c.copy()
            copy['options']['applies_to'] = 'group'
            copy['options']['group_id'] = self.get_group_id_by_name(group)
            conditions_template.append(copy)
        notifications = [v for k, v in self.notifications.items()
                         if k.startswith(notification_type)]
        pol_template = {
            "name": name,
            "condition": {
                "condition_type": condition_type,
                "options": {},
                "children": conditions
            },
            "notification_methods": notifications,
            "document": {
                "body": "Created by Tyr from policy template xxx"
            }
        }

        #URL to submit to https://app.stackdriver.com/api/alerting/policy
