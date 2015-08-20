# Examples

Here a few examples on how to use the stackdriver alerts module.


# Connecting

```
export STACKDRIVER_API_KEY=xxx
export STACKDRIVER_USERNAME=xxx
export STACKDRIVER_PASSWORD=xxx
python
from tyr.alerts.stackdriver import StackDriver
s = StackDriver() # This connects and caches a lot of the configuration
```


# What alerts are applied right now?
Get a list of conditions which are actually applied to a group presently
```
s.get_policies_applied_to_group_id(s.get_group_id_by_name('p-teams/web'))
```
Get a list of policies which should be applied for a group name according to configuration and pretty print them
```
s.pretty(s.get_defined_group_policies('p-teams/web'))
```

Test a group against it's configuration profile in ../policies/stackdriver.py
```
c = s.test_specific_conditions("p-push/mongo")
len(c) # How many are missing?
```
Exclude a threshold value from the comparison (window is excluded by default)
```
c = s.test_specific_conditions("p-highlights/web", ignore_options=['threshold','window'])
```

Generate a CSV for loading into a spreadsheet
```
s.create_csv_of_all_groups(filename='/Users/chris.gilbert/output.csv')
```


# Adding new alert policies

To create new alerts, you should have a policy list, which is attached to a group name.

These are located in tyr/policies/stackdriver.py

There are several python dictionaries there - the one you need to add to is called `conditions`.

- conditions:
  - group
    - condition []

These are the stackdriver conditions which should be applied to a group - e.g. disk usage > 0.75.  Each of them is a python dictionary representing the JSON object submitted to stackdriver to create a new policy for that condition.  In order to get new conditions to add, the easiest way is either to copy and paste an existing one, and change it as necessary, or to record the actual JSON payload submitted in Chrome.

To do this:

1. Go to a group in stackdriver, and click `Policies` then `Add New Policy`.
2. Start creating the policy through the interface, by adding conditions.  There's no need to add notifications.  Give it a name to make it easy to find afterwards.
3. Add your conditions to apply to groups (not a single instance)
4. Before you click Save Policy, open Chrome developer tools with `Ctrl(or Cmd)+Alt+I`
5. Choose the `Network` tab
5. Tick `preserve log`, make sure the record button is turned on (red) and then click the `Save Policy` button in the stackdriver interface
6. After a few seconds, turn the record button off, and find the request named `policy` right at the top.  You will only see this if you remembered to click 'preserve log'.
7. Choose the policy entry, and then on the `headers` tab, scroll to the bottom.
8. Click to view the RAW request payload.
9. The items below the children[] are those that need to be added to your stackdriver.py set.
10. Add conditions as necessary, and delete the group_id fields from them.

- 


# Creating Missing Alerts

 Apply any missing alert policies, ignoring threshold and window in the comparison
```
c = s.apply_missing_conditions("p-push/mongo", "hudl-push" # This is the notification group, ignore_options=['threshold','window'])
```

Directly create a policy on a group with a python dict (representing JSON from stackdriver interface):
```
conditions = [{
    "condition_type": "threshold",
    "name": "Tyr_applied_condition disk_usage above 0.7 for p-queues",
    "existing": True,
    "options": {
      "resource_type": "instance",
      "applies_to": "group",
      "group_id": 1282,
      "metric_name": "disk_usage",
      "useWildcards": False,
      "comparison": "above",
      "window": 600,
      "customMetricMatches": [],
      "metric_type": "disk_usage",
      "condition_trigger": "any",
      "metric_key": "instance.disk_usage.usage_percent",
      "threshold_unit": "percent",
      "suggested_thresholds": {},
      "threshold": 0.7
    }
}]

r = s.create_policy_for_group("test policy chrisg", conditions, "p-queues/web")
```



