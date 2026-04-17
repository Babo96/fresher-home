"""Fan platform for Beurer FreshHome."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import BeurerDataUpdateCoordinator
from .entity import BeurerEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Beurer fan from a config entry."""
    coordinator: BeurerDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[FanEntity] = []

    # Create fan entities for each device
    for device_id in coordinator.device_states:
        entities.append(BeurerFan(coordinator, device_id))

    async_add_entities(entities)


# Speed mappings (fan value <-> percentage)
# Beurer devices have 4 speeds: 1, 2, 3, 4
# Map to percentages: 1=25%, 2=50%, 3=75%, 4=100%
# 0% is off state
SPEED_TO_PERCENTAGE = {1: 25, 2: 50, 3: 75, 4: 100}
PERCENTAGE_TO_SPEED = {25: 1, 50: 2, 75: 3, 100: 4}


class BeurerFan(FanEntity, BeurerEntity):
    """Representation of a Beurer FreshHome fan."""

    _attr_supported_features = (
        FanEntityFeature.SET_SPEED
        | FanEntityFeature.TURN_ON
        | FanEntityFeature.TURN_OFF
    )
    _attr_speed_count = 4

    def __init__(
        self,
        coordinator: BeurerDataUpdateCoordinator,
        device_id: str,
    ) -> None:
        """Initialize the fan entity."""
        super().__init__(coordinator, device_id)

    @property
    def unique_id(self) -> str:
        """Return a unique ID for this entity."""
        return f"{self.device_id}_fan"

    @property
    def name(self) -> str:
        """Return the display name of this fan."""
        device_name = self.coordinator.get_device_name(self.device_id)
        return f"{device_name} Fan"

    @property
    def is_on(self) -> bool | None:
        """Return true if the fan is on."""
        device_state = self.coordinator.device_states.get(self.device_id)
        if device_state is None:
            return None
        power = device_state.get("power")
        return power == 1 if power is not None else None

    @property
    def percentage(self) -> int | None:
        """Return the current speed as a percentage."""
        device_state = self.coordinator.device_states.get(self.device_id)
        if device_state is None:
            return None

        # Check if device is off
        power = device_state.get("power")
        if power == 0:
            return 0

        # Get fan speed (1-4)
        fan_speed = device_state.get("fan")
        if fan_speed is None:
            return None

        return SPEED_TO_PERCENTAGE.get(fan_speed)

    @property
    def speed_list(self) -> list[str]:
        """Return the list of available speeds."""
        return ["1", "2", "3", "4"]

    @property
    def percentage_step(self) -> int:
        """Return the step size for percentage."""
        return 25

    async def async_turn_on(self, percentage: int | None = None, **kwargs: Any) -> None:
        """Turn on the fan."""
        # If percentage is provided, set that speed
        if percentage is not None and percentage > 0:
            await self.async_set_percentage(percentage)
            return

        old_power = self.coordinator.device_states.get(self.device_id, {}).get("power")
        try:
            if self.device_id in self.coordinator.device_states:
                self.coordinator.device_states[self.device_id]["power"] = 1
                self.async_write_ha_state()
            await self.coordinator.async_send_command(self.device_id, "power", 1)
        except Exception:
            if self.device_id in self.coordinator.device_states and old_power is not None:
                self.coordinator.device_states[self.device_id]["power"] = old_power
                self.async_write_ha_state()
            _LOGGER.warning("Failed to turn on fan for device %s", self.device_id)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the fan."""
        old_power = self.coordinator.device_states.get(self.device_id, {}).get("power")
        try:
            if self.device_id in self.coordinator.device_states:
                self.coordinator.device_states[self.device_id]["power"] = 0
                self.async_write_ha_state()
            await self.coordinator.async_send_command(self.device_id, "power", 0)
        except Exception:
            if self.device_id in self.coordinator.device_states and old_power is not None:
                self.coordinator.device_states[self.device_id]["power"] = old_power
                self.async_write_ha_state()
            _LOGGER.warning("Failed to turn off fan for device %s", self.device_id)

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed of the fan as a percentage."""
        if percentage == 0:
            await self.async_turn_off()
            return

        if percentage <= 25:
            speed = 1
        elif percentage <= 50:
            speed = 2
        elif percentage <= 75:
            speed = 3
        else:
            speed = 4

        old_power = self.coordinator.device_states.get(self.device_id, {}).get("power")
        old_fan = self.coordinator.device_states.get(self.device_id, {}).get("fan")
        try:
            if self.device_id in self.coordinator.device_states:
                self.coordinator.device_states[self.device_id]["power"] = 1
                self.coordinator.device_states[self.device_id]["fan"] = speed
                self.async_write_ha_state()
            await self.coordinator.async_send_command(self.device_id, "power", 1)
            await self.coordinator.async_send_command(self.device_id, "fan", speed)
        except Exception:
            if self.device_id in self.coordinator.device_states:
                if old_power is not None:
                    self.coordinator.device_states[self.device_id]["power"] = old_power
                if old_fan is not None:
                    self.coordinator.device_states[self.device_id]["fan"] = old_fan
                self.async_write_ha_state()
            _LOGGER.warning("Failed to set fan speed for device %s", self.device_id)

    @callback
    def handle_state_update(self, device_id: str, new_state: dict | None) -> None:
        """Handle state update from coordinator.

        Called by the coordinator when the device state changes.
        Updates Home Assistant state to reflect new device state.
        """
        if new_state is not None:
            self.async_write_ha_state()
