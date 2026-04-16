"""API client for Beurer FreshHome."""

from __future__ import annotations

import base64
import json
import logging
from typing import Any

import aiohttp

from .const import API_GET_DEVICES, API_LOGIN, AUTH_URL, BASE_URL
from .models import BeurerDevice, LoginResponse

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
            "client_id": "beurersso",
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
            "client_id": "beurersso",
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


class BeurerApiClient:
    """REST API client for Beurer FreshHome device operations."""

    def __init__(
        self,
        session: aiohttp.ClientSession | None = None,
        auth_client: BeurerAuthClient | None = None,
    ) -> None:
        """Initialize the API client.

        Args:
            session: Optional aiohttp ClientSession to use for requests.
                     If not provided, a new session will be created.
            auth_client: Optional BeurerAuthClient for token refresh operations.
                         If not provided, a new instance will be created.
        """
        self._session = session
        self._own_session = session is None
        self._auth_client = auth_client or BeurerAuthClient(session)

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
        await self._auth_client.close()

    async def _make_authenticated_request(
        self,
        method: str,
        url: str,
        access_token: str,
        refresh_token: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make an authenticated request with automatic token refresh on 401.

        Args:
            method: HTTP method (GET, POST, etc.).
            url: Request URL.
            access_token: Current access token for Bearer authentication.
            refresh_token: Optional refresh token for token refresh on 401.
            **kwargs: Additional arguments to pass to the request.

        Returns:
            JSON response as dictionary.

        Raises:
            BeurerApiClientError: If the request fails or token refresh fails.
        """
        session = await self._get_session()
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {access_token}"

        try:
            async with session.request(
                method, url, headers=headers, **kwargs
            ) as response:
                if response.status == 401 and refresh_token:
                    # Token expired, try to refresh
                    _LOGGER.debug("Access token expired, attempting refresh")
                    new_tokens = await self._auth_client.refresh_token(refresh_token)
                    # Retry with new token
                    headers["Authorization"] = f"Bearer {new_tokens.access_token}"
                    async with session.request(
                        method, url, headers=headers, **kwargs
                    ) as retry_response:
                        if retry_response.status != 200:
                            text = await retry_response.text()
                            raise BeurerApiClientError(
                                f"API request failed after token refresh: HTTP {retry_response.status} - {text}"
                            )
                        return await retry_response.json()

                if response.status != 200:
                    text = await response.text()
                    raise BeurerApiClientError(
                        f"API request failed: HTTP {response.status} - {text}"
                    )

                return await response.json()

        except aiohttp.ClientError as err:
            raise BeurerApiClientError(f"Connection error: {err}") from err

    async def get_devices(
        self, email: str, access_token: str, refresh_token: str | None = None
    ) -> list[BeurerDevice]:
        """Get list of devices for a user.

        Endpoint: GET /api/users/list?email=<email>

        Args:
            email: User email address.
            access_token: Valid access token for authentication.
            refresh_token: Optional refresh token for automatic token refresh.

        Returns:
            List of BeurerDevice objects.

        Raises:
            BeurerApiClientError: If the request fails.
        """
        url = f"{BASE_URL}{API_GET_DEVICES}"
        params = {"email": email}

        response_data = await self._make_authenticated_request(
            "GET", url, access_token, refresh_token, params=params
        )

        devices = []
        devices_data = response_data.get("devices", [])

        for device_data in devices_data:
            device = BeurerDevice(
                id=device_data.get("id", ""),
                name=device_data.get("name", ""),
                model=device_data.get("model", ""),
                user=device_data.get("user", ""),
            )
            devices.append(device)

        return devices
