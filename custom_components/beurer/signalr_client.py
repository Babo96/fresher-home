"""Beurer FreshHome SignalR WebSocket client using aiohttp."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Callable

import aiohttp

from .const import SIGNALR_URL, PROTOCOL_VERSION, DEFAULT_SOURCE

_LOGGER = logging.getLogger(__name__)

# SignalR JSON protocol record separator
RECORD_SEPARATOR = chr(0x1E)


class BeurerSignalRClient:
    """Async SignalR client for Beurer FreshHome using raw WebSocket."""

    def __init__(
        self,
        access_token: str,
        on_state_callback: Callable[[str, dict[str, Any]], Any] | None,
        on_disconnect_callback: Callable[[str], Any] | None,
    ) -> None:
        self._access_token = access_token
        self._on_state_callback = on_state_callback
        self._on_disconnect_callback = on_disconnect_callback
        self._logger = _LOGGER

        self._session: aiohttp.ClientSession | None = None
        self._ws: aiohttp.ClientWebSocketResponse | None = None
        self._connected = False
        self._receive_task: asyncio.Task | None = None
        self._device_last_seen: dict[str, float] = {}
        self._disconnect_timeout = 15

    async def async_connect(self) -> None:
        """Connect to SignalR hub."""
        if self._connected:
            return

        # Build URL with auth token
        hub_url = f"{SIGNALR_URL}?access_token={self._access_token}"

        self._session = aiohttp.ClientSession()

        try:
            self._ws = await self._session.ws_connect(hub_url)
            self._logger.debug("WebSocket connected")

            # Send SignalR handshake
            handshake = {"protocol": "json", "version": 1}
            await self._ws.send_str(json.dumps(handshake) + RECORD_SEPARATOR)
            self._logger.debug("Handshake sent: %s", handshake)

            # Wait for handshake response
            msg = await self._ws.receive()
            if msg.type == aiohttp.WSMsgType.TEXT:
                self._logger.debug("Handshake response: %s", msg.data)

            self._connected = True

            # Start receive loop
            self._receive_task = asyncio.create_task(self._receive_loop())

        except Exception as err:
            self._logger.error("Failed to connect: %s", err)
            if self._session:
                await self._session.close()
            raise

    async def async_disconnect(self) -> None:
        """Disconnect from hub."""
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass

        if self._ws:
            await self._ws.close()

        if self._session:
            await self._session.close()

        self._connected = False

    async def async_send_command(
        self, device_id: str, function: str, value: Any
    ) -> None:
        """Send command to device."""
        if not self._connected or not self._ws:
            raise RuntimeError("Not connected")

        # Build command payload as JSON string (second argument must be string)
        cmd_payload = {
            "function": function,
            "value": value,
            "version": PROTOCOL_VERSION,
            "valueType": "int",
            "type": "cmd",
            "source": DEFAULT_SOURCE,
        }

        # SignalR invocation message format
        invocation = {
            "type": 1,
            "target": "SendCommand",
            "arguments": [
                device_id,
                json.dumps(cmd_payload),
            ],
        }

        await self._ws.send_str(json.dumps(invocation) + RECORD_SEPARATOR)
        self._logger.debug("Command sent: %s", invocation)

    async def _receive_loop(self) -> None:
        """Main receive loop for WebSocket messages."""
        if not self._ws:
            return

        try:
            async for msg in self._ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    await self._handle_message(msg.data)
                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    self._logger.debug("WebSocket closed")
                    break
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    self._logger.error("WebSocket error")
                    break
        except asyncio.CancelledError:
            self._logger.debug("Receive loop cancelled")
        except Exception as err:
            self._logger.exception("Receive loop error: %s", err)
        finally:
            self._connected = False

    async def _handle_message(self, data: str) -> None:
        """Handle incoming SignalR message."""
        # Split by record separator (messages can be batched)
        for msg_text in data.split(RECORD_SEPARATOR):
            if not msg_text:
                continue

            try:
                msg = json.loads(msg_text)
            except json.JSONDecodeError:
                continue

            msg_type = msg.get("type")

            # Type 1 = Invocation, Type 3 = Completion
            if msg_type == 1:
                # Server invocation (state update)
                target = msg.get("target")
                arguments = msg.get("arguments", [])

                if target == "ReceiveMessage" and len(arguments) >= 2:
                    device_id = arguments[0]
                    payload = arguments[1]
                    await self._handle_state_update(device_id, payload)

            elif msg_type == 3:
                # Completion (command response)
                self._logger.debug("Command completed: %s", msg)

    async def _handle_state_update(
        self, device_id: str, payload: str | dict[str, Any]
    ) -> None:
        """Handle device state update."""
        # Payload may be a JSON string, parse it
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                return

        if not isinstance(payload, dict) or payload.get("type") != "device":
            return

        self._device_last_seen[device_id] = asyncio.get_event_loop().time()

        state = payload.get("state") or payload

        if self._on_state_callback:
            try:
                result = self._on_state_callback(device_id, state)
                if asyncio.iscoroutine(result):
                    await result
            except Exception:
                self._logger.exception("Error in state callback")
