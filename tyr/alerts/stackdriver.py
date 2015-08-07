#!/usr/bin/python
# -*- coding: utf8 -*-
import requests
import json
import logging
import re
import os
import collections
from copy import deepcopy
from tyr.policies.stackdriver import conditions
from tyr.policies.stackdriver import notification_types
from tyr.policies.stackdriver import notification_groups
from tyr.policies.stackdriver import notification_lookups

API_ENDPOINT = 'https://api.stackdriver.com/'
API_KEY = os.environ['STACKDRIVER_API_KEY']
USERNAME = os.environ['STACKDRIVER_USERNAME']
PASSWORD = os.environ['STACKDRIVER_PASSWORD']
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

# URLs not in the API
CREATE_POLICY_URL = "https://app.stackdriver.com/api/alerting/policy"
USER_LOGIN_URL = "https://app.stackdriver.com/account/login/"
USER_LOGOUT_URL = "https://app.stackdriver.com/account/logout/"
STATIC_WEBHOOKS_URL = "https://app.stackdriver.com/api/settings/static_webhook"
TEAMS_URL = "https://app.stackdriver.com/api/settings/teams"
SLACK_URL = "https://app.stackdriver.com/api/settings/slack"
PAGERDUTY_SERVICES_URL = "https://app.stackdriver.com/api/settings/pagerduty_services"


