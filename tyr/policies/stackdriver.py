conditions = {
    "disk_gt_70pct_10m":  {
        "groups": ["all prod web", "p-mongo-all", "p-rabbit", "p-solr", "p-sql"],
        "condition_type": "threshold",
        "options": {
            "comparison": "above",
            "metric_name": "agent:df:*:used:pct",
            "metric_type": "disk_usage",
            "resource_type": "Instance",
            "threshold": 0.7,
            "window": 600
        }
    },

    "general_mem_gt_something": {
        "groups": ["web", "p-mongo", "p-rabbit", "p-solr", "p-sql"],
        "condition_type": "threshold",
        "options": {
            "comparison": "above",
            "metric_type": "memory",
            "resource_type": "Instance"
        }
    },

    "general_disk_gt_something":  {
        "groups": ["web", "p-mongo", "p-rabbit", "p-solr", "p-sql"],
        "condition_type": "threshold",
        "options": {
            "comparison": "above",
            "metric_type": "disk_usage",
            "resource_type": "Instance"
        }
    },

    "general_cpu_gt_something":  {
        "groups": ["p-web", "p-mongo", "p-rabbit", "p-solr", "p-sql", "web"],
        "condition_type": "threshold",
        "options": {
            "comparison": "above",
            "metric_type": "cpu",
            "resource_type": "Instance"
        }
    },

    "general_cpu_gt_80pct_5m":  {
        "groups": ["p-queues-jobs"],
        "condition_type": "threshold",
        "options": {
            "comparison": "above",
            "metric_name": "agent:aggregation:cpu-average:cpu:used:pct",
            "metric_type": "cpu",
            "resource_type": "Instance",
            "threshold": 0.9,
            "threshold_unit": "percent",
            "window": 300
        }
    },

    "web_cpu_gt_95pct_15m":  {
        "groups": ["all prod web"],
        "condition_type": "threshold",
        "options": {
            "comparison": "above",
            "metric_name": "agent:aggregation:cpu-average:cpu:used:pct",
            "metric_type": "memory",
            "resource_type": "Instance",
            "threshold": 0.25,
            "threshold_unit": "percent",
            "window": 900
        }
    },

    "web_cloudwatch_cpu_gt_90pct_5m":  {
        "groups": ["p-web", "p-mongo", "p-rabbit", "p-solr", "p-sql", "web"],
        "condition_type": "threshold",
        "options": {
            "comparison": "above",
            "metric_type": "cloudwatch_cpu",
            "resource_type": "Instance"
        }
    },

    "web_cpu_gt_90pct_5m":  {
        "condition_type": "threshold",
        "groups": ["web"],
        "options": {
            "comparison": "above",
            "metric_name": "winagent:cpu",
            "metric_type": "windows_cpu",
            "resource_type": "Instance",
            "threshold": 90,
            "threshold_unit": "percent",
            "window": 300
        }
    },

    "web_not_registered_with_eureka":  {
        "condition_type": "threshold",
        "groups": ["web"],
        "options": {
            "comparison": "below",
            "metric_name": "custom:Registered with Eureka",
            "metric_type": "custom:Registered with Eureka",
            "resource_type": "Instance",
            "threshold": 1,
            "threshold_unit": "custom"
        }
    },

    "postfix_mem_gt_90pct_5m":  {
        "condition_type": "threshold",
        "groups": ["p-postfix"],
        "options": {
            "comparison": "above",
            "metric_name": "agent:memory::memory:used:pct",
            "metric_type": "memory",
            "resource_type": "Instance",
            "threshold": 0.9,
            "threshold_unit": "percent",
            "window": 300
        }
    },

    "rabbit_process_running":  {
        "groups": ["p-rabbit"],
        "condition_type": "process_health",
        "options": {
            "comparison": "below",
            "condition_trigger": "any",
            "process": "/usr/sbin/rabbitmq-server",
            "resource_type": "Instance",
            "threshold": 1,
            "user": None,
            "window": 300
        }
    },

    "mongo_process_running":  {
        "groups": ["p-mongo", "p-mongo-all"],
        "condition_type": "process_health",
        "options": {
            "comparison": "below",
            "condition_trigger": "any",
            "process": "/usr/bin/mongod",
            "resource_type": "Instance",
            "threshold": 1,
            "user": None,
            "window": 300
        }
    },

    "nginx_process_running":  {
        "condition_type": "process_health",
        "groups": ["p-nginx"],
        "options": {
            "comparison": "below",
            "condition_trigger": "any",
            "process": "nginx: master process",
            "resource_type": "Instance",
            "threshold": 1,
            "user": None,
            "window": 300
        }
    },

    "solr_process_running":  {
        "condition_type": "process_health",
        "groups": ["p-solr"],
        "options": {
            "comparison": "below",
            "condition_trigger": "any",
            "process": "sudo java -Deureka.name=SOLR",
            "resource_type": "Instance",
            "threshold": 1,
            "user": None,
            "window": 300
        }
    },

    "rds_cpu_gt_80pct_5m":  {
        "condition_type": "threshold",
        "instances": ["p-quartz-vpc"],
        "options": {
            "applies_to": "single",
            "comparison": "above",
            "metric_name": "CPUUtilization",
            "metric_type": "cpu_utilization",
            "resource_id": "p-quartz-vpc-3355",
            "resource_type": "DatabaseInstance",
            "threshold": 80,
            "threshold_unit": "percent",
            "window": 300
        }
    },

    "rds_disk_gt_80pct_5m": {
        "condition_type": "threshold",
        "instances": ["p-quartz-vpc"],
        "options": {
            "applies_to": "single",
            "comparison": "above",
            "metric_name": "AverageDiskUsage",
            "metric_type": "average_disk_usage",
            "resource_id": "p-quartz-vpc-3355",
            "resource_type": "DatabaseInstance",
            "threshold": 0.8,
            "threshold_unit": "percent",
            "window": 300
        }
    }
}


notifications = {

    "heimdall":  {
        "notification_type": "static_webhook",
        "notify_on": "all",
        "static_webhook": 65,
        "status": "active"
    },
    "pagerduty": {
        "notification_type": "pagerduty",
        "notify_on": "all",
        "resource": "/v0.2/settings/channels/pagerduty/183/",
        "status": "active"
    },
    "general_1": {
        "notification_type": "static_webhook",
        "notification_value": 5
    },
    "general_2": {
        "notification_type": "pagerduty",
        "notification_value": 49
    }
}
