"""Config flow for Beurer FreshHome."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN
from .api import BeurerAuthClient, BeurerApiClientError

_LOGGER = logging.getLogger(__name__)


class BeurerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Beurer FreshHome."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            email = user_input[CONF_EMAIL]
            password = user_input[CONF_PASSWORD]

            auth_client = None
            try:
                auth_client = BeurerAuthClient()
                _LOGGER.debug("Attempting login for email: %s", email)
                login_response = await auth_client.login(email, password)
                _LOGGER.debug("Login successful for email: %s", email)

                # Create config entry with token data
                return self.async_create_entry(
                    title=email,
                    data={
                        "email": email,
                        "access_token": login_response.access_token,
                        "refresh_token": login_response.refresh_token,
                        "expires_in": login_response.expires_in,
                        "token_type": login_response.token_type,
                    },
                )

            except BeurerApiClientError as err:
                error_str = str(err).lower()
                _LOGGER.error("Beurer API error during login: %s", err)
                if "invalid_grant" in error_str:
                    errors["base"] = "invalid_auth"
                elif "connection" in error_str:
                    errors["base"] = "cannot_connect"
                else:
                    errors["base"] = "unknown"
            except Exception as err:
                _LOGGER.exception("Unexpected error during login: %s", err)
                errors["base"] = "unknown"
            finally:
                if auth_client is not None:
                    await auth_client.close()

        # Show form
        data_schema = vol.Schema(
            {
                vol.Required(CONF_EMAIL): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )
