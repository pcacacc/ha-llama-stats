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

SENSOR_FIELDS: list[tuple[str, str, str, SensorStateClass, SensorDeviceClass | None]] = [
    ("input_tokens", "Input tokens", "tokens", SensorStateClass.TOTAL, None),
    ("cached_tokens", "Cached input tokens", "tokens", SensorStateClass.TOTAL, None),
    ("gen_tokens", "Generated tokens", "tokens", SensorStateClass.TOTAL, None),
    ("total_tokens", "Total tokens", "tokens", SensorStateClass.TOTAL, None),
    ("cost", "Token cost", "", SensorStateClass.TOTAL, SensorDeviceClass.MONETARY),
    ("energy_kwh", "Energy", "kWh", SensorStateClass.TOTAL, SensorDeviceClass.ENERGY),
    ("energy_cost", "Energy cost", "", SensorStateClass.TOTAL, SensorDeviceClass.MONETARY),
    ("net_cost", "Net cost", "", SensorStateClass.TOTAL, SensorDeviceClass.MONETARY),
    ("requests", "Requests", "requests", SensorStateClass.TOTAL, None),
    ("power_watts", "GPU power", "W", SensorStateClass.MEASUREMENT, SensorDeviceClass.POWER),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        LlamaStatsSensor(
            coordinator,
            entry,
            key,
            label,
            unit,
            state_class,
            device_class,
            coordinator.currency,
            coordinator.currency_symbol,
        )
        for key, label, unit, state_class, device_class in SENSOR_FIELDS
    )

    if coordinator.data is not None:
        async_add_entities(
            LlamaStatsGPUSensor(coordinator, entry, gpu)
            for gpu in coordinator.data.get("gpus", [])
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
        currency: str,
        currency_symbol: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._key = key
        self._attr_name = label
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_native_unit_of_measurement = currency_symbol if device_class == SensorDeviceClass.MONETARY else unit
        self._attr_currency = currency if device_class == SensorDeviceClass.MONETARY else None
        self._attr_state_class = state_class
        self._attr_device_class = device_class
        if device_class == SensorDeviceClass.MONETARY:
            precision = 2
        elif key == "energy_kwh":
            precision = 2
        elif key == "power_watts":
            precision = 1
        else:
            precision = 0
        self._attr_suggested_display_precision = precision
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title or "llama.cpp",
            manufacturer="llama.cpp",
            model=coordinator.container,
        )

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self._key)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return month, last_updated, and currency as attributes."""
        if self.coordinator.data is None:
            return {}
        attrs = {
            "month": self.coordinator.data.get("month"),
            "last_updated": self.coordinator.data.get("last_updated"),
        }
        if self._attr_currency:
            attrs["currency"] = self._attr_currency
        return attrs


class LlamaStatsGPUSensor(CoordinatorEntity[LlamaStatsCoordinator], SensorEntity):
    """Sensor exposing current power draw for one discovered GPU."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: LlamaStatsCoordinator,
        entry: ConfigEntry,
        gpu: dict[str, Any],
    ) -> None:
        """Initialize the GPU power sensor."""
        super().__init__(coordinator)
        self._gpu_id = gpu.get("id", "")
        self._attr_name = gpu.get("label") or f"GPU {self._gpu_id}"
        self._attr_unique_id = f"{entry.entry_id}_gpu_{self._gpu_id}"
        self._attr_native_unit_of_measurement = "W"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_suggested_display_precision = 1
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title or "llama.cpp",
            manufacturer="llama.cpp",
            model=coordinator.container,
        )

    @property
    def native_value(self) -> Any:
        """Return current GPU power."""
        if self.coordinator.data is None:
            return None
        for gpu in self.coordinator.data.get("gpus", []):
            if gpu.get("id") == self._gpu_id:
                return gpu.get("power_watts")
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return GPU identifiers as attributes."""
        if self.coordinator.data is None:
            return {}
        for gpu in self.coordinator.data.get("gpus", []):
            if gpu.get("id") == self._gpu_id:
                return {"id": self._gpu_id, "bus": gpu.get("bus")}
        return {"id": self._gpu_id}
