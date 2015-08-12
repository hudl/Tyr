# conditions = {
#     "disk_gt_70pct_10m":  {
#         "groups": ["all prod web", "p-mongo-all", "p-rabbit", "p-solr", "p-sql"],
#         "condition_type": "threshold",
#         "options": {
#             "comparison": "above",
#             "metric_name": "agent:df:*:used:pct",
#             "metric_type": "disk_usage",
#             "resource_type": "Instance",
#             "threshold": 0.7,
#             "window": 600
#         }
#     },

#     "general_mem_gt_something": {
#         "groups": ["web", "p-mongo", "p-rabbit", "p-solr", "p-sql"],
#         "condition_type": "threshold",
#         "options": {
#             "comparison": "above",
#             "metric_type": "memory",
#             "resource_type": "Instance"
#         }
#     },

#     "general_disk_gt_something":  {
#         "groups": ["p-mongo", "p-rabbit", "p-solr", "p-sql"],
#         "condition_type": "threshold",
#         "options": {
#             "comparison": "above",
#             "metric_type": "disk_usage",
#             "resource_type": "Instance"
#         }
#     },

#     "general_cpu_gt_something":  {
#         "groups": ["p-web", "p-mongo", "p-rabbit", "p-solr", "p-sql"],
#         "condition_type": "threshold",
#         "options": {
#             "comparison": "above",
#             "metric_type": "cpu",
#             "resource_type": "Instance"
#         }
#     },

#     "general_cpu_gt_80pct_5m":  {
#         "groups": ["p-queues-jobs"],
#         "condition_type": "threshold",
#         "options": {
#             "comparison": "above",
#             "metric_name": "agent:aggregation:cpu-average:cpu:used:pct",
#             "metric_type": "cpu",
#             "resource_type": "Instance",
#             "threshold": 0.9,
#             "threshold_unit": "percent",
#             "window": 300
#         }
#     },

#     "web_cpu_gt_95pct_15m":  {
#         "groups": ["all prod web"],
#         "condition_type": "threshold",
#         "options": {
#             "comparison": "above",
#             "metric_name": "agent:aggregation:cpu-average:cpu:used:pct",
#             "metric_type": "memory",
#             "resource_type": "Instance",
#             "threshold": 0.25,
#             "threshold_unit": "percent",
#             "window": 900
#         }
#     },

#     "web_cloudwatch_cpu_gt_90pct_5m":  {
#         "groups": ["p-web"],
#         "condition_type": "threshold",
#         "options": {
#             "comparison": "above",
#             "metric_type": "cloudwatch_cpu",
#             "resource_type": "Instance"
#         }
#     },

#     "web_cpu_gt_90pct_5m":  {
#         "condition_type": "threshold",
#         "groups": ["p-web"],
#         "options": {
#             "comparison": "above",
#             "metric_name": "winagent:cpu",
#             "metric_type": "windows_cpu",
#             "resource_type": "Instance",
#             "threshold": 90,
#             "threshold_unit": "percent",
#             "window": 300
#         }
#     },

#     "web_not_registered_with_eureka":  {
#         "condition_type": "threshold",
#         "groups": ["p-web"],
#         "options": {
#             "comparison": "below",
#             "metric_name": "custom:Registered with Eureka",
#             "metric_type": "custom:Registered with Eureka",
#             "resource_type": "Instance",
#             "threshold": 1,
#             "threshold_unit": "custom"
#         }
#     },

#     "postfix_mem_gt_90pct_5m":  {
#         "condition_type": "threshold",
#         "groups": ["p-postfix"],
#         "options": {
#             "comparison": "above",
#             "metric_name": "agent:memory::memory:used:pct",
#             "metric_type": "memory",
#             "resource_type": "Instance",
#             "threshold": 0.9,
#             "threshold_unit": "percent",
#             "window": 300
#         }
#     },

#     "rabbit_process_running":  {
#         "groups": ["p-rabbit"],
#         "condition_type": "process_health",
#         "options": {
#             "comparison": "below",
#             "condition_trigger": "any",
#             "process": "/usr/sbin/rabbitmq-server",
#             "resource_type": "Instance",
#             "threshold": 1,
#             "user": None,
#             "window": 300
#         }
#     },

#     "mongo_process_running":  {
#         "groups": ["p-mongo", "p-mongo-all"],
#         "condition_type": "process_health",
#         "options": {
#             "comparison": "below",
#             "condition_trigger": "any",
#             "process": "/usr/bin/mongod",
#             "resource_type": "Instance",
#             "threshold": 1,
#             "user": None,
#             "window": 300
#         }
#     },

#     "nginx_process_running":  {
#         "condition_type": "process_health",
#         "groups": ["p-nginx"],
#         "options": {
#             "comparison": "below",
#             "condition_trigger": "any",
#             "process": "nginx: master process",
#             "resource_type": "Instance",
#             "threshold": 1,
#             "user": None,
#             "window": 300
#         }
#     },

#     "solr_process_running":  {
#         "condition_type": "process_health",
#         "groups": ["p-solr"],
#         "options": {
#             "comparison": "below",
#             "condition_trigger": "any",
#             "process": "sudo java -Deureka.name=SOLR",
#             "resource_type": "Instance",
#             "threshold": 1,
#             "user": None,
#             "window": 300
#         }
#     },

#     "rds_cpu_gt_80pct_5m":  {
#         "condition_type": "threshold",
#         "instances": ["p-quartz-vpc"],
#         "options": {
#             "applies_to": "single",
#             "comparison": "above",
#             "metric_name": "CPUUtilization",
#             "metric_type": "cpu_utilization",
#             "resource_id": "p-quartz-vpc-3355",
#             "resource_type": "DatabaseInstance",
#             "threshold": 80,
#             "threshold_unit": "percent",
#             "window": 300
#         }
#     },

#     "rds_disk_gt_80pct_5m": {
#         "condition_type": "threshold",
#         "instances": ["p-quartz-vpc"],
#         "options": {
#             "applies_to": "single",
#             "comparison": "above",
#             "metric_name": "AverageDiskUsage",
#             "metric_type": "average_disk_usage",
#             "resource_id": "p-quartz-vpc-3355",
#             "resource_type": "DatabaseInstance",
#             "threshold": 0.8,
#             "threshold_unit": "percent",
#             "window": 300
#         }
#     }
# }

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
