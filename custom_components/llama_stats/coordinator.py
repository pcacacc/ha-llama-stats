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
    CONF_CACHED_PRICE,
    CONF_CONTAINER,
    CONF_CURRENCY,
    CONF_ENERGY_PRICE,
    CONF_HOST,
    CONF_INPUT_PRICE,
    CONF_OUTPUT_PRICE,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    DATA_VERSION,
    DEFAULT_CACHED_PRICE,
    DEFAULT_CONTAINER,
    DEFAULT_CURRENCY,
    DEFAULT_ENERGY_PRICE,
    DEFAULT_INPUT_PRICE,
    DEFAULT_OUTPUT_PRICE,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
)
from .store import MonthlyStats
from .util import calculate_cost, parse_gpu_metrics

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
        self.cached_price = get_conf(entry, CONF_CACHED_PRICE, DEFAULT_CACHED_PRICE)
        self.energy_price = get_conf(entry, CONF_ENERGY_PRICE, DEFAULT_ENERGY_PRICE)
        self.currency = str(get_conf(entry, CONF_CURRENCY, DEFAULT_CURRENCY)).upper()
        self.currency_symbol = "€" if self.currency == "EUR" else "$"
        self.scan_interval = int(get_conf(entry, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
        self.session = async_get_clientsession(hass)
        self.store = Store(hass, DATA_VERSION, "llama_stats")
        self.containers = [c.strip() for c in str(self.container).split(",") if c.strip()]
        self.data_state: dict[str, Any] = {
            "cursors": {},
            "months": {},
            "gpus": [],
            "power_watts": 0.0,
        }

    async def async_load_state(self) -> None:
        """Load persisted state from HA .storage."""
        saved = await self.store.async_load()
        if saved:
            self.data_state = saved
        self.data_state["months"] = {
            key: MonthlyStats.from_dict(value)
            for key, value in self.data_state.get("months", {}).items()
        }
        self.data_state.setdefault("cursors", {})
        self.data_state.setdefault("gpus", [])
        self.data_state.setdefault("power_watts", 0.0)

        legacy_cursor = self.data_state.get("cursor", "")
        if not self.data_state["cursors"] and legacy_cursor:
            self.data_state["cursors"]["llama.cpp"] = legacy_cursor

    def get_current_month(self) -> MonthlyStats:
        """Return the current month's statistics (creating it if missing)."""
        key = MonthlyStats.month_key()
        months = self.data_state["months"]
        if key not in months:
            months[key] = MonthlyStats(month=key)
        return months[key]

    async def _async_update_data(self) -> dict[str, Any]:
        """Poll each configured source, aggregate tokens, update GPU power, persist state."""
        cursors = self.data_state.setdefault("cursors", {})
        window = {
            "input_tokens": 0,
            "cached_tokens": 0,
            "gen_tokens": 0,
            "requests": 0,
        }
        url = f"http://{self.host}:{self.port}/metrics"

        async with asyncio.timeout(30):
            for name in self.containers:
                params = {"container": name}
                if cursors.get(name):
                    params["since"] = cursors[name]
                async with self.session.get(url, params=params) as response:
                    if response.status != 200:
                        raise UpdateFailed(f"HTTP {response.status} from plugin endpoint")
                    metrics = await response.json()

                if "error" in metrics:
                    raise UpdateFailed(f"Plugin error for container {name}: {metrics['error']}")

                window["input_tokens"] += int(metrics.get("input_tokens", 0))
                window["cached_tokens"] += int(metrics.get("cached_tokens", 0))
                window["gen_tokens"] += int(metrics.get("gen_tokens", 0))
                window["requests"] += int(metrics.get("requests", 0))

                new_cursor = str(metrics.get("cursor", ""))
                if new_cursor:
                    cursors[name] = new_cursor

                if "gpus" in metrics or "power_watts" in metrics:
                    parsed_gpus, parsed_total = parse_gpu_metrics(metrics.get("gpus", []))
                    total_power = float(metrics.get("power_watts", parsed_total))
                    if parsed_gpus:
                        self.data_state["gpus"] = parsed_gpus
                    if total_power:
                        self.data_state["power_watts"] = total_power

        power_watts = float(self.data_state.get("power_watts", 0.0))
        energy_wh = round(power_watts * self.scan_interval / 3600.0, 6)
        energy_kwh = round(energy_wh / 1000.0, 6)
        energy_cost = round(energy_kwh * float(self.energy_price), 6)

        month = self.get_current_month()
        cost = calculate_cost(
            window["input_tokens"],
            window["gen_tokens"],
            self.input_price,
            self.output_price,
            window["cached_tokens"],
            self.cached_price,
        )
        month.add_window(
            window["input_tokens"],
            window["gen_tokens"],
            window["requests"],
            cost,
            window["cached_tokens"],
            energy_wh,
            energy_cost,
        )

        await self.store.async_save(
            {
                "cursors": cursors,
                "months": {k: v.to_dict() for k, v in self.data_state["months"].items()},
                "gpus": self.data_state.get("gpus", []),
                "power_watts": self.data_state.get("power_watts", 0.0),
            }
        )

        return {
            "input_tokens": month.input_tokens,
            "cached_tokens": month.cached_tokens,
            "gen_tokens": month.gen_tokens,
            "total_tokens": month.total_tokens,
            "cost": round(month.total_cost, 4),
            "energy_kwh": round(month.energy_kwh, 3),
            "energy_cost": round(month.energy_cost, 4),
            "net_cost": round(month.net_cost, 4),
            "requests": month.requests,
            "month": month.month,
            "last_updated": month.last_updated,
            "window_input": window["input_tokens"],
            "window_cached": window["cached_tokens"],
            "window_gen": window["gen_tokens"],
            "window_energy_wh": energy_wh,
            "gpus": self.data_state.get("gpus", []),
            "power_watts": power_watts,
        }


class CannotConnect(Exception):
    """Raised when the plugin endpoint is unreachable during validation."""
