"""Tests for the monthly statistics model."""

from conftest import store


def test_window_accumulation():
    month = store.MonthlyStats(month="2026-11")
    month.add_window(1_000, 2_000, 2, 0.15)
    month.add_window(500, 1_000, 1, 0.07)

    assert month.input_tokens == 1_500
    assert month.gen_tokens == 3_000
    assert month.total_tokens == 4_500
    assert month.total_cost == 0.22
    assert month.requests == 3

    month.add_window(0, 0, 0, 0.0)
    assert month.requests == 3


def test_month_key_format():
    key = store.MonthlyStats.month_key()
    assert len(key) == 7
    assert key.count("-") == 1
