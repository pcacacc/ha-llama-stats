"""Pure calculation and parsing helpers (no Home Assistant dependency, unit-testable)."""

from __future__ import annotations

import re
from typing import Any

LOG_TS_RE = re.compile(r"^\[?(\d{4}-\d{2}-\d{2}T[\d:.]+Z)\]?")
PROMPT_EVAL_RE = re.compile(
    r"prompt eval time = .*? /\s*(\d+) tokens(?: \(\s*(\d+) reused,)?",
    re.IGNORECASE,
)
EVAL_TIME_RE = re.compile(r"(?<!prompt )eval time = .*? /\s*(\d+) tokens")
STRATA_PROMPT_RE = re.compile(
    r"prompt (\d+) tokens(?: = (\d+) reused \+ (\d+) read)?",
    re.IGNORECASE,
)
STRATA_GEN_RE = re.compile(r"(\d+) generated")


def calculate_cost(
    input_tokens: int,
    gen_tokens: int,
    input_price_per_million: float,
    output_price_per_million: float,
    cached_tokens: int = 0,
    cached_price_per_million: float = 0.0,
) -> float:
    """Calculate cost for token counts; cached input tokens use the lower price."""
    cached = max(0, min(int(cached_tokens), int(input_tokens)))
    noncached = input_tokens - cached
    return round(
        (noncached / 1_000_000) * input_price_per_million
        + (cached / 1_000_000) * cached_price_per_million
        + (gen_tokens / 1_000_000) * output_price_per_million,
        6,
    )


def parse_log_lines(lines: list[str]) -> dict[str, int | str]:
    """Parse docker log lines (docker logs -t) into token counts per window."""
    input_tokens = 0
    cached_tokens = 0
    gen_tokens = 0
    requests = 0
    last_timestamp = ""
    for line in lines:
        ts_match = LOG_TS_RE.match(line)
        if ts_match:
            last_timestamp = max(last_timestamp, ts_match.group(1))
        prompt_match = PROMPT_EVAL_RE.search(line)
        if prompt_match:
            prompt_tokens = int(prompt_match.group(1))
            input_tokens += prompt_tokens
            if prompt_match.group(2):
                cached_tokens += min(int(prompt_match.group(2)), prompt_tokens)
            requests += 1
            continue
        gen_match = EVAL_TIME_RE.search(line)
        if gen_match:
            gen_tokens += int(gen_match.group(1))
    return {
        "input_tokens": input_tokens,
        "cached_tokens": cached_tokens,
        "gen_tokens": gen_tokens,
        "requests": requests,
        "last_timestamp": last_timestamp,
    }


def parse_strata_lines(lines: list[str]) -> dict[str, int]:
    """Parse strata engine log lines into token counts per window.

    Full prompt tokens are counted as input; explicit reused tokens are cached input.
    """
    input_tokens = 0
    cached_tokens = 0
    gen_tokens = 0
    requests = 0
    for line in lines:
        prompt_match = STRATA_PROMPT_RE.search(line)
        if prompt_match:
            prompt_tokens = int(prompt_match.group(1))
            input_tokens += prompt_tokens
            if prompt_match.group(2):
                cached_tokens += min(int(prompt_match.group(2)), prompt_tokens)
            requests += 1
            gen_match = STRATA_GEN_RE.search(line)
            if gen_match:
                gen_tokens += int(gen_match.group(1))
    return {
        "input_tokens": input_tokens,
        "cached_tokens": cached_tokens,
        "gen_tokens": gen_tokens,
        "requests": requests,
    }


def parse_gpu_metrics(gpus: Any) -> tuple[list[dict[str, Any]], float]:
    """Parse plugin GPU power data into parsed GPU records and total watts."""
    if not isinstance(gpus, list):
        return 0.0, []

    parsed: list[dict[str, Any]] = []
    total = 0.0
    for gpu in gpus:
        power = float(gpu.get("power_watts", 0.0))
        parsed.append(
            {
                "id": str(gpu.get("id", "")),
                "label": str(gpu.get("label", "")),
                "bus": str(gpu.get("bus", "")),
                "power_watts": round(power, 2),
            }
        )
        total += power

    return parsed, round(total, 2)
