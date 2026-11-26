"""Tests for cost calculation and log parsing."""

from conftest import util

SAMPLE_LOG = [
    "2026-11-25T16:31:32.824Z prompt eval time = 2159.35 ms /  6796 tokens",
    "2026-11-25T16:31:32.828Z        eval time = 56699.03 ms /  5369 tokens",
    "2026-11-25T16:31:32.828Z       total time = 58858.37 ms / 12165 tokens",
    "2026-11-25T16:31:30.100Z prompt eval time = 100.00 ms /   120 tokens",
    "2026-11-25T16:31:31.200Z        eval time = 1200.00 ms /   200 tokens",
]

SAMPLE_LOG_CACHED = [
    "2026-11-25T16:31:32.828Z prompt eval time = 100 ms / 1000 tokens (500 reused, 500 read)",
]


def test_openrouter_prices():
    cost = util.calculate_cost(1_750_531, 11_614_683, 0.05, 0.70)
    assert cost == round((1.750531 * 0.05) + (11.614683 * 0.70), 6)


def test_zero_tokens():
    assert util.calculate_cost(0, 0, 0.05, 0.70) == 0.0


def test_cached_cost():
    cost = util.calculate_cost(1000, 1000, 10, 10, 1000, 5)
    assert cost == 0.015


def test_parse_log_lines():
    parsed = util.parse_log_lines(SAMPLE_LOG)
    assert parsed["input_tokens"] == 6796 + 120
    assert parsed["cached_tokens"] == 0
    assert parsed["gen_tokens"] == 5369 + 200
    assert parsed["requests"] == 2
    assert parsed["last_timestamp"] == "2026-11-25T16:31:32.828Z"


def test_parse_log_lines_cached():
    parsed = util.parse_log_lines(SAMPLE_LOG_CACHED)
    assert parsed["input_tokens"] == 1000
    assert parsed["cached_tokens"] == 500
    assert parsed["requests"] == 1


def test_parse_empty():
    parsed = util.parse_log_lines([])
    assert parsed["input_tokens"] == 0
    assert parsed["last_timestamp"] == ""


SAMPLE_STRATA = [
    "strata serve: prompt 58451 tokens = 58078 reused + 373 read in 3061 ms (121.9 tok/s), "
    "581 generated in 16678 ms (34.8 tok/s), drafts accepted 360 of 521, 6 checkpoints",
    "strata serve: conversation cache: the reply this request replaces is not parked "
    "(585 tokens past the turn checkpoint at 58446)",
    "strata serve: prompt 59097 tokens = 58446 reused + 651 read in 3021 ms (215.5 tok/s), "
    "223 generated in 4753 ms (46.9 tok/s), drafts accepted 135 of 210, 6 checkpoints",
]


def test_parse_strata_lines():
    parsed = util.parse_strata_lines(SAMPLE_STRATA)
    assert parsed["input_tokens"] == 58451 + 59097
    assert parsed["cached_tokens"] == 58078 + 58446
    assert parsed["gen_tokens"] == 581 + 223
    assert parsed["requests"] == 2


def test_parse_gpu_metrics():
    parsed, total = util.parse_gpu_metrics(
        [
            {"id": "card1", "label": "GPU card1", "bus": "0000:03:00.0", "power_watts": 11.0},
            {"id": "card2", "label": "GPU card2", "bus": "0000:08:00.0", "power_watts": 58.0},
        ]
    )
    assert total == 69.0
    assert parsed == [
        {"id": "card1", "label": "GPU card1", "bus": "0000:03:00.0", "power_watts": 11.0},
        {"id": "card2", "label": "GPU card2", "bus": "0000:08:00.0", "power_watts": 58.0},
    ]
