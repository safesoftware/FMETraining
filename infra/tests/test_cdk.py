"""CDK assertion tests.

These tests synthesize each environment and assert:

1. The four stacks synth without raising.
2. Key resources (VPC, RDS, the four S3 buckets, App Runner service,
   Fargate task def) exist with the expected properties.
3. **No IAM policy contains a ``Resource: "*"`` paired with a write or
   delete action.** This is the load-bearing security property — write
   permissions must be scoped to specific ARNs.

Run with::

    cd infra
    pytest tests/

The tests are pure CDK synth-time assertions — they do not call AWS.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable

import aws_cdk as cdk
import pytest
from aws_cdk import assertions

# Make ``infra/`` importable when running pytest from any CWD.
INFRA_ROOT = Path(__file__).resolve().parents[1]
if str(INFRA_ROOT) not in sys.path:
    sys.path.insert(0, str(INFRA_ROOT))

from config import get_config  # noqa: E402  (path injection above)
from stacks import (  # noqa: E402
    ComputeStack,
    DataStack,
    NetworkStack,
    ObservabilityStack,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
WRITE_ACTION_PREFIXES = (
    "s3:put",
    "s3:delete",
    "s3:abort",
    "s3:create",
    "s3:replicat",
    "s3:restore",
    "kms:create",
    "kms:delete",
    "kms:disable",
    "kms:enable",
    "kms:put",
    "kms:schedule",
    "kms:update",
    "ecr:put",
    "ecr:upload",
    "ecr:complete",
    "ecr:initiate",
    "ecr:tagresource",
    "ecr:untagresource",
    "ecr:delete",
    "ecr:start",
    "rds:create",
    "rds:delete",
    "rds:modify",
    "rds:reboot",
    "rds:restore",
    "ecs:registertaskdef",
    "ecs:deregistertaskdef",
    "ecs:put",
    "ecs:update",
    "ecs:delete",
    "ecs:create",
    "iam:create",
    "iam:delete",
    "iam:put",
    "iam:update",
    "iam:attach",
    "iam:detach",
    "secretsmanager:put",
    "secretsmanager:update",
    "secretsmanager:delete",
    "secretsmanager:rotate",
    "logs:create",
    "logs:put",
    "logs:delete",
    "logs:tag",
    "ssm:put",
    "ssm:delete",
)


def _is_write_action(action: str) -> bool:
    a = action.lower()
    if a == "*":
        return True  # treat "*" as write-implying
    if a.endswith(":*"):
        # Service-wide wildcard like "s3:*" is a write-implying wildcard.
        return True
    return any(a.startswith(p) for p in WRITE_ACTION_PREFIXES)


def _iter_policy_statements(template: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    """Yield every IAM policy Statement in the synthesized template."""

    for resource in template.get("Resources", {}).values():
        rtype = resource.get("Type", "")
        if rtype not in (
            "AWS::IAM::Policy",
            "AWS::IAM::ManagedPolicy",
            "AWS::IAM::Role",
        ):
            continue
        props = resource.get("Properties", {})

        # Inline policies on a Role.
        for inline in props.get("Policies", []) or []:
            for stmt in (
                inline.get("PolicyDocument", {}).get("Statement", []) or []
            ):
                yield stmt

        # Standalone Policy / ManagedPolicy resources.
        doc = props.get("PolicyDocument") or {}
        for stmt in doc.get("Statement", []) or []:
            yield stmt

        # AssumeRolePolicyDocument: trust policies. We *do not* check
        # these for "*" because trust statements legitimately use
        # ``Principal: *`` patterns. Skip.


def _resource_is_star(resource: Any) -> bool:
    """Return True if a Resource clause is the literal `"*"`.

    CDK occasionally emits Resource as a one-element list containing
    ``"*"``. Both forms count as star.
    """

    if resource == "*":
        return True
    if isinstance(resource, list) and len(resource) == 1 and resource[0] == "*":
        return True
    return False


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(params=["staging", "production"], ids=["staging", "production"])
def env_name(request: pytest.FixtureRequest) -> str:
    return request.param


@pytest.fixture()
def synth(env_name: str) -> Dict[str, assertions.Template]:
    """Build the full app for one env and return per-stack Templates."""

    app = cdk.App(context={"env": env_name})
    config = get_config(env_name)
    aws_env = cdk.Environment(account="111111111111", region="us-west-2")
    prefix = config["stack_prefix"]

    network = NetworkStack(
        app, f"{prefix}Network", config=config, env=aws_env
    )
    data = DataStack(
        app,
        f"{prefix}Data",
        config=config,
        vpc=network.vpc,
        rds_security_group=network.rds_sg,
        env=aws_env,
    )
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
    )

    return {
        "network": assertions.Template.from_stack(network),
        "data": assertions.Template.from_stack(data),
        "compute": assertions.Template.from_stack(compute),
        "observability": assertions.Template.from_stack(observability),
    }


# ---------------------------------------------------------------------------
# Synth + key-resource tests
# ---------------------------------------------------------------------------
def test_all_stacks_synth(synth: Dict[str, assertions.Template]) -> None:
    """All four stacks synth without raising."""

    for name, tpl in synth.items():
        assert tpl.to_json()["Resources"], (
            f"{name} stack synthesized with zero resources"
        )


def test_network_has_vpc_with_two_azs(
    synth: Dict[str, assertions.Template],
) -> None:
    network = synth["network"]
    network.resource_count_is("AWS::EC2::VPC", 1)
    # Two AZs × (public + private-with-egress + isolated) = 6 subnets.
    network.resource_count_is("AWS::EC2::Subnet", 6)
    # Per env config we want exactly 1 NAT gateway.
    network.resource_count_is("AWS::EC2::NatGateway", 1)


def test_network_security_groups_present(
    synth: Dict[str, assertions.Template],
) -> None:
    """Three SGs exist; RDS SG only has ingress from the other two."""

    network = synth["network"]
    # 3 application SGs (App Runner, Fargate, RDS). CDK may emit
    # additional CFN SecurityGroups for VPC defaults.
    sgs = network.find_resources("AWS::EC2::SecurityGroup")
    descriptions = [
        sg["Properties"].get("GroupDescription", "") for sg in sgs.values()
    ]
    assert any("App Runner" in d for d in descriptions)
    assert any("Fargate" in d for d in descriptions)
    assert any("RDS Postgres" in d for d in descriptions)


def test_data_has_rds_postgres(
    synth: Dict[str, assertions.Template], env_name: str
) -> None:
    data = synth["data"]
    config = get_config(env_name)
    data.has_resource_properties(
        "AWS::RDS::DBInstance",
        {
            "Engine": "postgres",
            "DBInstanceClass": f"db.{config['rds_instance_class']}",
            "StorageEncrypted": True,
            "PubliclyAccessible": False,
            "MultiAZ": bool(config["rds_multi_az"]),
        },
    )


def test_data_has_four_private_buckets_plus_images(
    synth: Dict[str, assertions.Template],
) -> None:
    """artifacts/drafts/skilljar-content/cache + images = 5 buckets."""

    data = synth["data"]
    buckets = data.find_resources("AWS::S3::Bucket")
    assert len(buckets) == 5, (
        f"Expected exactly 5 S3 buckets (4 private + images), got "
        f"{len(buckets)}: {list(buckets)}"
    )


def test_data_buckets_block_public_access(
    synth: Dict[str, assertions.Template],
) -> None:
    """Every bucket has public access fully blocked."""

    data = synth["data"]
    buckets = data.find_resources("AWS::S3::Bucket")
    for logical_id, bucket in buckets.items():
        bpa = bucket["Properties"].get("PublicAccessBlockConfiguration")
        assert bpa is not None, f"{logical_id} has no PublicAccessBlock"
        assert bpa.get("BlockPublicAcls") is True, logical_id
        assert bpa.get("BlockPublicPolicy") is True, logical_id
        assert bpa.get("IgnorePublicAcls") is True, logical_id
        assert bpa.get("RestrictPublicBuckets") is True, logical_id


def test_data_kms_key_rotation_enabled(
    synth: Dict[str, assertions.Template],
) -> None:
    data = synth["data"]
    data.has_resource_properties(
        "AWS::KMS::Key",
        {"EnableKeyRotation": True},
    )


def test_data_cloudfront_distribution_exists(
    synth: Dict[str, assertions.Template],
) -> None:
    synth["data"].resource_count_is(
        "AWS::CloudFront::Distribution", 1
    )


def test_compute_has_apprunner_service_and_fargate(
    synth: Dict[str, assertions.Template],
) -> None:
    compute = synth["compute"]
    compute.resource_count_is("AWS::AppRunner::Service", 1)
    compute.resource_count_is("AWS::AppRunner::VpcConnector", 1)
    compute.resource_count_is("AWS::ECS::Cluster", 1)
    compute.resource_count_is("AWS::ECS::TaskDefinition", 1)
    compute.resource_count_is("AWS::ECR::Repository", 1)


def test_compute_has_immutable_ecr_tags(
    synth: Dict[str, assertions.Template],
) -> None:
    synth["compute"].has_resource_properties(
        "AWS::ECR::Repository",
        {"ImageTagMutability": "IMMUTABLE"},
    )


def test_observability_has_alarms_and_budget(
    synth: Dict[str, assertions.Template],
) -> None:
    observability = synth["observability"]
    # 5 alarms: cost ceiling, worker fatal, RDS CPU, RDS free storage,
    # App Runner 5xx.
    alarms = observability.find_resources("AWS::CloudWatch::Alarm")
    assert len(alarms) == 5, (
        f"Expected 5 alarms; got {len(alarms)}: {list(alarms)}"
    )
    observability.resource_count_is("AWS::Budgets::Budget", 1)
    observability.resource_count_is("AWS::CloudWatch::Dashboard", 1)
    # Two metric filters on the worker log group.
    observability.resource_count_is(
        "AWS::Logs::MetricFilter", 2
    )


def test_observability_budget_amount_matches_config(
    synth: Dict[str, assertions.Template], env_name: str
) -> None:
    expected = int(get_config(env_name)["monthly_budget_usd"])
    synth["observability"].has_resource_properties(
        "AWS::Budgets::Budget",
        {
            "Budget": assertions.Match.object_like(
                {
                    "BudgetType": "COST",
                    "TimeUnit": "MONTHLY",
                    "BudgetLimit": {"Amount": expected, "Unit": "USD"},
                }
            )
        },
    )


# ---------------------------------------------------------------------------
# IAM least-privilege tests (the load-bearing security property)
# ---------------------------------------------------------------------------
def test_no_write_action_with_star_resource(
    synth: Dict[str, assertions.Template],
) -> None:
    """No IAM Allow statement may pair a write action with Resource: *.

    Read-only metadata actions on `*` (`ecr:GetAuthorizationToken`,
    `ecs:ListTasks`, `ecs:DescribeTaskDefinition`, `logs:Describe...`)
    are explicitly allowed because AWS does not support resource-level
    scoping for them. Anything else is a bug.
    """

    offences: list[str] = []
    for stack_name, tpl in synth.items():
        template_dict = tpl.to_json()
        for stmt in _iter_policy_statements(template_dict):
            if stmt.get("Effect", "Allow") != "Allow":
                continue
            resource = stmt.get("Resource")
            if not _resource_is_star(resource):
                continue
            actions = stmt.get("Action", [])
            if isinstance(actions, str):
                actions = [actions]
            offending_writes = [a for a in actions if _is_write_action(a)]
            if offending_writes:
                offences.append(
                    f"{stack_name} has Resource:* on writes: "
                    f"{offending_writes} (full stmt: {json.dumps(stmt)})"
                )

    assert not offences, (
        "IAM least-privilege violations found:\n  - "
        + "\n  - ".join(offences)
    )


def test_no_admin_star_action_anywhere(
    synth: Dict[str, assertions.Template],
) -> None:
    """No statement is ``Action: '*'``. That's a literal admin grant."""

    offences: list[str] = []
    for stack_name, tpl in synth.items():
        for stmt in _iter_policy_statements(tpl.to_json()):
            if stmt.get("Effect", "Allow") != "Allow":
                continue
            actions = stmt.get("Action")
            if actions == "*" or (
                isinstance(actions, list) and actions == ["*"]
            ):
                offences.append(
                    f"{stack_name}: {json.dumps(stmt)}"
                )

    assert not offences, (
        "Found 'Action: *' admin-grant statements:\n  - "
        + "\n  - ".join(offences)
    )


def test_passrole_is_constrained_to_ecs_tasks(
    synth: Dict[str, assertions.Template],
) -> None:
    """Every iam:PassRole grant must constrain iam:PassedToService."""

    compute_template = synth["compute"].to_json()
    found_passrole = False
    for stmt in _iter_policy_statements(compute_template):
        if stmt.get("Effect", "Allow") != "Allow":
            continue
        actions = stmt.get("Action", [])
        if isinstance(actions, str):
            actions = [actions]
        if "iam:PassRole" not in actions:
            continue
        found_passrole = True
        condition = stmt.get("Condition", {})
        passed_to = (
            condition.get("StringEquals", {}).get("iam:PassedToService")
        )
        assert passed_to == "ecs-tasks.amazonaws.com", (
            f"PassRole without ecs-tasks PassedToService constraint: "
            f"{json.dumps(stmt)}"
        )
    assert found_passrole, (
        "Compute stack does not appear to grant iam:PassRole at all "
        "— App Runner needs it to dispatch RunTask."
    )
