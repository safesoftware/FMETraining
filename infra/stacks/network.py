"""Network stack: VPC, subnets, security groups.

Per plan section 1 the app runs entirely inside a small VPC:

* Two private subnets across two AZs (durability without paying for
  multi-AZ RDS).
* One public subnet per AZ for the NAT gateways (egress to OpenAI, Jira,
  Skilljar, Skilljar's public S3).
* Single NAT gateway for staging/prod (cost-conscious; the team is 2-5
  users so a second NAT does not pay for itself).

Security groups:

* ``app_runner_sg``        - attached to the App Runner VPC connector.
* ``fargate_sg``           - attached to Fargate run-task ENIs.
* ``rds_sg``               - attached to the RDS instance. Ingress
  allowed only from ``app_runner_sg`` and ``fargate_sg`` on 5432.
* All compute SGs allow egress to the world (App Runner / Fargate need
  to reach OpenAI / Jira / Skilljar over the public internet).

The RDS SG is intentionally *not* internet-egress permissive: the DB
should only ever talk to the App Runner / Fargate consumers.
"""

from __future__ import annotations

from typing import Any, Dict

from aws_cdk import Stack, Tags
from aws_cdk import aws_ec2 as ec2
from constructs import Construct


class NetworkStack(Stack):
    """VPC, subnets, security groups, NAT gateway."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        config: Dict[str, Any],
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        for tag_key, tag_value in config["tags"].items():
            Tags.of(self).add(tag_key, tag_value)

        # ------------------------------------------------------------------
        # VPC
        # ------------------------------------------------------------------
        # Two AZs, /20 supernet split into /24 subnets. Public subnets host
        # the NAT gateway(s); private (with egress) host RDS, the App Runner
        # VPC connector ENIs, and Fargate task ENIs.
        self.vpc = ec2.Vpc(
            self,
            "Vpc",
            ip_addresses=ec2.IpAddresses.cidr(config["vpc_cidr"]),
            max_azs=int(config["az_count"]),
            nat_gateways=int(config["nat_gateways"]),
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="Isolated",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24,
                ),
            ],
            # Enable DNS — required for App Runner VPC connector and for
            # SecretsManager VPC interface endpoint resolution.
            enable_dns_hostnames=True,
            enable_dns_support=True,
        )

        # ------------------------------------------------------------------
        # Security groups
        # ------------------------------------------------------------------
        self.app_runner_sg = ec2.SecurityGroup(
            self,
            "AppRunnerSg",
            vpc=self.vpc,
            description="App Runner VPC connector ENIs (FastAPI web/api).",
            allow_all_outbound=True,
        )

        self.fargate_sg = ec2.SecurityGroup(
            self,
            "FargateSg",
            vpc=self.vpc,
            description="Fargate run-task ENIs (pipeline worker).",
            allow_all_outbound=True,
        )

        self.rds_sg = ec2.SecurityGroup(
            self,
            "RdsSg",
            vpc=self.vpc,
            description="RDS Postgres — ingress only from app/worker SGs.",
            allow_all_outbound=False,
        )

        # 5432 from App Runner connector and Fargate worker only.
        self.rds_sg.add_ingress_rule(
            peer=self.app_runner_sg,
            connection=ec2.Port.tcp(5432),
            description="Postgres from App Runner VPC connector",
        )
        self.rds_sg.add_ingress_rule(
            peer=self.fargate_sg,
            connection=ec2.Port.tcp(5432),
            description="Postgres from Fargate worker",
        )

    # ----------------------------------------------------------------------
    # Convenience accessors used by sibling stacks (compute / data).
    # ----------------------------------------------------------------------
    @property
    def private_subnets(self) -> list[ec2.ISubnet]:
        """Subnets where stateful + compute resources live."""

        return self.vpc.select_subnets(
            subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
        ).subnets
