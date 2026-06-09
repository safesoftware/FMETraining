"""Compute stack: App Runner web/api, ECR repo, Fargate worker, IAM.

Per plan section 1 / section 3 / section 6:

* **App Runner** runs the FastAPI web/api in always-on mode, fronts the
  browser UI, and dispatches Fargate tasks via ``boto3.client('ecs').
  run_task()``. App Runner reaches RDS through a VPC connector attached
  to the network stack's private subnets.
* **ECR repository** holds the dual-mode container image (web vs worker
  selected via ``ENTRYPOINT_MODE`` env var). CI/CD pushes new images
  tagged with the git SHA.
* **Fargate cluster + task definition** runs one ephemeral worker per
  pipeline run. The task role is intentionally narrower than the App
  Runner role:

      App Runner role  → reads/writes any ``runs`` row, dispatches ECS
                         tasks, reads/writes any S3 prefix under the
                         four buckets, reads named secrets.

      Fargate task role → reads/writes only its *own* ``runs`` row's
                          slice of S3 (``artifacts/${RUN_ID}/*``,
                          ``drafts/${TO_VERSION}/*``,
                          ``skilljar-content/*`` read-only,
                          ``cache/*``), and reads named secrets only.
                          DB row-level isolation is enforced *in the
                          worker's SQL* (every UPDATE has
                          ``WHERE run_id = :run_id``); IAM cannot
                          enforce this at the row level for RDS.

* IAM policies use scoped resource ARNs everywhere. The only ``Resource:
  "*"`` you'll find in the synthesized output is on read-only metadata
  actions (``ecr:GetAuthorizationToken``, ``logs:DescribeLogGroups``)
  where AWS does not allow resource-level scoping.

Note: ``aws_apprunner.CfnService`` is a CloudFormation L1 because the
L2 ``aws_apprunner_alpha`` module is still pre-release jsii (the plan
forbids us using jsii pre-release deps). The L1 surface is a little
verbose but stable.
"""

from __future__ import annotations

from typing import Any, Dict

from aws_cdk import Duration, RemovalPolicy, Stack, Tags
from aws_cdk import aws_apprunner as apprunner
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecr as ecr
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_iam as iam
from aws_cdk import aws_kms as kms
from aws_cdk import aws_logs as logs
from aws_cdk import aws_rds as rds
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_secretsmanager as secretsmanager
from aws_cdk import aws_ssm as ssm
from constructs import Construct


def _sanitize(name: str) -> str:
    """Convert a secret name to a CDK-safe construct ID suffix."""

    parts = name.replace("/", "-").split("-")
    return "".join(p.capitalize() for p in parts if p)


class ComputeStack(Stack):
    """App Runner + ECR + Fargate + IAM roles."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        config: Dict[str, Any],
        vpc: ec2.IVpc,
        app_runner_security_group: ec2.ISecurityGroup,
        fargate_security_group: ec2.ISecurityGroup,
        rds_instance: rds.IDatabaseInstance,
        kms_key: kms.IKey,
        artifacts_bucket: s3.IBucket,
        drafts_bucket: s3.IBucket,
        skilljar_content_bucket: s3.IBucket,
        cache_bucket: s3.IBucket,
        secret_names: list[str],
        rds_master_secret_arn: str,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        for tag_key, tag_value in config["tags"].items():
            Tags.of(self).add(tag_key, tag_value)

        env_name: str = config["env_name"]

        # ------------------------------------------------------------------
        # Secrets Manager: import every named secret inside *this* stack so
        # resource policies CDK auto-adds when granting Read end up in this
        # template (not in the data stack), avoiding a cross-stack cycle.
        # ------------------------------------------------------------------
        secrets: Dict[str, secretsmanager.ISecret] = {}
        for secret_name in secret_names:
            if secret_name == "rds-master-credentials":
                # Re-import inside this stack to break the cycle: an
                # imported `ISecret` is opaque to CDK so `grant_read`
                # only adds an identity policy on the role and never
                # tries to mutate the secret's resource policy.
                secrets[secret_name] = (
                    secretsmanager.Secret.from_secret_complete_arn(
                        self,
                        "RdsMasterSecretRef",
                        secret_complete_arn=rds_master_secret_arn,
                    )
                )
                continue
            arn_param = ssm.StringParameter.from_string_parameter_name(
                self,
                f"SecretArn-{_sanitize(secret_name)}",
                string_parameter_name=(
                    f"/fme-train/{env_name}/secrets/{secret_name}/arn"
                ),
            )
            secrets[secret_name] = (
                secretsmanager.Secret.from_secret_complete_arn(
                    self,
                    f"Secret-{_sanitize(secret_name)}",
                    secret_complete_arn=arn_param.string_value,
                )
            )
        self.secrets = secrets

        # ------------------------------------------------------------------
        # ECR repository for the dual-mode container image -----------------
        # ------------------------------------------------------------------
        self.ecr_repo = ecr.Repository(
            self,
            "AppImageRepo",
            repository_name=f"fme-train-{env_name}",
            image_scan_on_push=True,
            image_tag_mutability=ecr.TagMutability.IMMUTABLE,
            removal_policy=(
                RemovalPolicy.RETAIN
                if env_name == "production"
                else RemovalPolicy.DESTROY
            ),
            empty_on_delete=env_name != "production",
            lifecycle_rules=[
                ecr.LifecycleRule(
                    description="Expire untagged images after 14 days.",
                    tag_status=ecr.TagStatus.UNTAGGED,
                    max_image_age=Duration.days(14),
                ),
                ecr.LifecycleRule(
                    description="Keep only the 30 most recent tagged images.",
                    tag_status=ecr.TagStatus.ANY,
                    max_image_count=30,
                ),
            ],
        )

        # ------------------------------------------------------------------
        # Fargate cluster --------------------------------------------------
        # ------------------------------------------------------------------
        self.fargate_cluster = ecs.Cluster(
            self,
            "RunCluster",
            cluster_name=f"fme-train-{env_name}-runs",
            vpc=vpc,
            container_insights=True,
        )

        # ------------------------------------------------------------------
        # Cost-ceiling parameter (read by the worker per plan section 3) --
        # ------------------------------------------------------------------
        self.max_run_usd_param = ssm.StringParameter(
            self,
            "MaxRunUsdParam",
            parameter_name=f"/fme-train/{env_name}/max-run-usd",
            string_value=str(config["max_run_usd"]),
            description=(
                "Per-run OpenAI cost ceiling (USD). Worker aborts when "
                "projected total exceeds this value."
            ),
            tier=ssm.ParameterTier.STANDARD,
        )

        # ------------------------------------------------------------------
        # Log groups (one per service)
        # ------------------------------------------------------------------
        log_retention = self._retention_days(int(config["log_retention_days"]))

        self.web_log_group = logs.LogGroup(
            self,
            "WebLogGroup",
            log_group_name=f"/fme-train/{env_name}/web",
            retention=log_retention,
            removal_policy=(
                RemovalPolicy.RETAIN
                if env_name == "production"
                else RemovalPolicy.DESTROY
            ),
        )
        self.worker_log_group = logs.LogGroup(
            self,
            "WorkerLogGroup",
            log_group_name=f"/fme-train/{env_name}/worker",
            retention=log_retention,
            removal_policy=(
                RemovalPolicy.RETAIN
                if env_name == "production"
                else RemovalPolicy.DESTROY
            ),
        )

        # ------------------------------------------------------------------
        # IAM: Fargate task execution role (used by ECS to PULL the image
        # and push platform logs — does NOT include app-level perms).
        # ------------------------------------------------------------------
        self.task_execution_role = iam.Role(
            self,
            "TaskExecutionRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            description=(
                "Fargate execution role: image pull + log shipping only."
            ),
        )
        # Inline ECR + Logs scoped to *this* repo and *this* log group.
        # We deliberately avoid `repo.grant_pull` / `log_group.grant_write`
        # because those mutate the resource (adding a resource policy)
        # which forces the data/compute stacks into a dependency loop.
        self.task_execution_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "ecr:BatchCheckLayerAvailability",
                    "ecr:GetDownloadUrlForLayer",
                    "ecr:BatchGetImage",
                ],
                resources=[self.ecr_repo.repository_arn],
                effect=iam.Effect.ALLOW,
            )
        )
        self.task_execution_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                ],
                resources=[
                    self.worker_log_group.log_group_arn,
                    f"{self.worker_log_group.log_group_arn}:*",
                ],
                effect=iam.Effect.ALLOW,
            )
        )
        # ECR auth token cannot be scoped to a single repo (AWS API limit).
        # This is metadata-only and read-only, so it is acceptable.
        self.task_execution_role.add_to_policy(
            iam.PolicyStatement(
                actions=["ecr:GetAuthorizationToken"],
                resources=["*"],
                effect=iam.Effect.ALLOW,
            )
        )

        # ------------------------------------------------------------------
        # IAM: Fargate task role  (the worker's *application* perms)
        # ------------------------------------------------------------------
        # Per-run S3 isolation is enforced via key-prefix scoping. The
        # worker is told its RUN_ID at task launch, so the prefix is
        # deterministic.
        self.worker_role = iam.Role(
            self,
            "WorkerTaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            description=(
                "Fargate worker app role: scoped S3, named secrets, KMS "
                "decrypt for those S3 prefixes only."
            ),
        )

        # S3 - run-specific prefixes ---------------------------------------
        # artifacts: read+write its own ${RUN_ID}/* prefix
        self.worker_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:DeleteObject",
                    "s3:AbortMultipartUpload",
                ],
                resources=[
                    artifacts_bucket.arn_for_objects(
                        "${aws:PrincipalTag/run_id}/*"
                    ),
                ],
                effect=iam.Effect.ALLOW,
            )
        )
        # drafts: read+write under its target version prefix.
        self.worker_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:DeleteObject",
                    "s3:AbortMultipartUpload",
                ],
                resources=[
                    drafts_bucket.arn_for_objects(
                        "${aws:PrincipalTag/to_version}/*"
                    ),
                ],
                effect=iam.Effect.ALLOW,
            )
        )
        # skilljar-content: read-only (cache populated by the web app).
        self.worker_role.add_to_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject"],
                resources=[skilljar_content_bucket.arn_for_objects("*")],
                effect=iam.Effect.ALLOW,
            )
        )
        # cache: read+write entire cache (fingerprints are content-addressed
        # so cross-run leakage is by design — that's the whole point of the
        # shared cache).
        self.worker_role.add_to_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject", "s3:PutObject"],
                resources=[cache_bucket.arn_for_objects("*")],
                effect=iam.Effect.ALLOW,
            )
        )
        # ListBucket for each bucket — required so the worker can scan
        # prefixes. Scoped to bucket ARNs (not "*").
        self.worker_role.add_to_policy(
            iam.PolicyStatement(
                actions=["s3:ListBucket", "s3:GetBucketLocation"],
                resources=[
                    artifacts_bucket.bucket_arn,
                    drafts_bucket.bucket_arn,
                    skilljar_content_bucket.bucket_arn,
                    cache_bucket.bucket_arn,
                ],
                effect=iam.Effect.ALLOW,
            )
        )

        # KMS — Decrypt + GenerateDataKey for the data CMK only -----------
        self.worker_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "kms:Decrypt",
                    "kms:GenerateDataKey",
                ],
                resources=[kms_key.key_arn],
                effect=iam.Effect.ALLOW,
            )
        )

        # Secrets: only the named secrets, by ARN -------------------------
        # Use identity-based statements (not `secret.grant_read`) so we
        # don't have CDK try to mutate the secret's resource policy from
        # this stack — that would create a cross-stack cycle with data.
        secret_arns = sorted({s.secret_arn for s in secrets.values()})
        self.worker_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "secretsmanager:GetSecretValue",
                    "secretsmanager:DescribeSecret",
                ],
                resources=secret_arns,
                effect=iam.Effect.ALLOW,
            )
        )

        # SSM parameter (cost ceiling) ------------------------------------
        self.worker_role.add_to_policy(
            iam.PolicyStatement(
                actions=["ssm:GetParameter", "ssm:GetParameters"],
                resources=[self.max_run_usd_param.parameter_arn],
                effect=iam.Effect.ALLOW,
            )
        )

        # CloudWatch Logs: write only to the worker log group -------------
        self.worker_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                ],
                resources=[
                    self.worker_log_group.log_group_arn,
                    f"{self.worker_log_group.log_group_arn}:*",
                ],
                effect=iam.Effect.ALLOW,
            )
        )

        # RDS access at the IAM layer is "permission to connect"; the
        # actual SQL-level row scoping (write only own runs/run_logs/etc.
        # rows) is enforced in the worker's SQL with `WHERE run_id =
        # :run_id` — IAM cannot do that for RDS Postgres without IAM auth.
        # We deliberately do not enable IAM auth at this scale.

        # ------------------------------------------------------------------
        # Fargate task definition ------------------------------------------
        # ------------------------------------------------------------------
        # The container image is rendered via ``ContainerImage.from_ecr_
        # repository`` so CI/CD can push images and the task picks up the
        # ``latest`` tag at run time. Production deploys pin to a SHA via
        # ``cdk deploy -c image_tag=<sha>``.
        image_tag = self.node.try_get_context("image_tag") or "latest"

        self.worker_task_definition = ecs.FargateTaskDefinition(
            self,
            "WorkerTaskDef",
            cpu=int(config["fargate_cpu"]),
            memory_limit_mib=int(config["fargate_memory_mib"]),
            execution_role=self.task_execution_role,
            task_role=self.worker_role,
            family=f"fme-train-{env_name}-worker",
        )
        self.worker_task_definition.add_container(
            "Worker",
            image=ecs.ContainerImage.from_ecr_repository(
                self.ecr_repo, image_tag
            ),
            command=["python", "-m", "worker"],
            environment={
                "ENTRYPOINT_MODE": "worker",
                "ENV_NAME": env_name,
                "AWS_REGION": config["aws_region"],
                "S3_ARTIFACTS_BUCKET": artifacts_bucket.bucket_name,
                "S3_DRAFTS_BUCKET": drafts_bucket.bucket_name,
                "S3_SKILLJAR_CONTENT_BUCKET": (
                    skilljar_content_bucket.bucket_name
                ),
                "S3_CACHE_BUCKET": cache_bucket.bucket_name,
                "MAX_RUN_USD_PARAM": self.max_run_usd_param.parameter_name,
                "FARGATE_TASK_MAX_MINUTES": str(
                    config["fargate_task_max_minutes"]
                ),
            },
            secrets=self._build_container_secrets(secrets, rds_instance),
            logging=ecs.LogDriver.aws_logs(
                stream_prefix="worker",
                log_group=self.worker_log_group,
            ),
            essential=True,
        )

        # ------------------------------------------------------------------
        # App Runner — VPC connector + service -----------------------------
        # ------------------------------------------------------------------
        self.app_runner_vpc_connector = apprunner.CfnVpcConnector(
            self,
            "WebVpcConnector",
            vpc_connector_name=f"fme-train-{env_name}-web",
            subnets=[s.subnet_id for s in vpc.private_subnets],
            security_groups=[app_runner_security_group.security_group_id],
        )

        # Access role: lets App Runner pull from ECR.
        self.app_runner_access_role = iam.Role(
            self,
            "AppRunnerAccessRole",
            assumed_by=iam.ServicePrincipal("build.apprunner.amazonaws.com"),
            description="App Runner ECR pull role.",
        )
        self.app_runner_access_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "ecr:BatchCheckLayerAvailability",
                    "ecr:GetDownloadUrlForLayer",
                    "ecr:BatchGetImage",
                    "ecr:DescribeImages",
                ],
                resources=[self.ecr_repo.repository_arn],
                effect=iam.Effect.ALLOW,
            )
        )
        self.app_runner_access_role.add_to_policy(
            iam.PolicyStatement(
                actions=["ecr:GetAuthorizationToken"],
                resources=["*"],
                effect=iam.Effect.ALLOW,
            )
        )

        # Instance role: App Runner's runtime app permissions ------------
        self.app_runner_instance_role = iam.Role(
            self,
            "AppRunnerInstanceRole",
            assumed_by=iam.ServicePrincipal("tasks.apprunner.amazonaws.com"),
            description=(
                "App Runner runtime role: secrets, S3 buckets, RunTask "
                "dispatch, log writing."
            ),
        )

        # S3: web/api needs full access to all four buckets (it's the
        # control plane). Still scoped to specific bucket ARNs - no '*'.
        # Use identity-based policy statements rather than
        # `bucket.grant_read_write` so CDK does not also mutate the
        # bucket's resource policy or KMS key policy from this stack
        # (that would create a cross-stack cycle).
        all_app_buckets = (
            artifacts_bucket,
            drafts_bucket,
            skilljar_content_bucket,
            cache_bucket,
        )
        self.app_runner_instance_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:DeleteObject",
                    "s3:AbortMultipartUpload",
                ],
                resources=[b.arn_for_objects("*") for b in all_app_buckets],
                effect=iam.Effect.ALLOW,
            )
        )
        self.app_runner_instance_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "s3:ListBucket",
                    "s3:GetBucketLocation",
                ],
                resources=[b.bucket_arn for b in all_app_buckets],
                effect=iam.Effect.ALLOW,
            )
        )
        self.app_runner_instance_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "kms:Encrypt",
                    "kms:Decrypt",
                    "kms:ReEncrypt*",
                    "kms:GenerateDataKey*",
                    "kms:DescribeKey",
                ],
                resources=[kms_key.key_arn],
                effect=iam.Effect.ALLOW,
            )
        )

        # Secrets: read all named secrets.
        self.app_runner_instance_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "secretsmanager:GetSecretValue",
                    "secretsmanager:DescribeSecret",
                ],
                resources=secret_arns,
                effect=iam.Effect.ALLOW,
            )
        )

        # ECS RunTask: scoped to *this* task definition family + cluster.
        # We use the task-def family ARN with a wildcard for the revision.
        task_def_family_arn = self.format_arn(
            service="ecs",
            resource="task-definition",
            resource_name=(
                f"fme-train-{env_name}-worker:*"
            ),
        )
        self.app_runner_instance_role.add_to_policy(
            iam.PolicyStatement(
                actions=["ecs:RunTask", "ecs:StopTask", "ecs:DescribeTasks"],
                resources=[task_def_family_arn],
                conditions={
                    "ArnEquals": {
                        "ecs:cluster": self.fargate_cluster.cluster_arn,
                    }
                },
                effect=iam.Effect.ALLOW,
            )
        )
        # PassRole for the worker + execution roles (RunTask requires it).
        self.app_runner_instance_role.add_to_policy(
            iam.PolicyStatement(
                actions=["iam:PassRole"],
                resources=[
                    self.worker_role.role_arn,
                    self.task_execution_role.role_arn,
                ],
                conditions={
                    "StringEquals": {
                        "iam:PassedToService": "ecs-tasks.amazonaws.com",
                    },
                },
                effect=iam.Effect.ALLOW,
            )
        )
        # ListTasks/DescribeTaskDefinition do not support resource-level
        # scoping (AWS limitation). Read-only, narrow set, acceptable.
        self.app_runner_instance_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "ecs:ListTasks",
                    "ecs:DescribeTaskDefinition",
                ],
                resources=["*"],
                effect=iam.Effect.ALLOW,
            )
        )

        # CloudWatch Logs: write only to the web log group.
        self.app_runner_instance_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                ],
                resources=[
                    self.web_log_group.log_group_arn,
                    f"{self.web_log_group.log_group_arn}:*",
                ],
                effect=iam.Effect.ALLOW,
            )
        )

        # SSM cost-ceiling parameter
        self.app_runner_instance_role.add_to_policy(
            iam.PolicyStatement(
                actions=["ssm:GetParameter", "ssm:GetParameters"],
                resources=[self.max_run_usd_param.parameter_arn],
                effect=iam.Effect.ALLOW,
            )
        )

        # The actual App Runner service ----------------------------------
        # We expose the image via ImageRepository (ECR). Health check is
        # the /healthz endpoint the FastAPI app exposes.
        self.app_runner_service = apprunner.CfnService(
            self,
            "WebService",
            service_name=f"fme-train-{env_name}-web",
            source_configuration=apprunner.CfnService.SourceConfigurationProperty(
                authentication_configuration=apprunner.CfnService.AuthenticationConfigurationProperty(
                    access_role_arn=self.app_runner_access_role.role_arn,
                ),
                auto_deployments_enabled=False,
                image_repository=apprunner.CfnService.ImageRepositoryProperty(
                    image_identifier=(
                        f"{self.ecr_repo.repository_uri}:{image_tag}"
                    ),
                    image_repository_type="ECR",
                    image_configuration=apprunner.CfnService.ImageConfigurationProperty(
                        port="8000",
                        runtime_environment_variables=self._app_runner_env(
                            config=config,
                            artifacts_bucket=artifacts_bucket,
                            drafts_bucket=drafts_bucket,
                            skilljar_content_bucket=skilljar_content_bucket,
                            cache_bucket=cache_bucket,
                            cluster_arn=self.fargate_cluster.cluster_arn,
                            task_def_family=(
                                f"fme-train-{env_name}-worker"
                            ),
                        ),
                        runtime_environment_secrets=(
                            self._app_runner_secrets(secrets, rds_instance)
                        ),
                    ),
                ),
            ),
            instance_configuration=apprunner.CfnService.InstanceConfigurationProperty(
                cpu=config["app_runner_cpu"],
                memory=config["app_runner_memory"],
                instance_role_arn=self.app_runner_instance_role.role_arn,
            ),
            network_configuration=apprunner.CfnService.NetworkConfigurationProperty(
                egress_configuration=apprunner.CfnService.EgressConfigurationProperty(
                    egress_type="VPC",
                    vpc_connector_arn=(
                        self.app_runner_vpc_connector.attr_vpc_connector_arn
                    ),
                ),
                ingress_configuration=apprunner.CfnService.IngressConfigurationProperty(
                    is_publicly_accessible=True,
                ),
            ),
            health_check_configuration=apprunner.CfnService.HealthCheckConfigurationProperty(
                protocol="HTTP",
                path="/healthz",
                interval=10,
                timeout=5,
                healthy_threshold=1,
                unhealthy_threshold=3,
            ),
        )
        # Make the service depend on the VPC connector (CFN ordering).
        self.app_runner_service.add_dependency(self.app_runner_vpc_connector)

    # ----------------------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------------------
    @staticmethod
    def _retention_days(days: int) -> logs.RetentionDays:
        """Map an int day count to the closest CloudWatch enum."""

        # CloudWatch only allows discrete retention buckets.
        buckets = [
            (1, logs.RetentionDays.ONE_DAY),
            (3, logs.RetentionDays.THREE_DAYS),
            (5, logs.RetentionDays.FIVE_DAYS),
            (7, logs.RetentionDays.ONE_WEEK),
            (14, logs.RetentionDays.TWO_WEEKS),
            (30, logs.RetentionDays.ONE_MONTH),
            (60, logs.RetentionDays.TWO_MONTHS),
            (90, logs.RetentionDays.THREE_MONTHS),
            (120, logs.RetentionDays.FOUR_MONTHS),
            (150, logs.RetentionDays.FIVE_MONTHS),
            (180, logs.RetentionDays.SIX_MONTHS),
            (365, logs.RetentionDays.ONE_YEAR),
            (400, logs.RetentionDays.THIRTEEN_MONTHS),
            (545, logs.RetentionDays.EIGHTEEN_MONTHS),
            (731, logs.RetentionDays.TWO_YEARS),
        ]
        for cap, enum in buckets:
            if days <= cap:
                return enum
        return logs.RetentionDays.TEN_YEARS

    @staticmethod
    def _build_container_secrets(
        secrets: Dict[str, secretsmanager.ISecret],
        rds_instance: rds.IDatabaseInstance,
    ) -> Dict[str, ecs.Secret]:
        """Translate Secrets-Manager refs into ECS container secrets."""

        out: Dict[str, ecs.Secret] = {}
        # Map secret-name → env-var name. Underscored, uppercased.
        for name, secret in secrets.items():
            env_var = name.upper().replace("-", "_")
            if name == "rds-master-credentials":
                # Pull the URL from the SecretsManager JSON. RDS-managed
                # secrets contain {host,port,username,password,dbname}.
                out["DATABASE_HOST"] = ecs.Secret.from_secrets_manager(
                    secret, field="host"
                )
                out["DATABASE_PORT"] = ecs.Secret.from_secrets_manager(
                    secret, field="port"
                )
                out["DATABASE_USER"] = ecs.Secret.from_secrets_manager(
                    secret, field="username"
                )
                out["DATABASE_PASSWORD"] = ecs.Secret.from_secrets_manager(
                    secret, field="password"
                )
                out["DATABASE_NAME"] = ecs.Secret.from_secrets_manager(
                    secret, field="dbname"
                )
                continue
            out[env_var] = ecs.Secret.from_secrets_manager(secret)
        return out

    @staticmethod
    def _app_runner_secrets(
        secrets: Dict[str, secretsmanager.ISecret],
        rds_instance: rds.IDatabaseInstance,
    ) -> list[apprunner.CfnService.KeyValuePairProperty]:
        """App Runner takes secrets as ``KeyValuePair(name, value=ARN)``."""

        out: list[apprunner.CfnService.KeyValuePairProperty] = []
        for name, secret in secrets.items():
            if name == "rds-master-credentials":
                # Same mapping as the worker container.
                for field in ("host", "port", "username", "password", "dbname"):
                    out.append(
                        apprunner.CfnService.KeyValuePairProperty(
                            name=f"DATABASE_{field.upper()}",
                            value=(
                                f"{secret.secret_arn}:{field}::"
                            ),
                        )
                    )
                continue
            env_var = name.upper().replace("-", "_")
            out.append(
                apprunner.CfnService.KeyValuePairProperty(
                    name=env_var,
                    value=secret.secret_arn,
                )
            )
        return out

    @staticmethod
    def _app_runner_env(
        *,
        config: Dict[str, Any],
        artifacts_bucket: s3.IBucket,
        drafts_bucket: s3.IBucket,
        skilljar_content_bucket: s3.IBucket,
        cache_bucket: s3.IBucket,
        cluster_arn: str,
        task_def_family: str,
    ) -> list[apprunner.CfnService.KeyValuePairProperty]:
        plain: Dict[str, str] = {
            "ENTRYPOINT_MODE": "web",
            "ENV_NAME": config["env_name"],
            "AWS_REGION": config["aws_region"],
            "S3_ARTIFACTS_BUCKET": artifacts_bucket.bucket_name,
            "S3_DRAFTS_BUCKET": drafts_bucket.bucket_name,
            "S3_SKILLJAR_CONTENT_BUCKET": skilljar_content_bucket.bucket_name,
            "S3_CACHE_BUCKET": cache_bucket.bucket_name,
            "FARGATE_CLUSTER_ARN": cluster_arn,
            "FARGATE_TASK_DEF_FAMILY": task_def_family,
            "MAX_RUN_USD_PARAM": (
                f"/fme-train/{config['env_name']}/max-run-usd"
            ),
        }
        return [
            apprunner.CfnService.KeyValuePairProperty(name=k, value=v)
            for k, v in plain.items()
        ]
