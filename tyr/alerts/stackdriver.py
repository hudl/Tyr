#!/usr/bin/python

#
# Some examples:
#
# To add all current web alert policies to a new multiverse group:
# s.create_policy_for_group("test policy chrisg",
#                           s.conditions['web'], "p-myservice/web")
#
# To add a custom condtion list:
#
# conditions = [{
#     "condition_type": "threshold",
#     "name": "Tyr_applied_condition disk_usage above 0.7 for p-queues",
#     "existing": True,
#     "options": {
#       "resource_type": "instance",
#       "applies_to": "group",
#       "group_id": 1282,
#       "metric_name": "disk_usage",
#       "useWildcards": False,
#       "comparison": "above",
#       "window": 600,
#       "customMetricMatches": [],
#       "metric_type": "disk_usage",
#       "condition_trigger": "any",
#       "metric_key": "instance.disk_usage.usage_percent",
#       "threshold_unit": "percent",
#       "suggested_thresholds": {},
#       "threshold": 0.7
#     }
# }]
# r = s.create_policy_for_group("test policy chrisg", conditions, "p-queues")
#
#
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
SLACK_HOOKS_URL = "https://app.stackdriver.com/api/settings/slack"
EMAIL_HOOKS_URL = "https://app.stackdriver.com/api/settings/email"
PAGERDUTY_HOOKS_URL = "https://app.stackdriver.com/api/settings/pagerduty_services"


class StackDriver:

    def __init__(self):
        self.headers = {"x-stackdriver-apikey": API_KEY}
        self.conditions = conditions
        self.notification_types = notification_types
        self.notification_groups = notification_groups
        self.user_login()
        self.update_cache()

    def update_cache(self):
        '''
        Update cached data from stackdriver
        '''
        self.policies = self.get_policy_list()
        self.groups = self.get_group_list()
        self.teams = self.get_teams_list()
        self.webhooks = self.get_static_webhooks_list()
        self.pagerduty = self.get_pagerduty_hooks_list()

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
        return json.loads(r.text.split('\n')[1])

    def get_static_webhooks_list(self):
        r = self.session.get(STATIC_WEBHOOKS_URL)
        # We get back some slightly mangled JSON here
        r.raise_for_status()
        return json.loads(r.text.split('\n')[1])

    def get_pagerduty_hooks_list(self):
        r = self.session.get(PAGERDUTY_HOOKS_URL)
        # We get back some slightly mangled JSON here
        r.raise_for_status()
        return json.loads(r.text.split('\n')[1])

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

    def get_policies_applied_to_group_id(self, group_id):
        '''
        Get a list of policies applied to a group id
        '''
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

    def test_condition_applied_to_group_id(self, policy, group,
                                           ignore_window=True):
        '''
        Test a policy condition is applied to a given group name
        If ignore_window is specified, the condition will be matched
        if everything but the time window match
        '''
        if ignore_window:
            ignore = ['window']
        pols = self.get_policies_applied_to_group_id(group['id'])
        log.debug('{n} policies applied to group id: {g}'
                  .format(n=len(pols), g=group['id']))
        for pol in pols:
            try:
                if self.condition_subset_in_superset(policy, pol,
                                                     ignore_options=ignore):
                    return True
                    break
            except KeyError:
                raise
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
            if self.test_condition_applied_to_group_id(policy,
                                                       group['id']):
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
            if self.test_condition_applied_to_group_id(policy,
                                                       group['id']):
                matches.append(group)
                break
        return matches

    def test_for_subgroup(self, specified_group):
        '''
        Test for a subgroup in the group string
        '''
        parent_group_id = None
        parent_group_name = None
        if '/' in specified_group:
            if len(specified_group.split('/')) > 2:
                raise Exception("This method does not support"
                                "multiple-levels of subgroups.")
            else:
                is_subgroup = True
                search_group = specified_group.split('/')[1]
                parent_group_name = specified_group.split('/')[0]
                if '*' not in parent_group_name:
                    parent_group_id = self.get_group_id_by_name(
                        parent_group_name)
        else:
            is_subgroup = False
            search_group = specified_group
        return {"is_subgroup": is_subgroup,
                "search_group": search_group,
                "parent_group_id": parent_group_id,
                "parent_group_name": parent_group_name}

    def get_defined_group_policies(self, specified_group):
        '''
        Test we have policies defined for this group name
        '''
        r = self.test_for_subgroup(specified_group)
        search_group = r['search_group']
        is_subgroup = r['is_subgroup']

        if search_group in self.conditions.keys():
            pols = self.conditions[search_group]
        elif (('*/' + search_group) in self.conditions.keys()
                and is_subgroup):
                    pols = self.conditions['*/' + search_group]
        else:
            raise Exception("No policies are defined for group: {g}"
                            .format(g=specified_group))
        return pols

    def test_specific_conditions(self, specified_group):
        '''
        Test whether a policy condition is applied everywhere it should be
        for a given search group.  Will accept subgroups via a */subgroup
        identifier.  Uses the stackdriver policies list
        '''
        r = self.test_for_subgroup(specified_group)
        search_group = r['search_group']
        parent_group_id = r['parent_group_id']
        parent_group_name = r['parent_group_name']
        is_subgroup = r['is_subgroup']
        pols = self.get_defined_group_policies(specified_group)

        group_list = []
        missing = []
        if is_subgroup:
            # We know it's a subgroup, so allow a matching parent group
            # or a * wildcard
            for group in self.groups:
                if group['name'] == search_group and (
                        group['parent_id'] == parent_group_id
                        or parent_group_name == '*'):
                            group_list.append(group)
        else:
            # It's a parent group so exclude any subgroups
            for group in self.groups:
                if group['name'] == search_group and (not group['parent_id']):
                        group_list.append(group)
        for group in group_list:
            for pol in pols:
                name = pol['name']
                if self.test_condition_applied_to_group_id(pol,
                                                           group):
                    log.info("Policy {n} present in group {g}"
                             .format(n=name, g=group['id']))
                else:
                    log.info("Policy {n} NOT present in group {g}"
                             .format(n=name, g=group['id']))
                    missing.append({"name": name, "condition": pol,
                                    "group_id": group['id'],
                                    "parent_group_name":
                                    self.get_group_name_by_id(
                                        group["parent_id"])})
        return missing

    def apply_missing_conditions(self, condition_group, notification_group):
        '''
        Automatically apply any missing conditions from a configured condition
        group and add apporpriate notifications
        '''
        missing = self.test_specific_conditions(condition_group)
        for m in missing:
            self.create_policy_for_group(m['name'],
                                         [m['condition']],
                                         m['group_id'],
                                         condition_type='or',
                                         notification_group=notification_group,
                                         update_cache=False)
        self.update_cache()

    def delete_policies_for_group(self, group_name):
        '''
        Deletes the policies attached to a given group/subgroup name
        '''
        pass

    def condition_subset_in_superset(self, subset_input, superset_input,
                                     ignore_options=[]):
        '''
        Test for a subset of a condition by only including particular fields
        add ignore_options to exclude additional fields (e.g. window)
        '''
        metric_name_equivilents = [
            ("windows_cpu", "cpu"),
            ("windows_cpu", "winagent:cpu"),
            ("windows_memory", "memory"),
            ("windows_disk_usage", "disk_usage"),
            ("windows_disk_usage", "winagent:disk"),
            ("windows_disk_usage", "winagent:disk:*"),
            ("memory", "agent:memory::memory:used:pct"),
            ("disk_usage", "agent:df:*:df_complex:used:pct"),
            ("cpu", "agent:aggregation:cpu-average:cpu:idle:pct")
        ]
        remove_options = ['group_id', 'suggested_thresholds', 'useWildcards',
                          'customMetricMatches', 'condition_trigger',
                          'sub_resource', 'useUsername']
        if ignore_options:
            remove_options.extend(ignore_options)

        # Remove some newer fields to make comparison more accurate
        subset = deepcopy(subset_input)
        superset = deepcopy(superset_input)
        log.debug(subset)
        subset.pop('name')
        for field in remove_options:
            try:
                subset['options'].pop(field)
            except KeyError:
                pass

        # Remove metric_name, metric_type and metric_key
        # if they don't exist in superset
        check_ops = ['metric_name', 'metric_type',
                     'metric_key', 'threshold_unit']
        for opt in check_ops:
            if (opt not in superset['options']
               and opt in subset['options']):
                    log.debug('Removing {opt} as it is not in superset'
                              .format(opt=opt))
                    subset['options'].pop(opt)

        # Get some metric name to compare with equivilents
        if 'metric_name' in subset["options"]:
            name_tuple = (subset["options"]["metric_name"],
                          superset["options"]["metric_name"])
            if name_tuple in metric_name_equivilents:
                log.debug('Removing metric name '
                          'as they are equivilent.')
                subset['options'].pop('metric_name')

        if 'metric_type' in subset["options"]:
            type_tuple = (subset['options']["metric_type"],
                          superset['options']['metric_type'])
            if type_tuple in metric_name_equivilents:
                log.debug('Removing metric type '
                          'as they are equivilent.')
                subset['options'].pop('metric_type')

        match = True
        if not subset['condition_type'] == superset['condition_type']:
            log.debug("{o} not equal to {p}"
                      .format(o=subset['condition_type'],
                              p=superset['condition_type']))
            match = False

        if match:
            for key, o in subset['options'].iteritems():
                p = None
                q = None
                log.debug("Testing key: " + key)
                try:
                    if isinstance(o, basestring):
                        p = o.lower()
                        if p == '':
                            p = None
                        if key in superset['options']:
                            if isinstance(superset['options'][key], basestring):
                                q = superset['options'][key].lower()
                        else:
                            q = None
                    else:
                        p = o
                        q = superset['options'][key]
                    if p != q:
                        match = False
                        log.debug("{p} not equal to {q}"
                                  .format(p=p, q=q))
                        break
                    else:
                        log.debug("{p} IS equal to {q}"
                                  .format(p=p, q=q))
                except KeyError:
                    match = False
                    break
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
                pols = self.get_policies_applied_to_group_id(group['id'])
                if not pols:
                    if group['parent_id']:
                        parent_id = self.get_group_name_by_id(
                            group['parent_id'])
                    else:
                        parent_id = ' '
                    writer.writerow([group['name'], parent_id
                                    , ' ', ' ', ' ', ' ', ' ', ' ', ' '])
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
        log.debug(r.cookies)

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
        self.csrftoken = self.session.cookies['csrftoken']
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

    def create_policy_for_group(self,
                                name,
                                conditions,
                                group_id,
                                condition_type='or',
                                notification_group='test',
                                update_cache=True):
        '''
        Create a new stackdriver alert policy from a template and apply to
        a specified group name
        '''
        conditions_template = []
        notifications = []
        for c in conditions:
            copy = deepcopy(c)
            copy['options']['applies_to'] = 'group'
            copy['options']['group_id'] = group_id
            if 'groups' in copy:
                copy.pop('groups')
            if copy['condition_type'] == "process_health":
                type_desc = "process_health"
            else:
                type_desc = copy['options']['metric_type']
            copy['name'] = ('Tyr_applied_condition {typ} {c} {thres} for {g}'
                            .format(typ=type_desc,
                                    c=copy['options']['comparison'],
                                    thres=copy['options']['threshold'],
                                    g=group_id))
            conditions_template.append(copy)

        for k, grp in self.notification_groups.items():
            if notification_group in k:
                for typ, lookup in grp.items():
                    if typ == "heimdall_webhook":
                        field = self.webhooks
                        key = "webhook_name"
                    elif typ == "team_email":
                        field = self.teams
                        key = "team_name"
                    elif typ == "pagerduty":
                        field = self.pagerduty
                        key = "service_name"
                    else:
                        raise Exception("Notification type {t} is not"
                                        "supported!".format(t=typ))
                    type_template = deepcopy(self.notification_types[typ])
                    for hook in field:
                            if hook[key] == lookup:
                                result = hook
                                break
                    type_template['notification_value'] = result['id']
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
        log.debug(self.pretty_print_json(pol_template))

        r = self.session.post(CREATE_POLICY_URL,
                              json=pol_template,
                              headers=headers)
        r.raise_for_status()
        log.info("Created policy {p} for group {g}"
                 .format(p=pol_template['name'],
                         g=self.get_group_name_by_id(group_id)))
        if update_cache:
            self.update_cache()
        return r
