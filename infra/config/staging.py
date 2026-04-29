"""Staging environment configuration.

Smaller RDS, shorter backup retention, looser alarm thresholds. The intent is
that staging is a thin slice of production sized for low-cost dry-runs and
Playwright smoke tests, not for production-grade workloads.
"""

from __future__ import annotations

CONFIG = {
    "env_name": "staging",
    "stack_prefix": "FmeTrainStg",
    "tags": {
        "Project": "fme-training-automation",
        "Environment": "staging",
        "ManagedBy": "cdk",
    },
    # AWS region: matches the existing safeskilljar S3 bucket per plan section D.
    "aws_region": "us-west-2",
    # Network --------------------------------------------------------------
    "vpc_cidr": "10.40.0.0/20",
    "az_count": 2,
    # Single NAT gateway is enough for staging (low traffic, cost-conscious).
    "nat_gateways": 1,
    # Database -------------------------------------------------------------
    "rds_instance_class": "t4g.micro",
    "rds_allocated_storage_gb": 20,
    "rds_max_allocated_storage_gb": 50,
    "rds_backup_retention_days": 1,
    "rds_multi_az": False,
    "rds_deletion_protection": False,
    # Storage --------------------------------------------------------------
    # `cache/*` lifecycle: archive to Glacier Deep Archive after 365 days
    # of no access (plan section 4 - retention).
    "s3_cache_glacier_after_days": 365,
    # Drafts retention: keep forever (audit), but transition non-current
    # versions to IA after 30 days to keep costs down.
    "s3_drafts_versioned": True,
    # Compute --------------------------------------------------------------
    "app_runner_cpu": "0.5 vCPU",
    "app_runner_memory": "1 GB",
    "app_runner_min_size": 1,
    "app_runner_max_size": 2,
    "fargate_cpu": 1024,           # 1 vCPU
    "fargate_memory_mib": 2048,    # 2 GiB
    # Wall-clock guard for Fargate worker tasks (plan section 6).
    "fargate_task_max_minutes": 60,
    # Cost ceiling per run, surfaced via SSM parameter and read by worker
    # (plan section 3 - cost ceiling).
    "max_run_usd": 50,
    # Observability --------------------------------------------------------
    "log_retention_days": 30,
    # Alarm thresholds: looser than prod since failures here aren't customer-
    # impacting.
    "alarm_app_runner_5xx_threshold_per_5min": 10,
    "alarm_fargate_failed_tasks_threshold_per_15min": 3,
    "alarm_rds_cpu_threshold_pct": 90,
    "alarm_rds_free_storage_threshold_gb": 5,
    # AWS Budget alarm — keep below the prod budget so we notice runaway
    # staging usage early.
    "monthly_budget_usd": 75,
    # Secrets --------------------------------------------------------------
    # IT populates these *manually* in Secrets Manager (one-time setup or
    # rotation). The CDK code only references them by ARN; it never writes
    # values. See infra/README.md for the runbook.
    #
    # The list below is the contract — the CDK validates that every name
    # has an ARN-shaped value resolvable via context (or from the SSM
    # Parameter Store fallback at /fme-train/<env>/secrets/<name>/arn).
    "secret_names": [
        "openai-api-key",
        "jira-api-token",
        "skilljar-api-key",
        "google-oauth-client-secret",
        "session-signing-key",
        "rds-master-credentials",
    ],
    # Skilljar embedding -------------------------------------------------
    "cloudfront_price_class": "PRICE_CLASS_100",  # NA + EU only is fine
}
