#!/usr/bin/python
# -*- coding: utf8 -*-
#
# Test and apply stackdriver alert policies to groups of servers
# See README.md for further info
#
import requests
import json
import logging
import os
from copy import deepcopy
from tyr.policies.stackdriver import conditions
from tyr.policies.stackdriver import notification_types
from tyr.policies.stackdriver import notification_groups

API_ENDPOINT = 'https://api.stackdriver.com/'
API_KEY = os.environ['STACKDRIVER_API_KEY']
USERNAME = os.environ['STACKDRIVER_USERNAME']
PASSWORD = os.environ['STACKDRIVER_PASSWORD']

# log = logging.getLogger('tyr.alerts.StackDriver')
# if not log.handlers:
#     log.setLevel(logging.INFO)
#     ch = logging.StreamHandler()
#     ch.setLevel(logging.INFO)
#     formatter = logging.Formatter(
#         '%(asctime)s [%(name)s] %(levelname)s: %(message)s',
#         datefmt='%H:%M:%S')
#     ch.setFormatter(formatter)
#     log.addHandler(ch)

LIST_POLICY_URL = "/v0.2/alerting/policies/"
LIST_GROUPS_URL = "/v0.2/groups/"
GET_POLICY_URL = "/v0.2/alerting/policies/{policy_id}/"
GET_GROUP_URL = "/v0.2/groups/{group_id}/"
CREATE_GROUP_URL = "/v0.2/groups/"
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
        self.log = logging.getLogger('tyr.alerts.StackDriver')
        self.log.setLevel(logging.DEBUG)
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

    def get_policy_list(self):
        return self.get_paginated_list(LIST_POLICY_URL)

    def pretty(self, obj):
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

    def create_group(self, name, parent_id=None, conditions=[], conjunction="AND", is_cluster=False):
        data = {
            "name": name,
            "parent_id": None,
            "cluster": is_cluster,
            "conjunction": conjunction,
            "conditions": conditions
        }

        if parent_id:
            data['parent_id'] = parent_id

        log.debug(data)

        r = requests.post(API_ENDPOINT + CREATE_GROUP_URL,
                         headers=self.headers, json=data)
        r.raise_for_status()
        self.update_cache()
        return r.json()['data']['id']


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

    def get_group_id_by_name(self, name=None, create_if_missing=False, contains_name=None):
        """
        :param name:
        :param create_if_missing:
        :param contains_name:
        :return id:
        Returns group id from a name specifier.  Subgroups can use a / seperator.
        Can also create a group if it does not exist.
        """
        if not name:
            raise Exception("Must specify group name!")
        if create_if_missing and not contains_name:
            raise Exception("Must specify a membership regex to be able to create a group.")

        parent_id = None
        child_id = None
        if '/' in name:
            # Group is a subgroup
            parent = name.split('/')[0]
            child = name.split('/')[1]
            has_parent = True
        else:
            has_parent = False

        if has_parent:
            # We are searching for a child group
            for group in self.groups:
                # Find the top level parent group
                if group['name'] == parent and not group['parent_id']:
                    parent_id = group['id']
            for group in self.groups:
                if group['name'] == child and group['parent_id'] == parent_id and parent_id:
                    child_id = group['id']
                    self.log.debug('Retrieved child group {c} for {g} & parent {p}'
                              .format(p=parent_id, c=child_id, g=name))
                    return child_id
        else:
            # A top level group was specified
            for group in self.groups:
                # If group is not a subgroup, we should ignore them
                if group['name'] == name and not group['parent_id']:
                    parent_id = group['id']
                    self.log.debug('Retrieved group {id} for parent {group}'
                              .format(id=group['id'], group=name))
                    return parent_id

        # If we get here, the group has not been found
        if create_if_missing and not parent_id:
            use_conditions = [{"comparison": "contains", "type": "name", "value": contains_name}]
            if not has_parent:
                parent_id = self.create_group(name=name, parent_id=None, conditions=use_conditions)
                return parent_id
            else:
                parent_id = self.create_group(name=parent, parent_id=None, conditions=use_conditions)

        if create_if_missing and not child_id:
            use_conditions = [{"comparison": "contains", "type": "name", "value": contains_name}]
            child_id = self.create_group(name=child, parent_id=parent_id, conditions=use_conditions)
            return child_id

        raise Exception("Group {g} was not found! (specify create_if_missing to create)".format(g=name))

    def get_group_name_by_id(self, id):
        for group in self.groups:
            if group['id'] == id:
                self.log.debug('Retrieved group {name} for {id}'
                          .format(id=group['id'], name=group['name']))
                return group['name']

    def get_group_by_id(self, id):
        r = requests.get(API_ENDPOINT + GET_GROUP_URL.format(group_id=id),
                         headers=self.headers)
        r.raise_for_status()
        group = r.json()['data']
        self.log.debug('Retrieved group {group} for {id}'
                  .format(id=group['id'], group=group['name']))
        return group

    def get_policies_applied_to_group_id(self, group_id):
        '''
        Get a list of policies applied to a group id
        '''
        pol_list = []
        for c in self.policies['data']:
            if c['condition']:
                if c['condition']['children']:
                    for e in c['condition']['children']:
                        try:
                            if e:
                                if e['options']:
                                    if 'group' in e['options']['applies_to']:
                                        if e['options']['group_id'] == group_id:
                                            pol_list.append(e)
                        except KeyError:
                            pass
                        except TypeError:
                            print(e)
                            print(c['condition']['children'])
        return pol_list

    def test_condition_applied_to_group_id(self, policy, group,
                                           ignore_options=['window']):
        '''
        Test a policy condition is applied to a given group name
        If ignore_window is specified, the condition will be matched
        if everything but the time window match.  You can override
        the ignore_options argument to add other options to be
        ignored, such as threshold.
        '''
        pols = self.get_policies_applied_to_group_id(group['id'])
        self.log.debug('{n} policies applied to group id: {g}'
                  .format(n=len(pols), g=group['id']))
        for pol in pols:
            try:
                if self.condition_subset_in_superset(
                        policy,
                        pol,
                        ignore_options=ignore_options
                ):
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

    def test_specific_conditions(self, specified_group,
                                 ignore_options=['window']):
        '''
        Test whether a policy condition is applied everywhere it should be
        for a given search group.  Will accept subgroups via a */subgroup
        identifier.  Uses the stackdriver policies list
        Can override ignore_options if you want to consider time window
        or override additional options like threshold.
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
                if not group['parent_id']:
                    gn = group['name']
                else:
                    gn = ("{p}/{c}".format(
                          p=self.get_group_name_by_id(group['parent_id']),
                          c=group['name']))
                if self.test_condition_applied_to_group_id(
                        pol,
                        group,
                        ignore_options=ignore_options
                        ):
                            self.log.info("OK: Policy {n} present in group {gn} ({g})"
                                     .format(n=name, gn=gn,
                                             g=group['id']))
                else:
                    self.log.info("WARN: Policy {n} NOT present in group {gn} ({g})"
                             .format(n=name, gn=gn, g=group['id']))
                    missing.append({"name": name, "condition": pol,
                                    "group_id": group['id'],
                                    "parent_group_name":
                                    self.get_group_name_by_id(
                                        group["parent_id"])})
        return missing

    def apply_missing_conditions(self, condition_group, notification_group,
                                 ignore_options=['window']):
        '''
        Automatically apply any missing conditions from a configured condition
        group and add apporpriate notifications
        Can override ignore_options if you want to consider time windows
        or ignore additional options like threshold.
        '''
        missing = self.test_specific_conditions(condition_group,
                                                ignore_options=ignore_options)
        for m in missing:
            self.create_policy_for_group(m['parent_group_name'] + '-' +
                                         self.get_group_name_by_id(m['group_id']),
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
            ("windows_cpu", "winagent:cpu"),
            ("windows_disk_usage", "winagent:disk"),
            ("windows_disk_usage", "winagent:disk:*"),
            ("memory", "agent:memory::memory:used:pct"),
            ("disk_usage", "agent:df:*:df_complex:used:pct"),
            ("disk_usage", "agent:df:*:used:pct"),
            ("cpu", "agent:aggregation:cpu-average:cpu:idle:pct"),
            ("windows_memory", "winagent:mem"),
            ("rabbitmq_consumers", "agent:rabbitmq:*:gauge:consumers:value"),
            ("rabbitmq_messages", "agent:rabbitmq:*:gauge:messages:value"),
            ("mongodb_total_ops_command",
             "agent:mongodb::total_operations:command:value"),
            ("mongodb_current_connections",
             "agent:mongodb::current_connections::value"),
            ("mongodb_lock_held",
             "agent:mongodb::total_time_in_ms:global_lock_held:value")
        ]
        remove_options = ['group_id', 'suggested_thresholds', 'useWildcards',
                          'customMetricMatches', 'condition_trigger',
                          'sub_resource', 'useUsername']
        if ignore_options:
            remove_options.extend(ignore_options)

        # Remove some newer fields to make comparison more accurate
        subset = deepcopy(subset_input)
        superset = deepcopy(superset_input)
        self.log.debug(subset)
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
                    self.log.debug('Removing {opt} as it is not in superset'
                              .format(opt=opt))
                    subset['options'].pop(opt)

        # Get some metric name to compare with equivilents
        if 'metric_name' in subset["options"]:
            name_tuple = (subset["options"]["metric_name"],
                          superset["options"]["metric_name"])
            if name_tuple in metric_name_equivilents:
                self.log.debug('Removing metric name '
                          'as they are equivilent.')
                subset['options'].pop('metric_name')

        if 'metric_type' in subset["options"]:
            type_tuple = (subset['options']["metric_type"],
                          superset['options']['metric_type'])
            if type_tuple in metric_name_equivilents:
                self.log.debug('Removing metric type '
                          'as they are equivilent.')
                subset['options'].pop('metric_type')

        match = True
        if not subset['condition_type'] == superset['condition_type']:
            self.log.debug("{o} not equal to {p}"
                      .format(o=subset['condition_type'],
                              p=superset['condition_type']))
            match = False

        if match:
            for key, o in subset['options'].iteritems():
                p = None
                q = None
                self.log.debug("Testing key: " + key)
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
                        self.log.debug("{p} not equal to {q}"
                                  .format(p=p, q=q))
                        break
                    else:
                        self.log.debug("{p} IS equal to {q}"
                                  .format(p=p, q=q))
                except KeyError:
                    match = False
                    break
        self.log.debug(match)
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
        self.log.debug(r.cookies)

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
            copy['name'] = ('{gn} Tyr: {typ}'
                            .format(typ=type_desc,
                                    gn=name))
            conditions_template.append(copy)
        if len(conditions) == 1:
            policy_name = copy['name']
        else:
            policy_name = "{g} Tyr: multiple conditions".format(g=name)

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
                            result = None
                            if hook[key] == lookup:
                                result = hook
                                break
                    if not result:
                        raise Exception(("Config was not found for {typ}/{h}")
                                        .format(typ=typ, h=lookup))
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
            "name": policy_name,
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
        self.log.debug(self.pretty(pol_template))

        r = self.session.post(CREATE_POLICY_URL,
                              json=pol_template,
                              headers=headers)
        r.raise_for_status()
        self.log.info("Created policy {p} for group {g}"
                 .format(p=pol_template['name'],
                         g=self.get_group_name_by_id(group_id)))
        if update_cache:
            self.update_cache()
        return r
