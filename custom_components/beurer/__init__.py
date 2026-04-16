"""The Beurer FreshHome integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN
from .coordinator import BeurerDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.FAN,
    Platform.SWITCH,
    Platform.SELECT,
    Platform.NUMBER,
    Platform.BUTTON,
    Platform.SENSOR,
]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Beurer FreshHome component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Beurer FreshHome from a config entry."""
    coordinator = BeurerDataUpdateCoordinator(hass, entry)

    # Store coordinator
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Setup coordinator (auth, device discovery, SignalR connection)
    await coordinator.async_setup()

    # Forward setup to all platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Disconnect SignalR
    coordinator: BeurerDataUpdateCoordinator = hass.data[DOMAIN].get(entry.entry_id)
    if coordinator:
        await coordinator.async_shutdown()

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # Remove from hass.data
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok
