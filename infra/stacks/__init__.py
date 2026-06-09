"""CDK stacks for the FME Training Automation multi-user web app.

Each stack maps to a layer of the architecture described in
``docs/plans/2026-04-29-multi-user-web-app.md``:

* :mod:`infra.stacks.network` — VPC + security groups + NAT.
* :mod:`infra.stacks.data` — RDS Postgres + S3 buckets + KMS + Secrets refs.
* :mod:`infra.stacks.compute` — App Runner + ECR + Fargate task def + IAM.
* :mod:`infra.stacks.observability` — CloudWatch logs / metrics / alarms.

The stacks expose their cross-stack contracts as attributes on the stack
class (rather than via `CfnOutput` lookups) so the CDK app can wire them
together explicitly without runtime resolution.
"""

from .compute import ComputeStack
from .data import DataStack
from .network import NetworkStack
from .observability import ObservabilityStack

__all__ = [
    "ComputeStack",
    "DataStack",
    "NetworkStack",
    "ObservabilityStack",
]
