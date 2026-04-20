"""Data update coordinator for Beurer FreshHome integration."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Awaitable, Callable, Dict, Optional, Set

from homeassistant.exceptions import HomeAssistantError

from .const import (  # type: ignore
    DISCONNECT_TIMEOUT,
)
from .models import AwsCmdModel, BeurerDevice

# Optional import for SignalR client. We guard this to allow tests to run
# in environments where the SignalR client is not available.
_LOGGER = logging.getLogger(__name__)


class BeurerDataUpdateCoordinator:
    """Coordinator to manage Beurer devices and real-time updates.

    This class keeps a local cache of device states and notifies registered
    entity callbacks when updates arrive. It also handles token refresh with a
    per-coordinator asyncio.Lock to avoid race conditions.
    """

    def __init__(self, hass, entry, api_client) -> None:
        self.hass = hass
        self.entry = entry
        self.api_client = api_client
        self.signalr_client = None  # type: Optional[Any]
        self.device_states: Dict[str, Dict[str, Any]] = {}
        self.entity_callbacks: Dict[str, Set[Callable[[str, Dict[str, Any]], Any]]] = {}
        self._token_lock: asyncio.Lock = asyncio.Lock()

        # Internal state helpers
        self._initialized = False

    async def async_setup(self) -> None:
        """Initialize coordinator: fetch devices and start SignalR if available."""
        email = None
        access_token = None
        refresh_token = None

        # Entry data is expected to carry credentials. Be defensive here.
        data = getattr(self.entry, "data", {}) or {}
        email = data.get("email")
        access_token = data.get("access_token") or data.get("token")
        refresh_token = data.get("refresh_token")

        # Validate and refresh token if needed before making API calls
        access_token = await self._ensure_valid_token(
            email, access_token, refresh_token
        )

        # Load devices from API if possible
        devices: list[BeurerDevice] = []
        if self.api_client is not None and email and access_token:
            try:
                devices = await self.api_client.get_devices(
                    email, access_token, refresh_token
                )
            except Exception as err:  # pragma: no cover - defensive
                _LOGGER.debug("Failed to fetch devices: %s", err)
                devices = []

        # Initialize device state cache
        now = time.time()
        for d in devices:
            # BeurerDevice is imported as a dataclass; keep a simple state snapshot
            self.device_states[d.id] = {
                "id": d.id,
                "name": d.name,
                "model": d.model,
                "user": d.user,
                "online": True,
                "last_seen": now,
            }

        # Initialize SignalR client if available
        try:
            from .signalr_client import BeurerSignalRClient

            self.signalr_client = BeurerSignalRClient(
                access_token=access_token,
                on_state_callback=self._on_state_update,
                on_disconnect_callback=self._on_disconnect,
            )
            await self.signalr_client.async_connect()
            _LOGGER.info("SignalR client connected successfully")
        except Exception as err:
            _LOGGER.warning("SignalR connection failed: %s", err)
            self.signalr_client = None

        self._initialized = True

    async def async_shutdown(self) -> None:
        """Cleanup resources and disconnect SignalR client."""
        if self.signalr_client is not None:
            try:
                await self.signalr_client.async_disconnect()
            except Exception as err:
                _LOGGER.debug("SignalR disconnect failed: %s", err)
            finally:
                self.signalr_client = None

        # Close API client if it provides a close method
        if hasattr(self.api_client, "close"):
            try:
                await self.api_client.close()  # type: ignore[call-arg]
            except Exception:  # pragma: no cover
                pass

    async def _ensure_valid_token(
        self,
        email: str | None,
        access_token: str | None,
        refresh_token: str | None,
    ) -> str | None:
        """Ensure we have a valid access token, refreshing if needed.

        Args:
            email: User email (for logging purposes).
            access_token: Current access token to validate.
            refresh_token: Refresh token for token refresh.

        Returns:
            Valid access token or None if authentication fails.
        """
        if not email:
            _LOGGER.debug("No email available for token validation")
            return None

        auth_client = getattr(self.api_client, "_auth_client", None)
        if auth_client is None:
            _LOGGER.debug("No auth client available for token validation")
            return access_token

        # Check if current token is still valid
        if access_token and auth_client.validate_token(access_token):
            _LOGGER.debug("Access token is valid")
            return access_token

        _LOGGER.debug("Access token expired or invalid, attempting refresh")

        # Try to refresh the token
        if refresh_token:
            try:
                new_tokens = await auth_client.refresh_token(refresh_token)
                new_access = getattr(new_tokens, "access_token", None)
                new_refresh = getattr(new_tokens, "refresh_token", None)

                if new_access:
                    # Update config entry with new tokens
                    data = dict(getattr(self.entry, "data", {}) or {})
                    data["access_token"] = new_access
                    if new_refresh:
                        data["refresh_token"] = new_refresh

                    await self.hass.config_entries.async_update_entry(
                        self.entry, data=data
                    )
                    self.entry.data.update(data)  # type: ignore[attr-defined]

                    _LOGGER.debug("Token refreshed successfully")
                    return new_access
            except Exception as err:
                _LOGGER.debug("Token refresh failed: %s", err)

        _LOGGER.error(
            "Unable to obtain valid access token for %s. "
            "The refresh token may have expired. "
            "Please remove and re-add the Beurer FreshHome integration.",
            email
        )
        return None

    async def async_refresh_token(self) -> None:
        """Refresh access token in a thread-safe manner."""
        async with self._token_lock:
            data = getattr(self.entry, "data", {}) or {}
            refresh_token = data.get("refresh_token")
            if not refresh_token:
                return

            auth_client = getattr(self.api_client, "_auth_client", None)
            if auth_client is None:
                _LOGGER.debug("No auth client available; cannot refresh token")
                return

            try:
                new_tokens = await auth_client.refresh_token(refresh_token)  # type: ignore[call-arg]
            except Exception as err:  # pragma: no cover
                _LOGGER.debug("Token refresh failed: %s", err)
                return

            # Update config entry with new tokens
            try:
                new_access = getattr(new_tokens, "access_token", None)
                new_refresh = getattr(new_tokens, "refresh_token", None)
                if not new_access:
                    new_access = (
                        new_tokens.get("access_token")
                        if isinstance(new_tokens, dict)
                        else None
                    )
                if not new_refresh:
                    new_refresh = (
                        new_tokens.get("refresh_token")
                        if isinstance(new_tokens, dict)
                        else None
                    )

                updated = dict(data)
                if new_access:
                    updated["access_token"] = new_access
                if new_refresh:
                    updated["refresh_token"] = new_refresh
                if updated != data:
                    await self.hass.config_entries.async_update_entry(
                        self.entry, data=updated
                    )  # type: ignore[arg-type]
                    # Keep in-memory snapshot in sync
                    self.entry.data.update(updated)  # type: ignore[attr-defined]
            except Exception as err:  # pragma: no cover
                _LOGGER.debug("Failed to persist refreshed tokens: %s", err)

    async def async_send_command(
        self, device_id: str, function: str, value: Any
    ) -> None:
        """Send a command to a device via SignalR and handle token refresh on 401."""
        if self.signalr_client is None:
            _LOGGER.debug("No SignalR client; cannot send command for %s", device_id)
            raise HomeAssistantError("Not connected to device")

        try:
            await self.signalr_client.async_send_command(device_id, function, value)
        except Exception as err:
            msg = str(err)
            if "401" in msg or "Unauthorized" in msg:
                # Token might be expired; refresh and retry once
                await self.async_refresh_token()
                try:
                    await self.signalr_client.async_send_command(
                        device_id, function, value
                    )
                except Exception as retry_err:
                    _LOGGER.error("Command failed after token refresh: %s", retry_err)
                    raise retry_err
            else:
                _LOGGER.error("Failed to send command: %s", msg)
                raise err

    async def async_register_entity(
        self, device_id: str, callback: Callable[[str, Dict[str, Any]], Any]
    ) -> None:
        """Register an entity callback for a device state updates."""
        if device_id not in self.entity_callbacks:
            self.entity_callbacks[device_id] = set()
        self.entity_callbacks[device_id].add(callback)

        # Immediately push current state if available
        if device_id in self.device_states:
            try:
                await callback(device_id, dict(self.device_states[device_id]))  # type: ignore[arg-type]
            except Exception:  # pragma: no cover
                pass

    async def async_unregister_entity(
        self, device_id: str, callback: Callable[[str, Dict[str, Any]], Any]
    ) -> None:
        """Unregister a previously registered entity callback."""
        if device_id in self.entity_callbacks:
            self.entity_callbacks[device_id].discard(callback)
            if not self.entity_callbacks[device_id]:
                del self.entity_callbacks[device_id]

    # Internal callbacks used by the SignalR client (if any) or internal updates
    async def _on_state_update(
        self, device_id: str, state_dict: Dict[str, Any]
    ) -> None:
        """Handle a state update for a device and notify registered entities."""
        if device_id not in self.device_states:
            self.device_states[device_id] = {
                "id": device_id,
                "name": state_dict.get("name", self.get_device_name(device_id)),
                "model": state_dict.get("model", self.get_device_model(device_id)),
                "user": state_dict.get("user", None),
                "online": True,
                "last_seen": time.time(),
            }

        # Merge new state into cached device state
        self.device_states[device_id].update(state_dict)
        self.device_states[device_id]["last_seen"] = time.time()
        # Notify all registered callbacks
        callbacks = list(self.entity_callbacks.get(device_id, set()))
        for cb in callbacks:
            try:
                cb(device_id, dict(self.device_states[device_id]))  # type: ignore[arg-type]
            except Exception:  # pragma: no cover
                _LOGGER.debug(
                    "Entity callback raised exception for device %s", device_id
                )

    async def _on_disconnect(self, device_id: str) -> None:
        """Handle a device disconnect event (mark as timed out)."""
        if device_id not in self.device_states:
            self.device_states[device_id] = {
                "id": device_id,
                "name": self.get_device_name(device_id),
                "model": self.get_device_model(device_id),
                "user": None,
                "online": False,
                "last_seen": time.time(),
            }
        else:
            self.device_states[device_id]["online"] = False
            self.device_states[device_id]["last_seen"] = time.time()

        # Notify entities about the disconnect
        callbacks = list(self.entity_callbacks.get(device_id, set()))
        for cb in callbacks:
            try:
                cb(device_id, dict(self.device_states[device_id]))  # type: ignore[arg-type]
            except Exception:  # pragma: no cover
                _LOGGER.debug(
                    "Entity callback raised exception on disconnect for device %s",
                    device_id,
                )

    def is_device_timed_out(self, device_id: str) -> bool:
        """Return True if the device has not sent an update for 15 seconds."""
        info = self.device_states.get(device_id, {})
        last_seen = info.get("last_seen")
        if last_seen is None:
            return True
        return (time.time() - last_seen) > DISCONNECT_TIMEOUT

    def get_device_model(self, device_id: str) -> str:
        """Return the device model for a given device_id or LR500 by default."""
        info = self.device_states.get(device_id, {})
        model = info.get("model")
        if model:
            return model
        # If we have no model yet, fall back to LR500 as a safe default
        return "LR500"

    def get_device_name(self, device_id: str) -> str:
        """Return the device name for a given device_id or a fallback."""
        info = self.device_states.get(device_id, {})
        name = info.get("name")
        if name:
            return name
        return f"Beurer Device {device_id}" if device_id else "Beurer Device"
