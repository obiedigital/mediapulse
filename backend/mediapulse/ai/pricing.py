"""Per-model $/Mtok pricing for cost logging on `Classification` rows.

Matched by prefix (`claude-opus-*`, `claude-sonnet-*`, `claude-haiku-*`)
rather than exact model string, since date-suffixed model ids change more
often than relative tier pricing does. Figures are approximate published
list prices and will drift — treat `cost_usd` as directional for budget
tracking, not an invoice reconciliation figure. An unrecognized model
returns `None` rather than a guessed number, so a cost report can
distinguish "known to be cheap" from "we don't actually know".
"""
from __future__ import annotations

# (input $ per million tokens, output $ per million tokens)
_TIER_PRICING_USD_PER_MTOK: dict[str, tuple[float, float]] = {
    "claude-opus": (15.0, 75.0),
    "claude-sonnet": (3.0, 15.0),
    "claude-haiku": (0.80, 4.0),
}


def estimate_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float | None:
    for prefix, (input_price, output_price) in _TIER_PRICING_USD_PER_MTOK.items():
        if model.startswith(prefix):
            return (input_tokens * input_price + output_tokens * output_price) / 1_000_000
    return None
