"""Switch entities for Beurer FreshHome."""

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import callback

from .const import DOMAIN
from .coordinator import BeurerDataUpdateCoordinator
from .entity import BeurerEntity


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up switch entities for all devices."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    switches = []
    for device_id in coordinator.device_states:
        switches.extend(
            [
                BeurerSleepSwitch(coordinator, device_id),
                BeurerUVSwitch(coordinator, device_id),
                BeurerBuzzerSwitch(coordinator, device_id),
            ]
        )

    async_add_entities(switches)


class BeurerSleepSwitch(BeurerEntity, SwitchEntity):
    """Switch for Sleep Mode."""

    _attr_icon = "mdi:power-sleep"

    def __init__(
        self, coordinator: BeurerDataUpdateCoordinator, device_id: str
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, device_id)

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self.device_id}_sleep_switch"

    @property
    def name(self) -> str:
        """Return name."""
        return f"{self.coordinator.get_device_name(self.device_id)} Sleep Mode"

    @property
    def is_on(self) -> bool | None:
        """Return True if sleep mode is on."""
        device_state = self.coordinator.device_states.get(self.device_id, {})
        return bool(device_state.get("sleep"))

    async def async_turn_on(self) -> None:
        """Turn sleep mode on."""
        await self.coordinator.async_send_command(self.device_id, "sleep", 1)

    async def async_turn_off(self) -> None:
        """Turn sleep mode off."""
        await self.coordinator.async_send_command(self.device_id, "sleep", 0)

    @callback
    def handle_state_update(self, new_state: dict | None) -> None:
        """Handle state update from coordinator."""
        if new_state is not None:
            self.async_write_ha_state()


class BeurerUVSwitch(BeurerEntity, SwitchEntity):
    """Switch for UV Light."""

    _attr_icon = "mdi:lightbulb-ultraviolet"

    def __init__(
        self, coordinator: BeurerDataUpdateCoordinator, device_id: str
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, device_id)

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self.device_id}_uv_switch"

    @property
    def name(self) -> str:
        """Return name."""
        return f"{self.coordinator.get_device_name(self.device_id)} UV Light"

    @property
    def is_on(self) -> bool | None:
        """Return True if UV light is on."""
        device_state = self.coordinator.device_states.get(self.device_id, {})
        return bool(device_state.get("uv"))

    async def async_turn_on(self) -> None:
        """Turn UV light on."""
        await self.coordinator.async_send_command(self.device_id, "uv", 1)

    async def async_turn_off(self) -> None:
        """Turn UV light off."""
        await self.coordinator.async_send_command(self.device_id, "uv", 0)

    @callback
    def handle_state_update(self, new_state: dict | None) -> None:
        """Handle state update from coordinator."""
        if new_state is not None:
            self.async_write_ha_state()


class BeurerBuzzerSwitch(BeurerEntity, SwitchEntity):
    """Switch for Buzzer."""

    _attr_icon = "mdi:volume-high"

    def __init__(
        self, coordinator: BeurerDataUpdateCoordinator, device_id: str
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, device_id)

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self.device_id}_buzzer_switch"

    @property
    def name(self) -> str:
        """Return name."""
        return f"{self.coordinator.get_device_name(self.device_id)} Buzzer"

    @property
    def is_on(self) -> bool | None:
        """Return True if buzzer is on."""
        device_state = self.coordinator.device_states.get(self.device_id, {})
        return bool(device_state.get("buzzer"))

    async def async_turn_on(self) -> None:
        """Turn buzzer on."""
        await self.coordinator.async_send_command(self.device_id, "buzzer", 1)

    async def async_turn_off(self) -> None:
        """Turn buzzer off."""
        await self.coordinator.async_send_command(self.device_id, "buzzer", 0)

    @callback
    def handle_state_update(self, new_state: dict | None) -> None:
        """Handle state update from coordinator."""
        if new_state is not None:
            self.async_write_ha_state()
