"""Per-run OpenAI cost accumulator and ceiling enforcer.

Plan section 3: a ``RunCostMeter`` accumulates ``prompt_tokens`` +
``completion_tokens`` from every OpenAI response (already tracked in
``pipeline/assessment.py`` and ``pipeline/edit_suggestions.py``), prices
them against a model→$/M-token table, and aborts before the next OpenAI
call if the projected total exceeds ``max_run_usd``.

Status string ``aborted_cost_ceiling`` is what the worker writes back
to ``runs.status`` when this fires.

The meter is intentionally synchronous — the pipeline code that calls
into it is sync (legacy CLI), so wrapping it in async machinery would
just add overhead. Concurrency safety comes from the fact that a worker
runs one pipeline at a time; each ``RunCostMeter`` instance is owned by
one worker process.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


# Per-million-token prices in USD. Source: OpenAI public pricing as of 2026-05.
# Override at runtime via ``RunCostMeter(prices=...)`` if a model is missing
# or if you want test-deterministic prices.
DEFAULT_PRICES_USD_PER_M_TOKENS: Mapping[str, tuple[float, float]] = {
    # model name           (input, output) per 1M tokens
    "gpt-4o-mini":         (0.15, 0.60),
    "gpt-4o":              (2.50, 10.00),
    "gpt-4o-2024-08-06":   (2.50, 10.00),
    "gpt-4-turbo":         (10.00, 30.00),
}


class CostCeilingExceeded(Exception):
    """Raised by ``check_before_call`` when the projected cost would exceed
    the ceiling. The worker catches this, writes ``runs.status =
    'aborted_cost_ceiling'``, and exits cleanly."""


@dataclass
class _ModelTally:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    call_count: int = 0


@dataclass
class RunCostMeter:
    """Accumulates token usage and enforces a per-run dollar ceiling.

    Usage::

        meter = RunCostMeter(ceiling_usd=50.0)
        for pair in pairs:
            meter.check_before_call(model="gpt-4o-mini",
                                    expected_input_tokens=1500,
                                    expected_output_tokens=150)
            response = openai.chat.completions.create(...)
            meter.record_usage(model="gpt-4o-mini",
                               prompt_tokens=response.usage.prompt_tokens,
                               completion_tokens=response.usage.completion_tokens)
    """

    ceiling_usd: float
    prices: Mapping[str, tuple[float, float]] = field(
        default_factory=lambda: dict(DEFAULT_PRICES_USD_PER_M_TOKENS)
    )
    _tallies: dict[str, _ModelTally] = field(default_factory=dict, init=False, repr=False)

    # ---- recording -------------------------------------------------------

    def record_usage(self, *, model: str, prompt_tokens: int, completion_tokens: int) -> None:
        """Add observed tokens from a single OpenAI response."""
        if prompt_tokens < 0 or completion_tokens < 0:
            raise ValueError("token counts must be non-negative")
        tally = self._tallies.setdefault(model, _ModelTally())
        tally.prompt_tokens += prompt_tokens
        tally.completion_tokens += completion_tokens
        tally.call_count += 1

    # ---- pricing ---------------------------------------------------------

    def _price_pair(self, model: str) -> tuple[float, float]:
        """Return (input_$/M, output_$/M). Falls back to gpt-4o pricing for
        unknown models so an unexpected model name fails safe-high (we'd
        rather over-estimate and abort early than under-estimate and run away)."""
        return self.prices.get(model, self.prices.get("gpt-4o", (2.50, 10.00)))

    def _cost_for(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        in_price, out_price = self._price_pair(model)
        return (prompt_tokens / 1_000_000) * in_price + (
            completion_tokens / 1_000_000
        ) * out_price

    def total_cost_usd(self) -> float:
        """Total spent so far across all models."""
        total = 0.0
        for model, tally in self._tallies.items():
            total += self._cost_for(model, tally.prompt_tokens, tally.completion_tokens)
        return total

    def projected_cost_after_call(
        self,
        *,
        model: str,
        expected_input_tokens: int,
        expected_output_tokens: int,
    ) -> float:
        """What total_cost_usd() would be if the next call ran as estimated."""
        return self.total_cost_usd() + self._cost_for(
            model, expected_input_tokens, expected_output_tokens
        )

    # ---- enforcement -----------------------------------------------------

    def check_before_call(
        self,
        *,
        model: str,
        expected_input_tokens: int,
        expected_output_tokens: int,
    ) -> None:
        """Raise ``CostCeilingExceeded`` if the next call would push us over.

        The worker calls this *before* hitting OpenAI. If it raises, the
        caller skips the call, marks the run aborted, and exits.
        """
        projected = self.projected_cost_after_call(
            model=model,
            expected_input_tokens=expected_input_tokens,
            expected_output_tokens=expected_output_tokens,
        )
        if projected > self.ceiling_usd:
            raise CostCeilingExceeded(
                f"Projected total ${projected:.4f} would exceed ceiling "
                f"${self.ceiling_usd:.2f} (current total: "
                f"${self.total_cost_usd():.4f}, model={model}, "
                f"in={expected_input_tokens}, out={expected_output_tokens})"
            )

    # ---- reporting -------------------------------------------------------

    def snapshot(self) -> dict:
        """Return a JSON-serialisable summary suitable for ``run_steps.token_usage_json``."""
        return {
            "ceiling_usd": self.ceiling_usd,
            "total_cost_usd": round(self.total_cost_usd(), 6),
            "by_model": {
                model: {
                    "prompt_tokens": tally.prompt_tokens,
                    "completion_tokens": tally.completion_tokens,
                    "call_count": tally.call_count,
                    "cost_usd": round(
                        self._cost_for(
                            model, tally.prompt_tokens, tally.completion_tokens
                        ),
                        6,
                    ),
                }
                for model, tally in self._tallies.items()
            },
        }
