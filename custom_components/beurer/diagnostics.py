"""Diagnostics support for Beurer FreshHome."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import BeurerDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

TO_REDACT = {"password", "access_token", "refresh_token"}

async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: BeurerDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    diagnostics_data = {
        "entry": async_redact_data(entry.as_dict(), TO_REDACT),
        "device_states": coordinator.device_states,
    }

    return diagnostics_data
