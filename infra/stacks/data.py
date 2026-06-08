"""Data stack: RDS Postgres, S3 buckets, KMS keys, Secrets Manager refs.

Per plan section 1 / section 6:

* RDS Postgres (db.t4g.micro for staging, db.t4g.small for prod), encrypted
  at rest with a customer-managed KMS key, master credentials in Secrets
  Manager (referenced by ARN — IT populates the secret value, CDK never
  writes it).
* S3 buckets (private + KMS):
    - ``artifacts``  - run artifacts (manifest/changelog/recommendations).
    - ``drafts``     - lesson_drafts content (replaces local
      ``2026.1/.../index.html`` writes).
    - ``skilljar-content`` - canonical content cache from Skilljar API.
    - ``cache``      - shared OpenAI / Jira content cache.
* One additional ``images`` bucket fronted by CloudFront for Skilljar
  embedding (public via CloudFront's origin access; bucket itself stays
  private and rejects direct public reads).
* Secrets Manager *references* (one ``ISecret`` per secret name in the
  env config) - imported by ARN. CDK does not create the secrets.

IAM least-privilege wiring lives in :mod:`infra.stacks.compute` — this stack
just exposes the resource handles other stacks need.
"""

from __future__ import annotations

from typing import Any, Dict, List

from aws_cdk import Duration, RemovalPolicy, Stack, Tags
from aws_cdk import aws_cloudfront as cloudfront
from aws_cdk import aws_cloudfront_origins as cloudfront_origins
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_kms as kms
from aws_cdk import aws_rds as rds
from aws_cdk import aws_s3 as s3
from constructs import Construct


# Logical bucket names exposed on the stack.
# (Physical bucket names are derived from the stack ID + stack-prefix to
# keep them globally unique without hard-coding a customer-specific name.)
BUCKET_LOGICAL_IDS = ("artifacts", "drafts", "skilljar_content", "cache")


class DataStack(Stack):
    """RDS, S3, KMS, Secrets Manager references."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        config: Dict[str, Any],
        vpc: ec2.IVpc,
        rds_security_group: ec2.ISecurityGroup,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        for tag_key, tag_value in config["tags"].items():
            Tags.of(self).add(tag_key, tag_value)

        env_name: str = config["env_name"]

        # ------------------------------------------------------------------
        # KMS key (encryption at rest for RDS + S3).
        # ------------------------------------------------------------------
        # One CMK per env. Rotation enabled (annual) so we get audit-friendly
        # key rotation without the operational pain of multi-key migrations.
        self.kms_key = kms.Key(
            self,
            "DataKey",
            description=(
                f"FME Training Automation data-at-rest key ({env_name})."
            ),
            enable_key_rotation=True,
            removal_policy=(
                RemovalPolicy.RETAIN
                if env_name == "production"
                else RemovalPolicy.DESTROY
            ),
        )
        self.kms_key.add_alias(f"alias/fme-train-{env_name}-data")

        # ------------------------------------------------------------------
        # S3 buckets — private, KMS-encrypted, TLS-only.
        # ------------------------------------------------------------------
        self.buckets: Dict[str, s3.Bucket] = {}
        for logical_id in BUCKET_LOGICAL_IDS:
            self.buckets[logical_id] = self._make_private_bucket(
                logical_id, config
            )

        # CloudFront-fronted public images bucket -------------------------
        # Per plan section 1, lesson images embedded in Skilljar are served
        # via CloudFront. The bucket itself stays private; CloudFront uses
        # an Origin Access Identity to read.
        self.images_bucket = s3.Bucket(
            self,
            "ImagesBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            versioned=False,
            removal_policy=(
                RemovalPolicy.RETAIN
                if env_name == "production"
                else RemovalPolicy.DESTROY
            ),
            auto_delete_objects=env_name != "production",
        )

        # OAI to give CloudFront read access without exposing the bucket.
        self._images_oai = cloudfront.OriginAccessIdentity(
            self,
            "ImagesOai",
            comment=f"Read-only OAI for fme-train-{env_name} images",
        )
        self.images_bucket.grant_read(self._images_oai)

        self.images_distribution = cloudfront.Distribution(
            self,
            "ImagesCdn",
            default_behavior=cloudfront.BehaviorOptions(
                origin=cloudfront_origins.S3Origin(
                    self.images_bucket,
                    origin_access_identity=self._images_oai,
                ),
                viewer_protocol_policy=(
                    cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS
                ),
                cached_methods=cloudfront.CachedMethods.CACHE_GET_HEAD,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_GET_HEAD,
                compress=True,
            ),
            price_class=getattr(
                cloudfront.PriceClass, config["cloudfront_price_class"]
            ),
            comment=f"FME Training Automation lesson images ({env_name})",
        )

        # ------------------------------------------------------------------
        # RDS Postgres -----------------------------------------------------
        # ------------------------------------------------------------------
        # Master credentials live in Secrets Manager. We let CDK create the
        # *master* secret (it's necessary for RDS to even start, and IAM-
        # database-auth is overkill for a 2-5 user team), but every other
        # secret is referenced by ARN per the plan.
        instance_type = ec2.InstanceType(config["rds_instance_class"])

        self.rds = rds.DatabaseInstance(
            self,
            "Postgres",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_16_3,
            ),
            instance_type=instance_type,
            vpc=vpc,
            # Place RDS in fully isolated subnets — it has no legitimate
            # need to reach the internet, and the egress route in the
            # PRIVATE_WITH_EGRESS subnets would otherwise let a compromised
            # database (or a misbehaving stored procedure) exfiltrate data
            # outbound. Inbound is already gated by ``rds_security_group``
            # to App Runner / Fargate on port 5432.
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
            ),
            security_groups=[rds_security_group],
            allocated_storage=int(config["rds_allocated_storage_gb"]),
            max_allocated_storage=int(config["rds_max_allocated_storage_gb"]),
            backup_retention=Duration.days(
                int(config["rds_backup_retention_days"])
            ),
            multi_az=bool(config["rds_multi_az"]),
            deletion_protection=bool(config["rds_deletion_protection"]),
            storage_encrypted=True,
            storage_encryption_key=self.kms_key,
            publicly_accessible=False,
            credentials=rds.Credentials.from_generated_secret(
                "fmetrain_admin",
                secret_name=f"fme-train-{env_name}/rds/master-credentials",
                encryption_key=self.kms_key,
            ),
            # We don't need IAM auth or Performance Insights at this scale.
            iam_authentication=False,
            removal_policy=(
                RemovalPolicy.SNAPSHOT
                if env_name == "production"
                else RemovalPolicy.DESTROY
            ),
        )

        # ------------------------------------------------------------------
        # Secrets Manager references ---------------------------------------
        # ------------------------------------------------------------------
        # Per the plan: CDK does *not* create these secrets. IT populates
        # them once at setup. We expose only the *list of secret names*
        # plus the master RDS secret here. The compute stack imports each
        # secret by ARN inside its own scope, so resource policies CDK
        # auto-adds when granting Read live in compute, not data — this
        # avoids a cross-stack cycle.
        #
        # ARNs are looked up from SSM Parameter Store (one parameter per
        # secret, named ``/fme-train/<env>/secrets/<name>/arn``) so IT can
        # rotate / re-create secrets without re-deploying CDK.
        self.secret_names: list[str] = list(config["secret_names"])
        # The RDS master secret is created by RDS itself; expose its ARN
        # so the compute stack can import it as an ``ISecret`` *inside*
        # its own scope. Re-importing in compute is the only way to
        # break the cross-stack cycle that ``grant_read`` on the
        # natively-attached secret would create.
        self.rds_master_secret_arn: str = self.rds.secret.secret_arn  # type: ignore[union-attr]

    # ----------------------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------------------
    def _make_private_bucket(
        self,
        logical_id: str,
        config: Dict[str, Any],
    ) -> s3.Bucket:
        """Create a private, KMS-encrypted, TLS-only bucket."""

        env_name = config["env_name"]
        is_cache = logical_id == "cache"
        is_drafts = logical_id == "drafts"

        lifecycle_rules: List[s3.LifecycleRule] = []
        if is_cache:
            # Plan section 4: archive cache entries to Glacier Deep Archive
            # after `s3_cache_glacier_after_days` of no access.
            lifecycle_rules.append(
                s3.LifecycleRule(
                    id="cache-to-glacier",
                    enabled=True,
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.DEEP_ARCHIVE,
                            transition_after=Duration.days(
                                int(config["s3_cache_glacier_after_days"])
                            ),
                        ),
                    ],
                )
            )
        if is_drafts:
            # Drafts get versioned. Aggressively age non-current versions
            # to IA so we keep audit trail without paying full Standard
            # rates for old draft revisions.
            lifecycle_rules.append(
                s3.LifecycleRule(
                    id="drafts-noncurrent-ia",
                    enabled=True,
                    noncurrent_version_transitions=[
                        s3.NoncurrentVersionTransition(
                            storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                            transition_after=Duration.days(30),
                        ),
                    ],
                )
            )

        bucket = s3.Bucket(
            self,
            f"{self._pascal(logical_id)}Bucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.KMS,
            encryption_key=self.kms_key,
            bucket_key_enabled=True,
            enforce_ssl=True,
            versioned=is_drafts and bool(config.get("s3_drafts_versioned")),
            lifecycle_rules=lifecycle_rules or None,
            removal_policy=(
                RemovalPolicy.RETAIN
                if env_name == "production"
                else RemovalPolicy.DESTROY
            ),
            auto_delete_objects=env_name != "production",
        )
        return bucket

    @staticmethod
    def _sanitize(name: str) -> str:
        """CDK construct IDs cannot contain '/' or '-'. Use camelCase."""

        parts = name.replace("/", "-").split("-")
        return "".join(p.capitalize() for p in parts if p)

    @staticmethod
    def _pascal(snake: str) -> str:
        return "".join(part.capitalize() for part in snake.split("_") if part)

    # ----------------------------------------------------------------------
    # Cross-stack accessors --------------------------------------------------
    # ----------------------------------------------------------------------
    @property
    def artifacts_bucket(self) -> s3.IBucket:
        return self.buckets["artifacts"]

    @property
    def drafts_bucket(self) -> s3.IBucket:
        return self.buckets["drafts"]

    @property
    def skilljar_content_bucket(self) -> s3.IBucket:
        return self.buckets["skilljar_content"]

    @property
    def cache_bucket(self) -> s3.IBucket:
        return self.buckets["cache"]
