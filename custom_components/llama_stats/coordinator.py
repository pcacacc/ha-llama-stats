"""DataUpdateCoordinator for the llama.cpp Stats integration."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_INPUT_PRICE,
    CONF_METRICS_URL,
    CONF_OUTPUT_PRICE,
    CONF_SCAN_INTERVAL,
    DEFAULT_INPUT_PRICE,
    DEFAULT_OUTPUT_PRICE,
    DEFAULT_SCAN_INTERVAL,
)
from .store import MonthlyStats, StatsStore
from .util import calculate_cost

_LOGGER = logging.getLogger(__name__)


class LlamaStatsCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetch llama.cpp metrics and maintain the monthly store."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, store: StatsStore):
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="llama.cpp Stats",
            update_interval=timedelta(
                seconds=entry.options.get(
                    CONF_SCAN_INTERVAL,
                    entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                )
            ),
        )
        self.entry = entry
        self.store = store
        self.metrics_url = entry.options.get(CONF_METRICS_URL, entry.data[CONF_METRICS_URL])
        self.input_price = entry.options.get(
            CONF_INPUT_PRICE, entry.data.get(CONF_INPUT_PRICE, DEFAULT_INPUT_PRICE)
        )
        self.output_price = entry.options.get(
            CONF_OUTPUT_PRICE, entry.data.get(CONF_OUTPUT_PRICE, DEFAULT_OUTPUT_PRICE)
        )
        self.session = async_get_clientsession(hass)

    def get_current_month(self) -> MonthlyStats:
        """Return the current month's statistics."""
        return self.store.get_month(MonthlyStats.month_key())

    async def fetch_metrics(self) -> dict[str, Any]:
        """Fetch metrics JSON from the llama.cpp endpoint."""
        async with asyncio.timeout(10):
            async with self.session.get(self.metrics_url) as response:
                if response.status != 200:
                    raise UpdateFailed(f"HTTP {response.status} from metrics endpoint")
                return await response.json()

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch metrics, record a snapshot, persist the store."""
        metrics = await self.fetch_metrics()

        input_tokens = int(metrics.get("input_tokens", 0))
        gen_tokens = int(metrics.get("gen_tokens", 0))
        cost = calculate_cost(input_tokens, gen_tokens, self.input_price, self.output_price)

        month = self.store.get_current_month()
        month.add_snapshot(input_tokens, gen_tokens, cost)
        self.store.save()

        return {
            "input_tokens": month.input_tokens,
            "gen_tokens": month.gen_tokens,
            "total_tokens": month.total_tokens,
            "cost": round(cost, 4),
            "snapshots": len(month.snapshots),
            "month": month.month,
            "last_updated": month.last_updated,
        }


class CannotConnect(Exception):
    """Raised when the metrics endpoint is unreachable during validation."""
