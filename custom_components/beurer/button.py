"""Button entities for Beurer FreshHome."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import callback

from .const import DOMAIN
from .coordinator import BeurerDataUpdateCoordinator
from .entity import BeurerEntity


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up button entities for all devices."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    buttons = []
    for device_id in coordinator.device_states:
        buttons.extend(
            [
                BeurerFilterResetButton(coordinator, device_id),
                BeurerReadButton(coordinator, device_id),
            ]
        )

    async_add_entities(buttons)


class BeurerFilterResetButton(BeurerEntity, ButtonEntity):
    """Button to reset the filter timer."""

    _attr_icon = "mdi:air-filter"

    def __init__(
        self, coordinator: BeurerDataUpdateCoordinator, device_id: str
    ) -> None:
        """Initialize the filter reset button."""
        super().__init__(coordinator, device_id)

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self.device_id}_filterReset_button"

    @property
    def name(self) -> str:
        """Return name."""
        return f"{self.coordinator.get_device_name(self.device_id)} Reset Filter"

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.coordinator.async_send_command(self.device_id, "filterReset", 1)

    @callback
    def handle_state_update(self, new_state: dict | None) -> None:
        """Handle state update from coordinator."""
        if new_state is not None:
            self.async_write_ha_state()


class BeurerReadButton(BeurerEntity, ButtonEntity):
    """Button to request a state refresh from the device."""

    _attr_icon = "mdi:refresh"

    def __init__(
        self, coordinator: BeurerDataUpdateCoordinator, device_id: str
    ) -> None:
        """Initialize the read state button."""
        super().__init__(coordinator, device_id)

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self.device_id}_read_button"

    @property
    def name(self) -> str:
        """Return name."""
        return f"{self.coordinator.get_device_name(self.device_id)} Refresh"

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.coordinator.async_send_command(self.device_id, "read", 1)

    @callback
    def handle_state_update(self, new_state: dict | None) -> None:
        """Handle state update from coordinator."""
        if new_state is not None:
            self.async_write_ha_state()
