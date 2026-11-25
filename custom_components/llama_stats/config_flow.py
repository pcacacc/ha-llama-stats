"""Config flow for the llama.cpp Stats integration."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_INPUT_PRICE,
    CONF_METRICS_URL,
    CONF_OUTPUT_PRICE,
    CONF_SCAN_INTERVAL,
    DEFAULT_INPUT_PRICE,
    DEFAULT_OUTPUT_PRICE,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .coordinator import CannotConnect

_LOGGER = logging.getLogger(__name__)


def _user_schema() -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_METRICS_URL): str,
            vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
                vol.Coerce(int), vol.Range(min=10, max=3600)
            ),
            vol.Optional(CONF_INPUT_PRICE, default=DEFAULT_INPUT_PRICE): vol.Coerce(float),
            vol.Optional(CONF_OUTPUT_PRICE, default=DEFAULT_OUTPUT_PRICE): vol.Coerce(float),
        }
    )


async def validate_connection(session: aiohttp.ClientSession, url: str) -> None:
    """Validate that the metrics endpoint is reachable."""
    try:
        async with session.get(url) as response:
            if response.status == 200:
                await response.json()
                return
            raise CannotConnect(f"HTTP {response.status}")
    except (aiohttp.ClientError, TimeoutError) as err:
        raise CannotConnect(str(err)) from err


class LlamaStatsConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for llama.cpp Stats."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            url = user_input[CONF_METRICS_URL].strip()
            await self.async_set_unique_id(url.lower())
            try:
                await validate_connection(async_get_clientsession(self.hass), url)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(title="llama.cpp Stats", data=user_input)

        return self.async_show_form(step_id="user", data_schema=_user_schema(), errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlow:
        return LlamaStatsOptionsFlow(config_entry)


class LlamaStatsOptionsFlow(OptionsFlow):
    """Handle llama.cpp Stats options."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = {
            CONF_METRICS_URL: self._config_entry.options.get(
                CONF_METRICS_URL, self._config_entry.data[CONF_METRICS_URL]
            ),
            CONF_SCAN_INTERVAL: self._config_entry.options.get(
                CONF_SCAN_INTERVAL, self._config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
            ),
            CONF_INPUT_PRICE: self._config_entry.options.get(
                CONF_INPUT_PRICE, self._config_entry.data.get(CONF_INPUT_PRICE, DEFAULT_INPUT_PRICE)
            ),
            CONF_OUTPUT_PRICE: self._config_entry.options.get(
                CONF_OUTPUT_PRICE, self._config_entry.data.get(CONF_OUTPUT_PRICE, DEFAULT_OUTPUT_PRICE)
            ),
        }
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_METRICS_URL, default=current[CONF_METRICS_URL]): str,
                    vol.Optional(CONF_SCAN_INTERVAL, default=current[CONF_SCAN_INTERVAL]): vol.All(
                        vol.Coerce(int), vol.Range(min=10, max=3600)
                    ),
                    vol.Optional(CONF_INPUT_PRICE, default=current[CONF_INPUT_PRICE]): vol.Coerce(float),
                    vol.Optional(CONF_OUTPUT_PRICE, default=current[CONF_OUTPUT_PRICE]): vol.Coerce(float),
                }
            ),
        )
