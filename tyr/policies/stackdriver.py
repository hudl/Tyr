conditions = {
    # These are template polcicies which form the conditions part
    # of the JSON documented submitted to stackdriver.
    # Sicne this does not use a supported API, they may need
    # tweaking if/when extra fields are added or changed in
    # their webapp.
    #
    # */web indicates all servers in a /web subgroup.  You can also
    # specify something specific, like p-assistedbreakdown/web
    "*/web": [
        {
            "condition_type": "threshold",
            "name": "Tyr_applied_condition windows_disk_usage above 75",
            "options": {
                "resource_type": "instance",
                "applies_to": "group",
                "metric_name": "windows_disk_usage",
                "useWildcards": False,
                "comparison": "above",
                "window": 300,
                "customMetricMatches": [],
                "metric_type": "windows_disk_usage",
                "condition_trigger": "any",
                "metric_key": "instance.cpu.usage_percent",
                "threshold_unit": "percent",
                "suggested_thresholds": {
                    "upper": 55,
                    "lower": 50
                },
                "threshold": 75,
                "sub_resource": "*"
            },
        },
        {
            "condition_type": "threshold",
            "name": "Tyr_applied_condition windows_cpu_usage above 0.9",
            "options": {
                "resource_type": "instance",
                "applies_to": "group",
                "metric_name": "windows_cpu",
                "useWildcards": False,
                "comparison": "above",
                "window": 300,
                "customMetricMatches": [],
                "metric_type": "windows_cpu",
                "condition_trigger": "any",
                "metric_key": "instance.cpu.usage_percent",
                "threshold_unit": "percent",
                "suggested_thresholds": {
                    "upper": 6,
                    "lower": 0.9500000000000001
                },
                "threshold": 90
            }
        },
        {
            "condition_type": "threshold",
            "name": "Tyr_applied_condition windows_memory above 0.75",
            "options": {
                "resource_type": "instance",
                "applies_to": "group",
                "group_id": 17722,
                "metric_name": "windows_memory",
                "useWildcards": False,
                "comparison": "above",
                "window": 300,
                "customMetricMatches": [],
                "metric_type": "windows_memory",
                "condition_trigger": "any",
                "metric_key": "instance.cpu.usage_percent",
                "threshold_unit": "percent",
                "suggested_thresholds": {
                    "upper": 45,
                    "lower": 35
                },
                "threshold": 75
            },
        },
        {
            "name": "Tyr_applied_condition not registered in eureka",
            "condition_type": "threshold",
            "options": {
                "threshold_unit": "custom",
                "comparison": "below",
                "condition_trigger": "any",
                "metric_name": "custom:Registered with Eureka",
                "suggested_thresholds": {},
                "window": 300,
                "applies_to": "group",
                "customMetricMatches": [],
                "metric_type": "custom:Registered with Eureka",
                "metric_key": "instance.cpu.usage_percent",
                "useWildcards": False,
                "threshold": 1,
                "resource_type": "instance"
            }
        }
    ],

    "*/mongo": [
        {
            "options": {
                "resource_type": "instance",
                "applies_to": "group",
                "threshold": 1,
                "comparison": "below",
                "useUsername": False,
                "user": "",
                "window": 300,
                "condition_trigger": "any",
                "process": "mongod"
            },
            "condition_type": "process_health",
            "name": "Tyr_applied_condition for mongod process running"
        },
        {
            "condition_type": "threshold",
            "name": "Tyr_applied_condition disk_usage above 0.75",
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
                "threshold": 0.75
            }
        },
        {
            "condition_type": "threshold",
            "name": "Tyr_applied_condition cpu_usage above 0.8",
            "options": {
                "resource_type": "instance",
                "applies_to": "group",
                "metric_name": "cpu",
                "useWildcards": False,
                "comparison": "above",
                "window": 300,
                "customMetricMatches": [],
                "metric_type": "cpu",
                "condition_trigger": "any",
                "metric_key": "instance.cpu.usage_percent",
                "threshold_unit": "percent",
                "suggested_thresholds": {
                    "upper": 0.25,
                    "lower": 0.35000000000000003
                },
                "threshold": 0.8
            }
        },
        {
            "condition_type": "threshold",
            "name": "Tyr_applied_condition memory_usage above 0.8",
            "options": {
                "resource_type": "instance",
                "applies_to": "group",
                "metric_name": "memory",
                "useWildcards": False,
                "comparison": "above",
                "window": 300,
                "customMetricMatches": [],
                "metric_type": "memory",
                "condition_trigger": "any",
                "metric_key": "instance.cpu.usage_percent",
                "threshold_unit": "percent",
                "suggested_thresholds": {
                    "upper": 15,
                    "lower": 10
                },
                "threshold": 0.8
            }
        }
    ]
}

