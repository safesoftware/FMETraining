"""Production environment configuration.

Larger RDS instance, 7-day backup retention, tighter alarm thresholds, and a
$150/month budget alarm per plan section 6.

Note: per the plan we keep ``rds_multi_az = False`` for v1 — multi-AZ doubles
the RDS bill and the team is 2-5 users, so the cost is hard to justify until
we have evidence of business impact from a single-AZ outage.
"""

from __future__ import annotations

CONFIG = {
    "env_name": "production",
    "stack_prefix": "FmeTrainProd",
    "tags": {
        "Project": "fme-training-automation",
        "Environment": "production",
        "ManagedBy": "cdk",
    },
    "aws_region": "us-west-2",
    # Network --------------------------------------------------------------
    "vpc_cidr": "10.50.0.0/20",
    "az_count": 2,
    # Single NAT here too — 2-5 users will not saturate it, and the second
    # NAT would add ~$32/mo for negligible availability gain.
    "nat_gateways": 1,
    # Database -------------------------------------------------------------
    "rds_instance_class": "t4g.small",
    "rds_allocated_storage_gb": 50,
    "rds_max_allocated_storage_gb": 200,
    "rds_backup_retention_days": 7,
    "rds_multi_az": False,
    "rds_deletion_protection": True,
    # Storage --------------------------------------------------------------
    "s3_cache_glacier_after_days": 365,
    "s3_drafts_versioned": True,
    # Compute --------------------------------------------------------------
    "app_runner_cpu": "1 vCPU",
    "app_runner_memory": "2 GB",
    "app_runner_min_size": 1,
    "app_runner_max_size": 3,
    "fargate_cpu": 2048,           # 2 vCPU for prod runs
    "fargate_memory_mib": 4096,    # 4 GiB
    "fargate_task_max_minutes": 60,
    "max_run_usd": 50,
    # Observability --------------------------------------------------------
    "log_retention_days": 90,
    # Tighter prod thresholds.
    "alarm_app_runner_5xx_threshold_per_5min": 3,
    "alarm_fargate_failed_tasks_threshold_per_15min": 1,
    "alarm_rds_cpu_threshold_pct": 80,
    "alarm_rds_free_storage_threshold_gb": 10,
    "monthly_budget_usd": 150,
    # Secrets --------------------------------------------------------------
    "secret_names": [
        "openai-api-key",
        "jira-api-token",
        "skilljar-api-key",
        "google-oauth-client-secret",
        "session-signing-key",
        "rds-master-credentials",
    ],
    # Skilljar embedding -------------------------------------------------
    "cloudfront_price_class": "PRICE_CLASS_100",
}
