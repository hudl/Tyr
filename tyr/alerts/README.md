# Examples

Here a few examples on how to use the stackdriver alerts module.

```
export STACKDRIVER_API_KEY=xxx
export STACKDRIVER_USERNAME=xxx
export STACKDRIVER_PASSWORD=xxx
python
from tyr.alerts.stackdriver import StackDriver
s = StackDriver() # This connects and caches a lot of the configuration

# Test a group against it's configuration profile in ../policies/stackdriver.py
c = s.test_specific_conditions("p-push/mongo")
len(c) # How many are missing?

# Exclude a threshold value from the comparison (window is excluded by default)
c = s.test_specific_conditions("p-push/mongo", ignore_options=['threshold','window'])

# Apply any missing alert policies, ignoring threshold and window in the comparison
c = s.apply_missing_conditions("p-push/mongo", "hudl-push" # This is the notification group, ignore_options=['threshold','window'])


# Directly create a policy on a group with a python dict (representing JSON from stackdriver interface):
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


# Generate a CSV for loading into a spreadsheet
s.create_csv_of_all_groups(filename='/Users/chris.gilbert/output.csv')
```



