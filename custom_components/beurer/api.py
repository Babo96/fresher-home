"""API client for Beurer FreshHome."""

from __future__ import annotations

import base64
import json
import logging
from typing import Any

import aiohttp

from .const import API_LOGIN, AUTH_URL
from .models import LoginResponse

_LOGGER = logging.getLogger(__name__)


class BeurerApiClientError(Exception):
    """Exception to indicate a general API error."""

    pass


class BeurerAuthClient:
    """Authentication client for Beurer FreshHome OAuth2."""

    def __init__(self, session: aiohttp.ClientSession | None = None) -> None:
        """Initialize the auth client.

        Args:
            session: Optional aiohttp ClientSession to use for requests.
                     If not provided, a new session will be created.
        """
        self._session = session
        self._own_session = session is None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self) -> None:
        """Close the aiohttp session if we own it."""
        if self._own_session and self._session is not None and not self._session.closed:
            await self._session.close()
            self._session = None

    async def _make_token_request(self, data: dict[str, Any]) -> LoginResponse:
        """Make a token request to the auth endpoint.

        Args:
            data: Form data to send in the request.

        Returns:
            LoginResponse with the authentication tokens.

        Raises:
            BeurerApiClientError: If the request fails or response is invalid.
        """
        session = await self._get_session()
        url = f"{AUTH_URL}{API_LOGIN}"

        try:
            async with session.post(url, data=data) as response:
                if response.status != 200:
                    text = await response.text()
                    raise BeurerApiClientError(
                        f"Authentication failed: HTTP {response.status} - {text}"
                    )

                json_data = await response.json()

                if "access_token" not in json_data:
                    raise BeurerApiClientError("Invalid response: access_token missing")

                return LoginResponse(
                    access_token=json_data["access_token"],
                    refresh_token=json_data.get("refresh_token", ""),
                    expires_in=json_data.get("expires_in", 3600),
                    token_type=json_data.get("token_type", "Bearer"),
                )

        except aiohttp.ClientError as err:
            raise BeurerApiClientError(f"Connection error: {err}") from err

    async def login(self, email: str, password: str) -> LoginResponse:
        """Authenticate with email and password.

        Args:
            email: User email address.
            password: User password.

        Returns:
            LoginResponse with access_token, refresh_token, expires_in, token_type.

        Raises:
            BeurerApiClientError: If authentication fails.
        """
        data = {
            "username": email,
            "password": password,
            "grant_type": "password",
            "client_id": "beurer_app",
            "scope": "openid profile email offline_access",
        }

        return await self._make_token_request(data)

    async def refresh_token(self, refresh_token: str) -> LoginResponse:
        """Refresh an access token using a refresh token.

        Args:
            refresh_token: The refresh token from a previous login.

        Returns:
            LoginResponse with new access_token, refresh_token, expires_in, token_type.

        Raises:
            BeurerApiClientError: If token refresh fails.
        """
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": "beurer_app",
        }

        return await self._make_token_request(data)

    def _decode_jwt_payload(self, token: str) -> dict[str, Any] | None:
        """Decode JWT payload without verification.

        Args:
            token: JWT access token.

        Returns:
            Decoded payload dictionary or None if decoding fails.
        """
        try:
            # Split the JWT into parts (header.payload.signature)
            parts = token.split(".")
            if len(parts) != 3:
                return None

            # Get the payload (second part)
            payload_b64 = parts[1]

            # Add padding if needed
            padding = 4 - len(payload_b64) % 4
            if padding != 4:
                payload_b64 += "=" * padding

            # Decode base64url
            payload_bytes = base64.urlsafe_b64decode(payload_b64)
            payload_str = payload_bytes.decode("utf-8")

            return json.loads(payload_str)

        except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as err:
            _LOGGER.debug("Failed to decode JWT: %s", err)
            return None

    def validate_token(self, access_token: str) -> bool:
        """Validate if an access token is still valid (not expired).

        Checks the JWT expiry with a 120-second buffer to account for
        network delays and clock skew.

        Args:
            access_token: The JWT access token to validate.

        Returns:
            True if the token is valid (not expired), False otherwise.
        """
        import time

        payload = self._decode_jwt_payload(access_token)
        if payload is None:
            return False

        # Get expiration time from payload
        exp = payload.get("exp")
        if exp is None:
            # No expiration claim, assume valid
            return True

        # Check expiry with 120-second buffer
        current_time = time.time()
        return current_time < (exp - 120)
