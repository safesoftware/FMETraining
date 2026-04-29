#!/usr/bin/env python3
"""CDK app entrypoint — instantiates one full environment per ``cdk synth``.

Usage:
    cdk synth -c env=staging
    cdk synth -c env=production
    cdk diff  -c env=staging

If ``env`` is not provided we fall back to the value baked into
``cdk.json`` (currently ``staging``) so a bare ``cdk synth`` still works
during local development.

Environments are instantiated with stack names prefixed by
``config["stack_prefix"]`` (e.g. ``FmeTrainStgNetwork``). This prevents
accidental collision when both staging and production end up in the same
AWS account (as the plan calls for).
"""

from __future__ import annotations

import os

import aws_cdk as cdk

from config import get_config
from stacks import ComputeStack, DataStack, NetworkStack, ObservabilityStack


def main() -> None:
    app = cdk.App()

    env_name: str = (
        app.node.try_get_context("env")
        or os.environ.get("CDK_ENV")
        or "staging"
    )
    config = get_config(env_name)

    aws_env = cdk.Environment(
        # Account is intentionally unspecified at the CDK level so the
        # same code can synth against any account configured via
        # AWS_PROFILE / CDK_DEFAULT_ACCOUNT. cdk diff against an empty
        # account works without any AWS credentials.
        account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
        region=config["aws_region"],
    )

    prefix: str = config["stack_prefix"]

    # ------------------------------------------------------------------
    # Stack instantiation ---------------------------------------------
    # ------------------------------------------------------------------
    network = NetworkStack(
        app,
        f"{prefix}Network",
        config=config,
        env=aws_env,
        description=(
            f"FME Training Automation network ({env_name}): VPC, "
            f"subnets, security groups, NAT."
        ),
    )

    data = DataStack(
        app,
        f"{prefix}Data",
        config=config,
        vpc=network.vpc,
        rds_security_group=network.rds_sg,
        env=aws_env,
        description=(
            f"FME Training Automation data ({env_name}): RDS Postgres, "
            f"S3 buckets, KMS, Secrets Manager refs, CloudFront."
        ),
    )
    # CDK infers stack dependencies from cross-stack references — we
    # only force Network → Data because the SG / VPC handles must exist
    # before Data uses them (RDS subnet group lookup happens on every
    # synth). The other dependency chains are inferred automatically.
    data.add_dependency(network)

    compute = ComputeStack(
        app,
        f"{prefix}Compute",
        config=config,
        vpc=network.vpc,
        app_runner_security_group=network.app_runner_sg,
        fargate_security_group=network.fargate_sg,
        rds_instance=data.rds,
        kms_key=data.kms_key,
        artifacts_bucket=data.artifacts_bucket,
        drafts_bucket=data.drafts_bucket,
        skilljar_content_bucket=data.skilljar_content_bucket,
        cache_bucket=data.cache_bucket,
        secret_names=data.secret_names,
        rds_master_secret_arn=data.rds_master_secret_arn,
        env=aws_env,
        description=(
            f"FME Training Automation compute ({env_name}): App Runner "
            f"web/api, ECR, Fargate cluster + worker task def, IAM."
        ),
    )

    observability = ObservabilityStack(
        app,
        f"{prefix}Observability",
        config=config,
        rds_instance=data.rds,
        fargate_cluster=compute.fargate_cluster,
        app_runner_service=compute.app_runner_service,
        worker_log_group=compute.worker_log_group,
        web_log_group=compute.web_log_group,
        env=aws_env,
        description=(
            f"FME Training Automation observability ({env_name}): "
            f"CloudWatch alarms, dashboard, AWS Budget."
        ),
    )

    app.synth()


if __name__ == "__main__":
    main()
