"""Number platform for Beurer FreshHome."""

from __future__ import annotations

import logging

from homeassistant.components.number import NumberEntity
from homeassistant.core import callback

from .const import DOMAIN
from .coordinator import BeurerDataUpdateCoordinator
from .entity import BeurerEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up number entities for all devices."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    numbers = []
    for device_id in coordinator.device_states:
        numbers.append(BeurerTimerNumber(coordinator, device_id))

    async_add_entities(numbers)


class BeurerTimerNumber(BeurerEntity, NumberEntity):
    """Number entity for controlling device timer (0-480 minutes, 30-min increments)."""

    _attr_native_min_value = 0
    _attr_native_max_value = 480
    _attr_native_step = 30
    _attr_native_unit_of_measurement = "min"
    _attr_icon = "mdi:timer-outline"

    def __init__(
        self, coordinator: BeurerDataUpdateCoordinator, device_id: str
    ) -> None:
        """Initialize the timer number entity."""
        super().__init__(coordinator, device_id)

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self.device_id}_timer"

    @property
    def name(self) -> str:
        """Return name."""
        return f"{self.coordinator.get_device_name(self.device_id)} Timer"

    @property
    def native_value(self) -> float | None:
        """Return the current timer value in minutes."""
        device_state = self.coordinator.device_states.get(self.device_id, {})
        return device_state.get("timerMin")

    async def async_set_native_value(self, value: float) -> None:
        """Set the timer value in minutes."""
        old_value = self.coordinator.device_states.get(self.device_id, {}).get("timerMin")
        try:
            if self.device_id in self.coordinator.device_states:
                self.coordinator.device_states[self.device_id]["timerMin"] = int(value)
                self.async_write_ha_state()
            await self.coordinator.async_send_command(self.device_id, "timerMin", int(value))
        except Exception:
            if self.device_id in self.coordinator.device_states and old_value is not None:
                self.coordinator.device_states[self.device_id]["timerMin"] = old_value
                self.async_write_ha_state()
            _LOGGER.warning("Failed to set timer for device %s", self.device_id)

    @callback
    def handle_state_update(self, device_id: str, new_state: dict | None) -> None:
        """Handle state update from coordinator."""
        if new_state is not None:
            self.async_write_ha_state()
