"""Entity base class for Beurer FreshHome."""

from __future__ import annotations

from homeassistant.core import callback
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN
from .coordinator import BeurerDataUpdateCoordinator


class BeurerEntity(Entity):
    """Base class for Beurer FreshHome entities."""

    _attr_should_poll = False

    def __init__(
        self,
        coordinator: BeurerDataUpdateCoordinator,
        device_id: str,
    ) -> None:
        """Initialize the entity."""
        self.coordinator = coordinator
        self.device_id = device_id

    @property
    def available(self) -> bool:
        """Return True if device state exists and is not timed out."""
        device_state = self.coordinator.device_states.get(self.device_id)
        if device_state is None:
            return False
        return not self.coordinator.is_device_timed_out(self.device_id)

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            manufacturer="Beurer",
            model=self.coordinator.get_device_model(self.device_id),
            name=self.coordinator.get_device_name(self.device_id),
            identifiers={(DOMAIN, self.device_id)},
        )

    async def async_added_to_hass(self) -> None:
        await self.coordinator.async_register_entity(
            self.device_id, self.handle_state_update
        )

    @callback
    def handle_state_update(self, device_id: str, new_state: dict | None) -> None:
        """Handle state update from coordinator.

        Called by the coordinator when the device state changes.
        Subclasses should override this to update entity state.
        """
        if new_state is not None:
            self.async_write_ha_state()
