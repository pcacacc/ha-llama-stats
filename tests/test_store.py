"""Tests for the JSON store."""

from conftest import store


def test_snapshot_and_totals(tmp_path):
    s = store.StatsStore(str(tmp_path / "stats.json"))
    month = s.get_month("2026-11")
    month.add_snapshot(1_000, 2_000, 0.15)
    month.add_snapshot(1_500, 3_000, 0.22)

    assert len(month.snapshots) == 2
    assert month.input_tokens == 1_500
    assert month.gen_tokens == 3_000
    assert month.total_tokens == 4_500
    assert month.total_cost == 0.22


def test_save_load_roundtrip(tmp_path):
    path = str(tmp_path / "stats.json")
    s = store.StatsStore(path)
    s.get_month("2026-10").add_snapshot(100, 200, 0.01)
    s.save()

    s2 = store.StatsStore(path)
    s2.load()
    loaded = s2.get_month("2026-10")
    assert loaded.input_tokens == 100
    assert loaded.snapshots[0]["cost"] == 0.01
    assert len(s2.all_months()) == 1


def test_month_key_format():
    key = store.MonthlyStats.month_key()
    assert len(key) == 7
    assert key.count("-") == 1
