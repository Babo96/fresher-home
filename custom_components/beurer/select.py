"""Select entities for Beurer FreshHome."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import callback

from .const import DOMAIN
from .coordinator import BeurerDataUpdateCoordinator
from .entity import BeurerEntity

# Mode options and values
MODE_OPTIONS = ["manual", "auto", "sleep", "turbo"]
MODE_VALUE_MAP = {
    "manual": 0,
    "auto": 1,
    "sleep": 2,
    "turbo": 3,
}
MODE_NAME_MAP = {
    0: "manual",
    1: "auto",
    2: "sleep",
    3: "turbo",
}

# Temperature unit options and values
TEMP_UNIT_OPTIONS = ["celsius", "fahrenheit"]
TEMP_UNIT_VALUE_MAP = {
    "celsius": 0,
    "fahrenheit": 1,
}
TEMP_UNIT_NAME_MAP = {
    0: "celsius",
    1: "fahrenheit",
}


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up select entities for all devices."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    selects = []
    for device_id in coordinator.device_states:
        selects.extend(
            [
                BeurerModeSelect(coordinator, device_id),
                BeurerTempUnitSelect(coordinator, device_id),
            ]
        )

    async_add_entities(selects)


class BeurerModeSelect(BeurerEntity, SelectEntity):
    """Select for Mode."""

    _attr_icon = "mdi:fan"

    def __init__(
        self, coordinator: BeurerDataUpdateCoordinator, device_id: str
    ) -> None:
        """Initialize the mode select."""
        super().__init__(coordinator, device_id)

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self.device_id}_mode_select"

    @property
    def name(self) -> str:
        """Return name."""
        return f"{self.coordinator.get_device_name(self.device_id)} Mode"

    @property
    def options(self) -> list[str]:
        """Return available options."""
        return MODE_OPTIONS

    @property
    def current_option(self) -> str | None:
        """Return current option."""
        device_state = self.coordinator.device_states.get(self.device_id, {})
        mode_value = device_state.get("mode")
        if mode_value is not None:
            return MODE_NAME_MAP.get(mode_value)
        return None

    async def async_select_option(self, option: str) -> None:
        """Set the mode."""
        value = MODE_VALUE_MAP.get(option)
        if value is not None:
            await self.coordinator.async_send_command(self.device_id, "mode", value)

    @callback
    def handle_state_update(self, device_id: str, new_state: dict | None) -> None:
        """Handle state update from coordinator."""
        if new_state is not None:
            self.async_write_ha_state()


class BeurerTempUnitSelect(BeurerEntity, SelectEntity):
    """Select for Temperature Unit."""

    _attr_icon = "mdi:thermometer"

    def __init__(
        self, coordinator: BeurerDataUpdateCoordinator, device_id: str
    ) -> None:
        """Initialize the temperature unit select."""
        super().__init__(coordinator, device_id)

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self.device_id}_tempUnitSwitcher_select"

    @property
    def name(self) -> str:
        """Return name."""
        return f"{self.coordinator.get_device_name(self.device_id)} Temperature Unit"

    @property
    def options(self) -> list[str]:
        """Return available options."""
        return TEMP_UNIT_OPTIONS

    @property
    def current_option(self) -> str | None:
        """Return current option."""
        device_state = self.coordinator.device_states.get(self.device_id, {})
        temp_unit_value = device_state.get("tempUnitSwitcher")
        if temp_unit_value is not None:
            return TEMP_UNIT_NAME_MAP.get(temp_unit_value)
        return None

    async def async_select_option(self, option: str) -> None:
        """Set the temperature unit."""
        value = TEMP_UNIT_VALUE_MAP.get(option)
        if value is not None:
            await self.coordinator.async_send_command(
                self.device_id, "tempUnitSwitcher", value
            )

    @callback
    def handle_state_update(self, device_id: str, new_state: dict | None) -> None:
        """Handle state update from coordinator."""
        if new_state is not None:
            self.async_write_ha_state()