class StackDriver:

    def __init__(self):
        self.headers = {"x-stackdriver-apikey": API_KEY}
        self.conditions = conditions
        self.notification_types = notification_types
        self.notification_groups = notification_groups
        self.notification_lookups = notification_lookups
        self.policies = self.get_policy_list()
        self.groups = self.get_group_list()
        self.user_login()
        self.teams = self.get_teams_list()
        self.webhooks = self.get_static_webhooks_list()

    def exit_flush(self, code):
        logging.shutdown()
        exit(code)

    def merge_dict(self, a, b):
        '''recursively merges dict's. not just simple a['key'] = b['key'], if
        both a and b have a key who's value is a dict then dict_merge is called
        on both values and the result stored in the returned dictionary.
        See: https://www.xormedia.com/recursively-merge-dictionaries-in-python/
        '''
        if not isinstance(b, dict):
            return b
        result = deepcopy(a)
        for k, v in b.iteritems():
            if k in result and isinstance(result[k], dict):
                    result[k] = dict_merge(result[k], v)
            else:
                result[k] = deepcopy(v)
        return result

    def get_policy_list(self):
        return self.get_paginated_list(LIST_POLICY_URL)

    def pretty_print_json(self, obj):
        print(json.dumps(obj, sort_keys=True,
                         indent=4, separators=(',', ': ')))

    def get_teams_list(self):
        r = self.session.get(TEAMS_URL)
        r.raise_for_status()
        # We get back some slightly mangled JSON here
        return r.text.split('\n')[1]

    def get_static_webhooks_list(self):
        r = self.session.get(STATIC_WEBHOOKS_URL)
        # We get back some slightly mangled JSON here
        r.raise_for_status()
        return r.text.split('\n')[1]

    def get_group_list(self):
        groups = self.get_paginated_list(LIST_GROUPS_URL)
        return groups['data']

    def get_paginated_list(self, list_url):
        r = requests.get(API_ENDPOINT + list_url,
                         headers=self.headers)
        r.raise_for_status()
        full_list = r.json()
        part_list = r.json()

        while True:
            if 'next' in part_list['meta']:
                r = requests.get(API_ENDPOINT + part_list['meta']['next'],
                                 headers=self.headers)
                r.raise_for_status()
                part_list = r.json()
                if len(part_list['data']) > 0:
                    full_list['data'].extend(part_list['data'])
            else:
                break
        return full_list

    def get_group_id_by_name(self, name):
        if '/' in name:
            # Group is a subgroup
            parent = name.split('/')[0]
            child = name.split('/')[1]
        else:
            parent = None
        if parent:
            parent_id = None
            child_id = None
            for group in self.groups:
                if group['name'] == parent:
                    parent_id = group['id']
            for group in self.groups:
                if group['name'] == child and group['parent_id'] == parent_id:
                    child_id = group['id']
                    log.debug('Retrieved child group {c} for {g} & parent {p}'
                              .format(p=parent_id, c=child_id, g=name))
                    return child_id
            raise Exception('Unable to get parent/child group for name {g}!'
                            .format(g=name))

        else:
            # Group is not a subgroup, so we should ignore them
            for group in self.groups:
                if group['name'] == name and not group['parent_id']:
                    log.debug('Retrieved group {id} for {group}'
                              .format(id=group['id'], group=name))
                    return group['id']

        raise Exception("Group {g} was not found!".format(g=name))

    def get_group_name_by_id(self, id):
        for group in self.groups:
            if group['id'] == id:
                log.debug('Retrieved group {name} for {id}'
                          .format(id=group['id'], name=group['name']))
                return group['name']

    def get_group_by_id(self, id):
        r = requests.get(API_ENDPOINT + GET_GROUP_URL.format(group_id=id),
                         headers=self.headers)
        r.raise_for_status()
        group = r.json()['data']
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
            writer.writerow(['group', 'parent_group', 'policy_name',
                             'condition_type', 'metric_name', 'metric_type',
                             'threshold', 'window', 'process'])
            keys = ['metric_name', 'metric_type',
                    'threshold', 'window', 'process']
            for group in self.groups:
                pols = self.get_policies_applied_to_group(group['name'])
                for pol in pols:
                    opts_list = []
                    opts_list.append(group['name'])
                    if group['parent_id']:
                        opts_list.append(
                            self.get_group_name_by_id(group['parent_id']))
                    else:
                        opts_list.append(' ')
                    opts_list.append(pol['name'])
                    opts_list.append(pol['condition_type'])
                    for key in keys:
                        try:
                            if pol['options'][key]:
                                opts_list.append(pol['options'][key])
                        except KeyError:
                                opts_list.append(' ')
                    writer.writerow(opts_list)

    def user_login(self):
        '''
        Log into the stackdriver app as a normal user
        '''
        # Pick up a cookie and csrf session token
        self.session = requests.Session()
        r = self.session.get(USER_LOGIN_URL)
        r.raise_for_status()
        self.csrftoken = r.cookies['csrftoken']
        print r.cookies

        # Now actually login
        data = {
            "csrfmiddlewaretoken": self.csrftoken,
            "username": USERNAME,
            "password": PASSWORD,
            "next": None
        }

        headers = {
            "Referer": USER_LOGIN_URL,
            "Host": "app.stackdriver.com",
            "Origin": "https://app.stackdriver.com",
        }
        l = self.session.post(USER_LOGIN_URL, data=data,
                              cookies=self.session.cookies, headers=headers)
        l.raise_for_status()
        # Test another request is working
        t = self.session.get(STATIC_WEBHOOKS_URL, headers=headers)
        t.raise_for_status()

    def user_logout(self):
        '''
        Logout of the frontend app
        '''
        headers = {'Referer': 'https://app.stackdriver.com/'}
        r = self.session.get(USER_LOGOUT_URL, headers=headers)
        r.raise_for_status()
        self.csrftoken = None
        return r

    # TODO: This is not yet complete
    def create_policy_for_group(self,
                                name,
                                conditions,
                                group,
                                condition_type='or',
                                notification_group='test'):
        '''
        Create a new stackdriver alert policy from a template and apply to
        a specified group name
        '''
        conditions_template = []
        notifications = []
        for c in conditions:
            copy = c.copy()
            copy['options']['applies_to'] = 'group'
            copy['options']['group_id'] = self.get_group_id_by_name(group)
            if copy['groups']:
                copy.pop('groups')
            copy['name'] = ('Tyr_applied_condition {typ} {c} {thres} for {g}'
                            .format(typ=copy['options']['metric_type'],
                                    c=copy['options']['comparison'],
                                    thres=copy['options']['threshold'],
                                    g=group))
            conditions_template.append(copy)

        for k, grp in self.notification_groups.items():
            if notification_group in k:
                for typ, lookup in grp.items():
                    type_template = self.notification_types[typ].copy()
                    type_template['notification_value'] = \
                        self.notification_lookups[typ][lookup]
                    notifications.append(type_template)

        headers = {
            "Referer": "https://app.stackdriver.com/policy-advanced/create",
            "Host": "app.stackdriver.com",
            "Origin": "https://app.stackdriver.com",
            "X-CSRFToken": self.csrftoken,
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate"
        }

        pol_template = {
            "name": name,
            "condition": {
                "condition_type": condition_type,
                "options": {},
                "children": conditions_template
            },
            "notification_methods": notifications,
            "document": {
                "body": "Created by Tyr from policy template {name}"
                .format(name=name)
            }
        }
        self.pretty_print_json(pol_template)

        r = self.session.post(CREATE_POLICY_URL,
                              json=pol_template,
                              headers=headers)
        #r.raise_for_status()
        return r
