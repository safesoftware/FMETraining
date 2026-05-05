"""Unit tests for RunCostMeter — the per-run OpenAI cost guard.

The math is small but easy to get wrong (off-by-1M, in/out price swap),
so each branch of the meter has a focused test.
"""

from __future__ import annotations

import pytest

from app.services.run_cost_meter import (
    DEFAULT_PRICES_USD_PER_M_TOKENS,
    CostCeilingExceeded,
    RunCostMeter,
)


# ---- pricing math ---------------------------------------------------------

def test_total_cost_zero_when_no_calls() -> None:
    meter = RunCostMeter(ceiling_usd=50.0)
    assert meter.total_cost_usd() == 0.0


def test_record_usage_uses_correct_input_and_output_prices() -> None:
    """gpt-4o-mini is $0.15 in / $0.60 out per 1M tokens."""
    meter = RunCostMeter(ceiling_usd=50.0)
    meter.record_usage(model="gpt-4o-mini", prompt_tokens=1_000_000, completion_tokens=500_000)
    # 1M in @ $0.15 = $0.15
    # 500k out @ $0.60/M = $0.30
    # total = $0.45
    assert meter.total_cost_usd() == pytest.approx(0.45)


def test_unknown_model_falls_back_to_gpt4o_pricing() -> None:
    """Unknown model names price at gpt-4o so we err on the side of aborting early."""
    meter = RunCostMeter(ceiling_usd=50.0)
    meter.record_usage(model="future-model-9000", prompt_tokens=1_000_000, completion_tokens=0)
    # gpt-4o is $2.50/M in
    assert meter.total_cost_usd() == pytest.approx(2.50)


def test_per_model_costs_aggregate_in_total() -> None:
    meter = RunCostMeter(ceiling_usd=50.0)
    meter.record_usage(model="gpt-4o-mini", prompt_tokens=1_000_000, completion_tokens=0)  # $0.15
    meter.record_usage(model="gpt-4o", prompt_tokens=100_000, completion_tokens=0)         # $0.25
    assert meter.total_cost_usd() == pytest.approx(0.40)


# ---- enforcement ---------------------------------------------------------

def test_check_before_call_passes_when_under_ceiling() -> None:
    meter = RunCostMeter(ceiling_usd=10.0)
    # Should not raise.
    meter.check_before_call(
        model="gpt-4o-mini", expected_input_tokens=1_000_000, expected_output_tokens=0
    )


def test_check_before_call_raises_when_projected_exceeds_ceiling() -> None:
    """A single very large projected call must trip the check."""
    meter = RunCostMeter(ceiling_usd=0.10)  # $0.10 cap
    with pytest.raises(CostCeilingExceeded) as exc_info:
        meter.check_before_call(
            model="gpt-4o", expected_input_tokens=1_000_000, expected_output_tokens=0
        )  # would cost $2.50 — way over $0.10
    assert "would exceed ceiling" in str(exc_info.value)


def test_check_before_call_raises_when_already_at_ceiling() -> None:
    """Running tally is what matters — not just the projected next call alone."""
    meter = RunCostMeter(ceiling_usd=0.50)
    # Push up to nearly the ceiling
    meter.record_usage(model="gpt-4o-mini", prompt_tokens=2_000_000, completion_tokens=400_000)
    # 2M in @ $0.15 + 400k out @ $0.60/M = $0.30 + $0.24 = $0.54  →  already over!
    # Even a small next call should trip the guard.
    with pytest.raises(CostCeilingExceeded):
        meter.check_before_call(
            model="gpt-4o-mini", expected_input_tokens=100, expected_output_tokens=10
        )


def test_negative_tokens_rejected() -> None:
    meter = RunCostMeter(ceiling_usd=50.0)
    with pytest.raises(ValueError):
        meter.record_usage(model="gpt-4o-mini", prompt_tokens=-1, completion_tokens=0)
    with pytest.raises(ValueError):
        meter.record_usage(model="gpt-4o-mini", prompt_tokens=0, completion_tokens=-1)


# ---- snapshot / reporting ------------------------------------------------

def test_snapshot_shape() -> None:
    meter = RunCostMeter(ceiling_usd=10.0)
    meter.record_usage(model="gpt-4o-mini", prompt_tokens=1500, completion_tokens=150)
    meter.record_usage(model="gpt-4o-mini", prompt_tokens=1500, completion_tokens=150)
    meter.record_usage(model="gpt-4o", prompt_tokens=10_000, completion_tokens=800)

    snap = meter.snapshot()

    assert snap["ceiling_usd"] == 10.0
    assert "by_model" in snap
    assert set(snap["by_model"]) == {"gpt-4o-mini", "gpt-4o"}
    assert snap["by_model"]["gpt-4o-mini"]["call_count"] == 2
    assert snap["by_model"]["gpt-4o-mini"]["prompt_tokens"] == 3000
    assert snap["by_model"]["gpt-4o-mini"]["completion_tokens"] == 300
    assert snap["by_model"]["gpt-4o"]["call_count"] == 1
    assert snap["total_cost_usd"] > 0


def test_snapshot_is_json_serialisable() -> None:
    """The snapshot lands in run_steps.token_usage_json (a JSONB column)."""
    import json
    meter = RunCostMeter(ceiling_usd=50.0)
    meter.record_usage(model="gpt-4o-mini", prompt_tokens=42, completion_tokens=7)
    json.dumps(meter.snapshot())  # must not raise


# ---- price table sanity --------------------------------------------------

def test_default_price_table_has_known_models() -> None:
    """Lock in that the models the pipeline currently uses are priced."""
    assert "gpt-4o" in DEFAULT_PRICES_USD_PER_M_TOKENS
    assert "gpt-4o-mini" in DEFAULT_PRICES_USD_PER_M_TOKENS


def test_custom_prices_override_defaults() -> None:
    meter = RunCostMeter(
        ceiling_usd=10.0,
        prices={"gpt-4o-mini": (1.00, 1.00), "gpt-4o": (1.00, 1.00)},
    )
    meter.record_usage(model="gpt-4o-mini", prompt_tokens=1_000_000, completion_tokens=0)
    # With overridden price of $1/M, 1M tokens = $1.00 (vs the default $0.15)
    assert meter.total_cost_usd() == pytest.approx(1.00)
