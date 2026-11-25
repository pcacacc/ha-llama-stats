"""Pure calculation and parsing helpers (no Home Assistant dependency, unit-testable)."""

from __future__ import annotations

import re

LOG_TS_RE = re.compile(r"^\[(.*?)\]")
PROMPT_EVAL_RE = re.compile(r"prompt eval time = .*? /\s*(\d+) tokens")
EVAL_TIME_RE = re.compile(r"(?<!prompt )eval time = .*? /\s*(\d+) tokens")


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


def parse_log_lines(lines: list[str]) -> dict[str, int | str]:
    """Parse docker log lines (docker logs -t) into token counts per window."""
    input_tokens = 0
    gen_tokens = 0
    requests = 0
    last_timestamp = ""
    for line in lines:
        ts_match = LOG_TS_RE.match(line)
        if ts_match:
            last_timestamp = max(last_timestamp, ts_match.group(1))
        prompt_match = PROMPT_EVAL_RE.search(line)
        if prompt_match:
            input_tokens += int(prompt_match.group(1))
            requests += 1
            continue
        gen_match = EVAL_TIME_RE.search(line)
        if gen_match:
            gen_tokens += int(gen_match.group(1))
    return {
        "input_tokens": input_tokens,
        "gen_tokens": gen_tokens,
        "requests": requests,
        "last_timestamp": last_timestamp,
    }
