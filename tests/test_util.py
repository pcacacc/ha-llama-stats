"""Tests for cost calculation and log parsing."""

from conftest import util

SAMPLE_LOG = [
    "[2026-11-25T16:31:32.824Z] prompt eval time = 2159.35 ms /  6796 tokens",
    "[2026-11-25T16:31:32.828Z]        eval time = 56699.03 ms /  5369 tokens",
    "[2026-11-25T16:31:32.828Z]       total time = 58858.37 ms / 12165 tokens",
    "[2026-11-25T16:31:30.100Z] prompt eval time = 100.00 ms /   120 tokens",
    "[2026-11-25T16:31:31.200Z]        eval time = 1200.00 ms /   200 tokens",
]


def test_openrouter_prices():
    cost = util.calculate_cost(1_750_531, 11_614_683, 0.05, 0.70)
    assert cost == round((1.750531 * 0.05) + (11.614683 * 0.70), 6)


def test_zero_tokens():
    assert util.calculate_cost(0, 0, 0.05, 0.70) == 0.0


def test_parse_log_lines():
    parsed = util.parse_log_lines(SAMPLE_LOG)
    assert parsed["input_tokens"] == 6796 + 120
    assert parsed["gen_tokens"] == 5369 + 200
    assert parsed["requests"] == 2
    assert parsed["last_timestamp"] == "2026-11-25T16:31:32.828Z"


def test_parse_empty():
    parsed = util.parse_log_lines([])
    assert parsed["input_tokens"] == 0
    assert parsed["last_timestamp"] == ""
