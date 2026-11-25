"""JSON-based storage for monthly statistics (HA-independent, unit-testable)."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime


@dataclass
class MonthlyStats:
    """Monthly token statistics."""

    month: str
    input_tokens: int = 0
    gen_tokens: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    last_updated: str = ""
    snapshots: list = field(default_factory=list)

    def add_snapshot(self, input_tokens: int, gen_tokens: int, cost: float) -> None:
        """Add a snapshot and update month totals."""
        now = datetime.now(UTC).isoformat()
        self.snapshots.append(
            {
                "timestamp": now,
                "input_tokens": input_tokens,
                "gen_tokens": gen_tokens,
                "total_tokens": input_tokens + gen_tokens,
                "cost": round(cost, 6),
            }
        )
        self.input_tokens = input_tokens
        self.gen_tokens = gen_tokens
        self.total_tokens = input_tokens + gen_tokens
        self.total_cost = round(cost, 6)
        self.last_updated = now

    def to_dict(self) -> dict:
        """Convert to a plain dict for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> MonthlyStats:
        """Create from a plain dict."""
        return cls(**data)

    @classmethod
    def month_key(cls, dt: datetime | None = None) -> str:
        """Return the YYYY-MM key for a timestamp (default: now, UTC)."""
        return (dt or datetime.now(UTC)).strftime("%Y-%m")


class StatsStore:
    """Persist monthly statistics as JSON."""

    def __init__(self, path: str):
        self.path = path
        self.monthly_stats: dict[str, MonthlyStats] = {}

    def load(self) -> None:
        """Load stats from the JSON file."""
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, encoding="utf-8") as f:
                data = json.load(f)
            self.monthly_stats = {
                key: MonthlyStats.from_dict(value) for key, value in data.items()
            }
        except (OSError, ValueError) as err:
            raise ValueError(f"Failed to load stats store: {err}") from err

    def save(self) -> None:
        """Save stats to the JSON file."""
        data = {key: value.to_dict() for key, value in self.monthly_stats.items()}
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def get_month(self, month_key: str) -> MonthlyStats:
        """Get stats for a month key (YYYY-MM), creating it if missing."""
        if month_key not in self.monthly_stats:
            self.monthly_stats[month_key] = MonthlyStats(month=month_key)
        return self.monthly_stats[month_key]

    def all_months(self) -> list[MonthlyStats]:
        """All stored months, newest first."""
        return sorted(self.monthly_stats.values(), key=lambda s: s.month, reverse=True)
