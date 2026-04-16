"""Sensor entities for Beurer FreshHome integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfTemperature,
    PERCENTAGE,
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, TEMP_UNIT_MAP
from .coordinator import BeurerDataUpdateCoordinator
from .entity import BeurerEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Beurer sensors from a config entry."""
    coordinator: BeurerDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = []

    # Create sensor entities for each device
    for device_id in coordinator.device_states:
        entities.extend(
            [
                BeurerPM25Sensor(coordinator, device_id),
                BeurerAQISensor(coordinator, device_id),
                BeurerHumiditySensor(coordinator, device_id),
                BeurerTemperatureSensor(coordinator, device_id),
                BeurerFilterStatusSensor(coordinator, device_id),
            ]
        )

    async_add_entities(entities)


class BeurerPM25Sensor(BeurerEntity, SensorEntity):
    """Representation of a Beurer PM2.5 sensor."""

    _attr_device_class = SensorDeviceClass.PM25
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = CONCENTRATION_MICROGRAMS_PER_CUBIC_METER
    _attr_icon = "mdi:air-filter"

    def __init__(
        self,
        coordinator: BeurerDataUpdateCoordinator,
        device_id: str,
    ) -> None:
        """Initialize the PM2.5 sensor."""
        super().__init__(coordinator, device_id)
        self._attr_unique_id = f"{device_id}_pm25"
        self._attr_name = "PM2.5"

    @property
    def native_value(self) -> int | None:
        """Return the PM2.5 value."""
        device_state = self.coordinator.device_states.get(self.device_id)
        if device_state is None:
            return None
        return device_state.get("pm")

    @callback
    def handle_state_update(self, new_state: dict[str, Any] | None) -> None:
        """Handle state update from coordinator."""
        if new_state is not None:
            self.async_write_ha_state()


class BeurerAQISensor(BeurerEntity, SensorEntity):
    """Representation of a Beurer Air Quality Index sensor."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:air-quality"

    def __init__(
        self,
        coordinator: BeurerDataUpdateCoordinator,
        device_id: str,
    ) -> None:
        """Initialize the AQI sensor."""
        super().__init__(coordinator, device_id)
        self._attr_unique_id = f"{device_id}_aqi"
        self._attr_name = "Air Quality Index"

    @property
    def native_value(self) -> int | None:
        """Return the AQI value."""
        device_state = self.coordinator.device_states.get(self.device_id)
        if device_state is None:
            return None
        return device_state.get("airquality")

    @callback
    def handle_state_update(self, new_state: dict[str, Any] | None) -> None:
        """Handle state update from coordinator."""
        if new_state is not None:
            self.async_write_ha_state()


class BeurerHumiditySensor(BeurerEntity, SensorEntity):
    """Representation of a Beurer humidity sensor."""

    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(
        self,
        coordinator: BeurerDataUpdateCoordinator,
        device_id: str,
    ) -> None:
        """Initialize the humidity sensor."""
        super().__init__(coordinator, device_id)
        self._attr_unique_id = f"{device_id}_humidity"
        self._attr_name = "Humidity"

    @property
    def native_value(self) -> int | None:
        """Return the humidity percentage."""
        device_state = self.coordinator.device_states.get(self.device_id)
        if device_state is None:
            return None
        return device_state.get("humidity")

    @callback
    def handle_state_update(self, new_state: dict[str, Any] | None) -> None:
        """Handle state update from coordinator."""
        if new_state is not None:
            self.async_write_ha_state()


class BeurerTemperatureSensor(BeurerEntity, SensorEntity):
    """Representation of a Beurer temperature sensor."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: BeurerDataUpdateCoordinator,
        device_id: str,
    ) -> None:
        """Initialize the temperature sensor."""
        super().__init__(coordinator, device_id)
        self._attr_unique_id = f"{device_id}_temperature"
        self._attr_name = "Temperature"

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the unit of measurement based on device tempUnit."""
        device_state = self.coordinator.device_states.get(self.device_id)
        if device_state is None:
            return UnitOfTemperature.CELSIUS
        temp_unit = device_state.get("tempUnitSwitcher", 0)
        return TEMP_UNIT_MAP.get(temp_unit, "°C")

    @property
    def native_value(self) -> int | None:
        """Return the temperature value."""
        device_state = self.coordinator.device_states.get(self.device_id)
        if device_state is None:
            return None
        return device_state.get("temperature")

    @callback
    def handle_state_update(self, new_state: dict[str, Any] | None) -> None:
        """Handle state update from coordinator."""
        if new_state is not None:
            self.async_write_ha_state()


class BeurerFilterStatusSensor(BeurerEntity, SensorEntity):
    """Representation of a Beurer filter status sensor."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_icon = "mdi:air-filter"

    def __init__(
        self,
        coordinator: BeurerDataUpdateCoordinator,
        device_id: str,
    ) -> None:
        """Initialize the filter status sensor."""
        super().__init__(coordinator, device_id)
        self._attr_unique_id = f"{device_id}_filter_status"
        self._attr_name = "Filter Status"

    @property
    def native_value(self) -> int | None:
        """Return the filter remaining percentage."""
        device_state = self.coordinator.device_states.get(self.device_id)
        if device_state is None:
            return None
        return device_state.get("filterLeft")

    @callback
    def handle_state_update(self, new_state: dict[str, Any] | None) -> None:
        """Handle state update from coordinator."""
        if new_state is not None:
            self.async_write_ha_state()
