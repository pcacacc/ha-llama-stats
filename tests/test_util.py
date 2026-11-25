"""Tests for cost calculation."""

from conftest import util


def test_openrouter_prices():
    # 1.75M input at $0.05/M + 11.6M gen at $0.70/M
    cost = util.calculate_cost(1_750_531, 11_614_683, 0.05, 0.70)
    assert cost == round((1.750531 * 0.05) + (11.614683 * 0.70), 6)


def test_zero_tokens():
    assert util.calculate_cost(0, 0, 0.05, 0.70) == 0.0