notification_groups = {

    # These contain the names of the various hooks in stackdriver, so need
    # to match the exact String given in there.  See StackDriver.webhooks,
    # StackDriver.pagerduty and StackDriver.email instance vars for the data
    # retrieved from stackdriver which is matched up with.
    "hudl-assistedbreakdown": {
        "heimdall_webhook": "Heimdall hudl-assistedbreakdown Webhook",
        "pagerduty":  "",
        "team_email": ""
    },

    "hudl-assistedbreakdown": {
        "heimdall_webhook": "hudl-assistedbreakdown",
        "pagerduty":  "hudl-assistedbreakdown",
        "team_email": "Infrastructure Squad"
    },

    "test": {
        "team_email": "Infrastructure Squad"
    },


    "test": {
        "heimdall_webhook": "Heimdall Test Webhook",
        "pagerduty": "StackDriver Firedrill"
    },
    "hudl-recruit": {
        "heimdall_webhook": "Heimdall hudl-recruit Webhook",
        "pagerduty": "Stackdriver Team Sports"
    },
    "hudl-leroy": {
        "heimdall_webhook": "Heimdall hudl-leroy Webhook",
        "pagerduty": "Stackdriver Team Sports"
    },
    "hudl-maxpreps": {
        "heimdall_webhook": "Heimdall hudl-maxpreps Webhook",
        "pagerduty": "Stackdriver Community"
    },
    "hudl-statistics": {
        "heimdall_webhook": "Heimdall hudl-statistics Webhook",
        "pagerduty": "Stackdriver Community"
    },
    "hudl-teams": {
        "heimdall_webhook": "Heimdall hudl-teams Webhook",
        "pagerduty": "Stackdriver Team Sports"
    },
    "hudl-push": {
        "heimdall_webhook": "Heimdall hudl-push Webhook",
        "pagerduty": "Stackdriver Team Sports"
    },
    "hudl-getpaid": {
        "heimdall_webhook": "Heimdall hudl-getpaid Webhook",
        "pagerduty": "Stackdriver Team Sports"
    },
    "monolith": {
        "heimdall_webhook": "Heimdall Monolith Webhook",
        "pagerduty": "Stackdriver Monolith"
    },
    "hudl-exchanges": {
        "heimdall_webhook": "Heimdall hudl-exchanges Webhook",
        "pagerduty": "Stackdriver Community"
    },
    "hudl-platform": {
        "heimdall_webhook": "Heimdall hudl-platform Webhook",
    },
    "hudl-coresearch": {
        "heimdall_webhook": "Heimdall hudl-coresearch Webhook",
    },
    "test_jamie": {
        "heimdall_webhook": "Heimdall Test - Jamie",
    },
    "hudl-recommendations": {
        "heimdall_webhook": "Heimdall hudl-recommendations Webhook",
        "pagerduty": "Stackdriver Community"
    },
    "hudl-profiles": {
        "heimdall_webhook": "Heimdall hudl-profiles Webhook",
        "pagerduty": "Stackdriver Community"
    },
    "hudl-feed": {
        "heimdall_webhook": "Heimdall hudl-feed Webhook",
        "pagerduty": "Stackdriver Community"
    },
    "hudl-performancecapture": {
        "heimdall_webhook": "Heimdall hudl-performancecapture Webhook",
        "pagerduty": "Stackdriver Community"
    },
    "hudl-performancecenter": {
        "heimdall_webhook": "Heimdall hudl-performancecenter Webhook",
        "pagerduty": "Stackdriver Community"
    },
    "hudl-kickoff": {
        "heimdall_webhook": "Heimdall hudl-kickoff Webhook",
        "pagerduty": "Stackdriver Monolith"
    },
    "hudl-computervision": {
        "heimdall_webhook": "Heimdall hudl-computervision Webhook",
        "pagerduty": "StackDriver Monolith"
    },
    "hudl-features": {
        "heimdall_webhook": "Heimdall hudl-features Webhook",
        "pagerduty": "Stackdriver Monolith"
    },
    "hudl-highlights": {
        "heimdall_webhook": "Heimdall hudl-highlights Webhook",
        "pagerduty": "Stackdriver Community"
    },
    "hudl-users": {
        "heimdall_webhook": "Heimdall hudl-users Webhook",
        "pagerduty": "Stackdriver Monolith"
    },
    "hudl-assistedbreakdown": {
        "heimdall_webhook": "Heimdall hudl-assistedbreakdown Webhook",
        "pagerduty": "Stackdriver Team Sports"
    },
    "hudl-presentations": {
        "heimdall_webhook": "Heimdall hudl-presentations Webhook",
        "pagerduty": "Stackdriver Team Sports"
    },
    "hudl-usercontact": {
        "heimdall_webhook": "Heimdall hudl-usercontact Webhook",
        "pagerduty": "Stackdriver PagerDuty - Hemdall"
    },
    "hudl-videoediting": {
        "heimdall_webhook": "Heimdall hudl-videoediting Webhook",
        "pagerduty": "Stackdriver Team Sports"
    },
    "hudl-gulltop": {
        "heimdall_webhook": "Heimdall hudl-gulltop Webhook",
        "pagerduty": "Stackdriver PagerDuty - Hemdall"
    },
    "hudl-fbplaycardsearch": {
        "heimdall_webhook": "Heimdall hudl-fbplaycardsearch Webhook",
        "pagerduty": "Stackdriver Team Sports"
    },
    "hudl-recruitsearch": {
        "heimdall_webhook": "Heimdall hudl-recruitsearch Webhook",
        "pagerduty": "Stackdriver Team Sports"
    },
    "community": {
        "heimdall_webhook": "Heimdall - Community",
        "pagerduty": "StackDriver Community"
    },
    "teamsports": {
        "heimdall_webhook": "Heimdall - TeamSports",
        "pagerduty": "Stackdriver Team Sports"
    },
    "foundation": {
        "heimdall_webhook": "Heimdall - Foundation",
        "pagerduty": "StackDriver Foundation"
    },
    "individual_sports": {
        "heimdall_webhook": "Heimdall - Individual Sports",
        "pagerduty": "?"
    },
    "hudl-staticdata": {
        "heimdall_webhook": "Heimdall hudl-staticdata Webhook",
    },
    "hudl-videoanalytics": {
        "heimdall_webhook": "Heimdall hudl-videoanalytics Webhook",
        "pagerduty": "Stackdriver Team Sports",
        "team_email": "Infrastructure Squad"
    },

}

notification_types = {
    # these are the templates used in the JSON document
    # when creating new policies in stackdriver

    "team_email": {
        "notification_type": "team",
        "notification_value": None,
        "notification_options": {
            "primary_notification": "email"
        }
    },

    "heimdall_webhook": {
        "notification_type": "static_webhook",
        "notify_on": "all",
        "static_webhook": None,
        "status": "active"
    },

    "pagerduty": {
        "notification_type": "pagerduty",
        "notification_value": None
    }
}
