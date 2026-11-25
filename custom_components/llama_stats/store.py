"""Monthly statistics model (HA-independent, unit-testable)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime


@dataclass
class MonthlyStats:
    """Monthly token statistics."""

    month: str
    input_tokens: int = 0
    gen_tokens: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    requests: int = 0
    last_updated: str = ""

    def add_window(
        self, input_tokens: int, gen_tokens: int, requests: int, cost: float
    ) -> None:
        """Add one polling window (token counts delta since last poll)."""
        if requests == 0 and input_tokens == 0 and gen_tokens == 0:
            return
        self.input_tokens += input_tokens
        self.gen_tokens += gen_tokens
        self.total_tokens += input_tokens + gen_tokens
        self.total_cost = round(self.total_cost + cost, 6)
        self.requests += requests
        self.last_updated = datetime.now(UTC).isoformat()

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
