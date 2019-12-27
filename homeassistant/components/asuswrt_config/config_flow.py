"""Config flow for asuswrt_integration integration."""
import logging

import voluptuous as vol

from homeassistant import core, config_entries, exceptions
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_USERNAME,
    CONF_PORT,
    CONF_MODE,
    CONF_PROTOCOL,
)

# pylint: disable=import-error
from .const import DOMAIN, CONF_PUB_KEY, CONF_REQUIRE_IP, CONF_SENSORS, CONF_SSH_KEY

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        CONF_HOST: str,
        CONF_USERNAME: str,
        CONF_PROTOCOL: str,
        CONF_MODE: str,
        CONF_PORT: str,
        CONF_REQUIRE_IP: bool,
        CONF_PASSWORD: str,
        CONF_SSH_KEY: str,
        CONF_PUB_KEY: str,
        CONF_SENSORS: str,
    }
)


async def validate_input(hass: core.HomeAssistant, data):
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """
    # TODO validate the data can be used to set up a connection.
    # If you cannot connect:
    # throw CannotConnect
    # If the authentication is wrong:
    # InvalidAuth

    # Return some info we want to store in the config entry.
    return {"title": "Asuswrt Config"}


class DomainConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for asuswrt_integration."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)

                return self.async_create_entry(title=info["title"], data=user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""

    _LOGGER.error("Cannot Connect")


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""

    _LOGGER.error("Invalid Auth")
