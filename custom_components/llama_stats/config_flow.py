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
    CONF_CACHED_PRICE,
    CONF_CONTAINER,
    CONF_CURRENCY,
    CONF_ENERGY_PRICE,
    CONF_HOST,
    CONF_INPUT_PRICE,
    CONF_OUTPUT_PRICE,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    DEFAULT_CACHED_PRICE,
    DEFAULT_CONTAINER,
    DEFAULT_CURRENCY,
    DEFAULT_ENERGY_PRICE,
    DEFAULT_INPUT_PRICE,
    DEFAULT_OUTPUT_PRICE,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .coordinator import CannotConnect

_LOGGER = logging.getLogger(__name__)

_FIELD_ORDER = [
    CONF_HOST,
    CONF_PORT,
    CONF_CONTAINER,
    CONF_SCAN_INTERVAL,
    CONF_INPUT_PRICE,
    CONF_OUTPUT_PRICE,
    CONF_CACHED_PRICE,
    CONF_ENERGY_PRICE,
    CONF_CURRENCY,
]


def _schema(current: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_HOST, default=current.get(CONF_HOST, "homenas")): str,
            vol.Optional(CONF_PORT, default=current.get(CONF_PORT, DEFAULT_PORT)): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=65535)
            ),
            vol.Optional(CONF_CONTAINER, default=current.get(CONF_CONTAINER, DEFAULT_CONTAINER)): str,
            vol.Optional(
                CONF_SCAN_INTERVAL, default=current.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
            ): vol.All(vol.Coerce(int), vol.Range(min=10, max=3600)),
            vol.Optional(
                CONF_INPUT_PRICE, default=current.get(CONF_INPUT_PRICE, DEFAULT_INPUT_PRICE)
            ): vol.Coerce(float),
            vol.Optional(
                CONF_OUTPUT_PRICE, default=current.get(CONF_OUTPUT_PRICE, DEFAULT_OUTPUT_PRICE)
            ): vol.Coerce(float),
            vol.Optional(
                CONF_CACHED_PRICE, default=current.get(CONF_CACHED_PRICE, DEFAULT_CACHED_PRICE)
            ): vol.Coerce(float),
            vol.Optional(
                CONF_ENERGY_PRICE, default=current.get(CONF_ENERGY_PRICE, DEFAULT_ENERGY_PRICE)
            ): vol.Coerce(float),
            vol.Optional(
                CONF_CURRENCY, default=current.get(CONF_CURRENCY, DEFAULT_CURRENCY)
            ): vol.Any("EUR", "USD"),
        }
    )


async def validate_connection(session: aiohttp.ClientSession, url: str) -> None:
    """Validate that the plugin endpoint is reachable."""
    try:
        async with session.get(url, params={"since": "1970-01-01T00:00:00Z"}) as response:
            if response.status == 200:
                await response.json()
                return
            raise CannotConnect(f"HTTP {response.status}")
    except (aiohttp.ClientError, TimeoutError) as err:
        raise CannotConnect(str(err)) from err


class LlamaStatsConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for llama.cpp Stats."""

    VERSION = 2

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            url = f"http://{user_input[CONF_HOST]}:{user_input[CONF_PORT]}/metrics"
            await self.async_set_unique_id(f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}")
            try:
                await validate_connection(async_get_clientsession(self.hass), url)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(title="llama.cpp Stats", data=user_input)

        return self.async_show_form(step_id="user", data_schema=_schema({}), errors=errors)

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
            key: self._config_entry.options.get(
                key, self._config_entry.data.get(key)
            )
            for key in _FIELD_ORDER
        }
        return self.async_show_form(step_id="init", data_schema=_schema(current))
