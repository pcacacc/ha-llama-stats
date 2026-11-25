"""Sensor platform for the llama.cpp Stats integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import LlamaStatsCoordinator

SENSOR_FIELDS: list[tuple[str, str, str | None, SensorStateClass | None, SensorDeviceClass | None]] = [
    ("input_tokens", "Input tokens", "tokens", SensorStateClass.TOTAL, None),
    ("gen_tokens", "Generated tokens", "tokens", SensorStateClass.TOTAL, None),
    ("total_tokens", "Total tokens", "tokens", SensorStateClass.TOTAL, None),
    ("cost", "Monthly cost", "$", SensorStateClass.TOTAL, SensorDeviceClass.MONETARY),
    ("snapshots", "Snapshots", "snapshots", SensorStateClass.TOTAL, None),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        LlamaStatsSensor(coordinator, entry, key, label, unit, state_class, device_class)
        for key, label, unit, state_class, device_class in SENSOR_FIELDS
    )


class LlamaStatsSensor(CoordinatorEntity[LlamaStatsCoordinator], SensorEntity):
    """Sensor exposing one field of the monthly statistics."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: LlamaStatsCoordinator,
        entry: ConfigEntry,
        key: str,
        label: str,
        unit: str,
        state_class: SensorStateClass,
        device_class: SensorDeviceClass | None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._key = key
        self._attr_name = label
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_state_class = state_class
        self._attr_device_class = device_class
        self._attr_suggested_display_precision = 2 if key == "cost" else 0
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title or "llama.cpp",
            manufacturer="llama.cpp",
            configuration_url=coordinator.metrics_url,
        )

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self._key)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return month and last_updated as attributes."""
        if self.coordinator.data is None:
            return {}
        return {
            "month": self.coordinator.data.get("month"),
            "last_updated": self.coordinator.data.get("last_updated"),
        }
