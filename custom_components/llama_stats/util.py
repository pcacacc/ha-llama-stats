"""Pure calculation helpers (no Home Assistant dependency, unit-testable)."""

from __future__ import annotations


def calculate_cost(
    input_tokens: int,
    gen_tokens: int,
    input_price_per_million: float,
    output_price_per_million: float,
) -> float:
    """Calculate cost in USD for the given token counts."""
    return round(
        (input_tokens / 1_000_000) * input_price_per_million
        + (gen_tokens / 1_000_000) * output_price_per_million,
        6,
    )
