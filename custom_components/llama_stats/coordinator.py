"""DataUpdateCoordinator for the llama.cpp Stats integration."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_CONTAINER,
    CONF_HOST,
    CONF_INPUT_PRICE,
    CONF_OUTPUT_PRICE,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    DATA_VERSION,
    DEFAULT_CONTAINER,
    DEFAULT_INPUT_PRICE,
    DEFAULT_OUTPUT_PRICE,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
)
from .store import MonthlyStats
from .util import calculate_cost, parse_log_lines

_LOGGER = logging.getLogger(__name__)


def get_conf(entry: ConfigEntry, key: str, default: Any) -> Any:
    """Read an option with fallback to entry data and default."""
    return entry.options.get(key, entry.data.get(key, default))


class LlamaStatsCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Poll the Unraid companion plugin and maintain the monthly store."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="llama.cpp Stats",
            update_interval=timedelta(seconds=get_conf(entry, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)),
        )
        self.entry = entry
        self.host = get_conf(entry, CONF_HOST, "homenas")
        self.port = int(get_conf(entry, CONF_PORT, DEFAULT_PORT))
        self.container = get_conf(entry, CONF_CONTAINER, DEFAULT_CONTAINER)
        self.input_price = get_conf(entry, CONF_INPUT_PRICE, DEFAULT_INPUT_PRICE)
        self.output_price = get_conf(entry, CONF_OUTPUT_PRICE, DEFAULT_OUTPUT_PRICE)
        self.session = async_get_clientsession(hass)
        self.store = Store(hass, DATA_VERSION, "llama_stats")
        self.data_state: dict[str, Any] = {"cursor": "", "months": {}}

    async def async_load_state(self) -> None:
        """Load persisted state from HA .storage."""
        saved = await self.store.async_load()
        if saved:
            self.data_state = saved

    def get_current_month(self) -> MonthlyStats:
        """Return the current month's statistics (creating it if missing)."""
        key = MonthlyStats.month_key()
        months = self.data_state["months"]
        if key not in months:
            months[key] = MonthlyStats(month=key)
        return months[key]

    async def _async_update_data(self) -> dict[str, Any]:
        """Poll the plugin, aggregate into the current month, persist state."""
        cursor = self.data_state.get("cursor", "")
        params = {"since": cursor} if cursor else {}
        url = f"http://{self.host}:{self.port}/metrics"
        async with asyncio.timeout(15):
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    raise UpdateFailed(f"HTTP {response.status} from plugin endpoint")
                metrics = await response.json()

        window = parse_log_lines(metrics.get("lines", [])) if "lines" in metrics else {
            "input_tokens": int(metrics.get("input_tokens", 0)),
            "gen_tokens": int(metrics.get("gen_tokens", 0)),
            "requests": int(metrics.get("requests", 0)),
            "last_timestamp": metrics.get("last_timestamp", ""),
        }

        month = self.get_current_month()
        cost = calculate_cost(
            window["input_tokens"], window["gen_tokens"], self.input_price, self.output_price
        )
        month.add_window(window["input_tokens"], window["gen_tokens"], window["requests"], cost)

        if window["last_timestamp"]:
            self.data_state["cursor"] = window["last_timestamp"]

        await self.store.async_save(
            {
                "cursor": self.data_state.get("cursor", ""),
                "months": {k: v.to_dict() for k, v in self.data_state["months"].items()},
            }
        )

        return {
            "input_tokens": month.input_tokens,
            "gen_tokens": month.gen_tokens,
            "total_tokens": month.total_tokens,
            "cost": round(month.total_cost, 4),
            "requests": month.requests,
            "month": month.month,
            "last_updated": month.last_updated,
            "window_input": window["input_tokens"],
            "window_gen": window["gen_tokens"],
        }


class CannotConnect(Exception):
    """Raised when the plugin endpoint is unreachable during validation."""
