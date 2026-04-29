"""Observability stack: CloudWatch dashboards, metric filters, alarms.

Per plan section 6 ("Cost guardrails") and the verification plan, we need:

* RDS health alarms (CPU, free storage).
* Fargate task failure alarm.
* App Runner 5xx-rate alarm.
* AWS Budgets monthly cost alarm at the env-specific dollar threshold.
* CloudWatch metric filter on the worker log group that converts
  ``RunCostMeter`` cost-ceiling-exceeded log lines into a metric, and
  alarms on it.
* A CloudWatch dashboard collecting the above so on-call has a one-stop
  view.

Alarm notifications go to a single SNS topic per env. IT subscribes the
team's email distribution list to that topic post-deploy (the email
endpoint is intentionally not in CDK so an unsubscribe by one human
does not require a re-deploy).
"""

from __future__ import annotations

from typing import Any, Dict

from aws_cdk import Duration, Stack, Tags
from aws_cdk import aws_apprunner as apprunner
from aws_cdk import aws_budgets as budgets
from aws_cdk import aws_cloudwatch as cw
from aws_cdk import aws_cloudwatch_actions as cw_actions
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_logs as logs
from aws_cdk import aws_rds as rds
from aws_cdk import aws_sns as sns
from constructs import Construct


class ObservabilityStack(Stack):
    """CloudWatch alarms + dashboards + budget."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        config: Dict[str, Any],
        rds_instance: rds.IDatabaseInstance,
        fargate_cluster: ecs.ICluster,
        app_runner_service: apprunner.CfnService,
        worker_log_group: logs.ILogGroup,
        web_log_group: logs.ILogGroup,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        for tag_key, tag_value in config["tags"].items():
            Tags.of(self).add(tag_key, tag_value)

        env_name: str = config["env_name"]

        # ------------------------------------------------------------------
        # SNS notification topic ------------------------------------------
        # ------------------------------------------------------------------
        self.alarm_topic = sns.Topic(
            self,
            "AlarmTopic",
            topic_name=f"fme-train-{env_name}-alarms",
            display_name=f"FME Training Automation alarms ({env_name})",
        )
        alarm_action = cw_actions.SnsAction(self.alarm_topic)

        # ------------------------------------------------------------------
        # Metric filter: RunCostMeter cost-ceiling exceeded ----------------
        # ------------------------------------------------------------------
        # Worker emits a structured log line:
        #   "RUN_COST_CEILING_EXCEEDED run_id=... projected_usd=..."
        # The metric is incremented per occurrence.
        cost_ceiling_metric = logs.MetricFilter(
            self,
            "CostCeilingMetricFilter",
            log_group=worker_log_group,
            metric_namespace="FmeTrain",
            metric_name=f"CostCeilingExceeded-{env_name}",
            filter_pattern=logs.FilterPattern.literal(
                '"RUN_COST_CEILING_EXCEEDED"'
            ),
            metric_value="1",
            default_value=0,
        )

        cost_ceiling_alarm = cw.Alarm(
            self,
            "CostCeilingAlarm",
            metric=cost_ceiling_metric.metric(
                statistic="Sum",
                period=Duration.minutes(5),
            ),
            evaluation_periods=1,
            threshold=1,
            comparison_operator=(
                cw.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD
            ),
            alarm_description=(
                "A run hit the per-run OpenAI cost ceiling and aborted."
            ),
            treat_missing_data=cw.TreatMissingData.NOT_BREACHING,
        )
        cost_ceiling_alarm.add_alarm_action(alarm_action)

        # ------------------------------------------------------------------
        # RDS alarms -------------------------------------------------------
        # ------------------------------------------------------------------
        rds_cpu_alarm = cw.Alarm(
            self,
            "RdsCpuAlarm",
            metric=rds_instance.metric_cpu_utilization(
                period=Duration.minutes(5),
                statistic="Average",
            ),
            threshold=int(config["alarm_rds_cpu_threshold_pct"]),
            evaluation_periods=3,
            comparison_operator=(
                cw.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD
            ),
            alarm_description="RDS CPU sustained above threshold.",
            treat_missing_data=cw.TreatMissingData.NOT_BREACHING,
        )
        rds_cpu_alarm.add_alarm_action(alarm_action)

        free_storage_threshold_bytes = (
            int(config["alarm_rds_free_storage_threshold_gb"])
            * 1024 * 1024 * 1024
        )
        rds_storage_alarm = cw.Alarm(
            self,
            "RdsFreeStorageAlarm",
            metric=rds_instance.metric_free_storage_space(
                period=Duration.minutes(5),
                statistic="Minimum",
            ),
            threshold=free_storage_threshold_bytes,
            evaluation_periods=3,
            comparison_operator=cw.ComparisonOperator.LESS_THAN_THRESHOLD,
            alarm_description="RDS free storage low.",
            treat_missing_data=cw.TreatMissingData.NOT_BREACHING,
        )
        rds_storage_alarm.add_alarm_action(alarm_action)

        # ------------------------------------------------------------------
        # Fargate task failure alarm --------------------------------------
        # ------------------------------------------------------------------
        # ECS publishes ``CPUUtilization`` etc, but for failures we look at
        # the AWS/ECS namespace's ``CPUReservation`` is not the right
        # signal. Use the AWS/ECS ServiceName-less cluster metric
        # ``MemoryUtilization`` is also wrong. The standard pattern is a
        # custom log-based metric (we already have one for cost ceiling);
        # for "task exited non-zero", the worker is expected to log
        # ``WORKER_FATAL`` before exiting.
        worker_fatal_metric = logs.MetricFilter(
            self,
            "WorkerFatalMetricFilter",
            log_group=worker_log_group,
            metric_namespace="FmeTrain",
            metric_name=f"WorkerFatal-{env_name}",
            filter_pattern=logs.FilterPattern.literal('"WORKER_FATAL"'),
            metric_value="1",
            default_value=0,
        )
        fargate_failed_alarm = cw.Alarm(
            self,
            "FargateFailuresAlarm",
            metric=worker_fatal_metric.metric(
                statistic="Sum",
                period=Duration.minutes(15),
            ),
            threshold=int(
                config["alarm_fargate_failed_tasks_threshold_per_15min"]
            ),
            evaluation_periods=1,
            comparison_operator=(
                cw.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD
            ),
            alarm_description="Fargate worker fatal-error rate exceeded.",
            treat_missing_data=cw.TreatMissingData.NOT_BREACHING,
        )
        fargate_failed_alarm.add_alarm_action(alarm_action)

        # ------------------------------------------------------------------
        # App Runner 5xx alarm ---------------------------------------------
        # ------------------------------------------------------------------
        # App Runner exposes 5XXStatusResponse as a CloudWatch metric on
        # the AWS/AppRunner namespace.
        app_runner_5xx_metric = cw.Metric(
            namespace="AWS/AppRunner",
            metric_name="5xxStatusResponse",
            dimensions_map={
                "ServiceName": app_runner_service.service_name,  # type: ignore[arg-type]
            },
            statistic="Sum",
            period=Duration.minutes(5),
        )
        app_runner_5xx_alarm = cw.Alarm(
            self,
            "AppRunner5xxAlarm",
            metric=app_runner_5xx_metric,
            threshold=int(
                config["alarm_app_runner_5xx_threshold_per_5min"]
            ),
            evaluation_periods=1,
            comparison_operator=(
                cw.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD
            ),
            alarm_description="App Runner 5xx rate spiked.",
            treat_missing_data=cw.TreatMissingData.NOT_BREACHING,
        )
        app_runner_5xx_alarm.add_alarm_action(alarm_action)

        # ------------------------------------------------------------------
        # AWS Budget alarm -------------------------------------------------
        # ------------------------------------------------------------------
        # Per plan section 6: $150/mo (prod), $75/mo (staging).
        budgets.CfnBudget(
            self,
            "MonthlyBudget",
            budget=budgets.CfnBudget.BudgetDataProperty(
                budget_name=f"fme-train-{env_name}-monthly",
                budget_type="COST",
                time_unit="MONTHLY",
                budget_limit=budgets.CfnBudget.SpendProperty(
                    amount=int(config["monthly_budget_usd"]),
                    unit="USD",
                ),
                cost_filters={
                    # Tag-based filtering — every CDK-managed resource is
                    # tagged Project=fme-training-automation Environment=<env>.
                    "TagKeyValue": [
                        f"user:Project${'$'}fme-training-automation",
                        f"user:Environment${'$'}{env_name}",
                    ],
                },
            ),
            notifications_with_subscribers=[
                budgets.CfnBudget.NotificationWithSubscribersProperty(
                    notification=budgets.CfnBudget.NotificationProperty(
                        comparison_operator="GREATER_THAN",
                        notification_type="ACTUAL",
                        threshold=80,
                        threshold_type="PERCENTAGE",
                    ),
                    subscribers=[
                        budgets.CfnBudget.SubscriberProperty(
                            address=self.alarm_topic.topic_arn,
                            subscription_type="SNS",
                        ),
                    ],
                ),
                budgets.CfnBudget.NotificationWithSubscribersProperty(
                    notification=budgets.CfnBudget.NotificationProperty(
                        comparison_operator="GREATER_THAN",
                        notification_type="FORECASTED",
                        threshold=100,
                        threshold_type="PERCENTAGE",
                    ),
                    subscribers=[
                        budgets.CfnBudget.SubscriberProperty(
                            address=self.alarm_topic.topic_arn,
                            subscription_type="SNS",
                        ),
                    ],
                ),
            ],
        )

        # ------------------------------------------------------------------
        # Dashboard --------------------------------------------------------
        # ------------------------------------------------------------------
        dashboard = cw.Dashboard(
            self,
            "Dashboard",
            dashboard_name=f"fme-train-{env_name}",
        )
        dashboard.add_widgets(
            cw.GraphWidget(
                title="App Runner — request rate / 5xx",
                left=[
                    cw.Metric(
                        namespace="AWS/AppRunner",
                        metric_name="RequestCount",
                        dimensions_map={
                            "ServiceName": app_runner_service.service_name,  # type: ignore[arg-type]
                        },
                        statistic="Sum",
                        period=Duration.minutes(5),
                    ),
                ],
                right=[app_runner_5xx_metric],
                width=12,
            ),
            cw.GraphWidget(
                title="RDS — CPU + free storage",
                left=[
                    rds_instance.metric_cpu_utilization(
                        period=Duration.minutes(5),
                    ),
                ],
                right=[
                    rds_instance.metric_free_storage_space(
                        period=Duration.minutes(5),
                    ),
                ],
                width=12,
            ),
            cw.GraphWidget(
                title="Worker — cost-ceiling + fatal counts",
                left=[
                    cost_ceiling_metric.metric(
                        statistic="Sum",
                        period=Duration.minutes(15),
                    ),
                    worker_fatal_metric.metric(
                        statistic="Sum",
                        period=Duration.minutes(15),
                    ),
                ],
                width=12,
            ),
        )
