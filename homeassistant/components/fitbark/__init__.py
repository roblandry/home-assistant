"""
Support for Fitbark.

For more details about this component, please refer to the documentation at
https://home-assistant.io/integrations/fitbark/
"""
import asyncio
from datetime import timedelta
import logging

from requests import HTTPError
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import config_entry_oauth2_flow, config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import HomeAssistantType
from homeassistant.util import Throttle

from . import api, config_flow

API = "api"

DEVICES = "DEVICES"

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=30)

DOMAIN = "fitbark"

CONF_CLIENT_ID = "client_id"
CONF_CLIENT_SECRET = "client_secret"

# SOMFY_AUTH_CALLBACK_PATH = "/auth/somfy/callback"
# SOMFY_AUTH_START = "/auth/somfy"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_CLIENT_ID): cv.string,
                vol.Required(CONF_CLIENT_SECRET): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

FITBARK_COMPONENTS = ["sensor"]


async def async_setup(hass, config):
    """Set up the Fitbark component."""
    hass.data[DOMAIN] = {}

    if DOMAIN not in config:
        return True

    # TODO: Adds redirect urls to allow config.
    # not necessary this early, but not sure how to get
    # config data later.
    # Also would like to remove later.
    redir_api = api.UpdateRedirectUri(
        config[DOMAIN][CONF_CLIENT_ID],
        config[DOMAIN][CONF_CLIENT_SECRET],
        hass.config.api.base_url,
    )
    redir_api.add_hass_url()

    config_flow.FitbarkFlowHandler.async_register_implementation(
        hass,
        config_entry_oauth2_flow.LocalOAuth2Implementation(
            hass,
            DOMAIN,
            config[DOMAIN][CONF_CLIENT_ID],
            config[DOMAIN][CONF_CLIENT_SECRET],
            "https://app.fitbark.com/oauth/authorize",
            "https://app.fitbark.com/oauth/token",
        ),
    )

    return True


async def async_setup_entry(hass: HomeAssistantType, entry: ConfigEntry):
    """Set up Fitbark from a config entry."""
    # Backwards compat
    if "auth_implementation" not in entry.data:
        hass.config_entries.async_update_entry(
            entry, data={**entry.data, "auth_implementation": DOMAIN}
        )

    implementation = await config_entry_oauth2_flow.async_get_config_entry_implementation(
        hass, entry
    )

    hass.data[DOMAIN][API] = api.ConfigEntryFitbarkApi(hass, entry, implementation)

    await update_all_devices(hass)

    for component in FITBARK_COMPONENTS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )

    return True


async def async_unload_entry(hass: HomeAssistantType, entry: ConfigEntry):
    """Unload a config entry."""
    hass.data[DOMAIN].pop(API, None)
    await asyncio.gather(
        *[
            hass.config_entries.async_forward_entry_unload(entry, component)
            for component in FITBARK_COMPONENTS
        ]
    )
    return True


class FitbarkEntity(Entity):
    """Representation of a generic Fitbark device."""

    def __init__(self, device, FitbarkApi):
        """Initialize the FitBark device."""
        self.device = device
        self.api = FitbarkApi
        self.name = self.device["name"]
        self.unique_id = self.device["slug"].replace("-", "_")

    @property
    def unique_id(self):
        """Return the unique id base on the id returned by FitBark."""
        return self.device["slug"].replace("-", "_")

    @property
    def name(self):
        """Return the name of the device."""
        return self.device["name"]

    @property
    def device_info(self):
        """Return device specific attributes.

        Implemented by platform classes.
        """
        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": self.name,
            "model": self.device.type,
            # "via_hub": (DOMAIN, self.device.site_id),
            # For the moment, FitBark only returns their own device.
            "manufacturer": "FitBark",
        }

    async def async_update(self):
        """Update the device with the latest data."""
        await update_all_devices(self.hass)
        devices = self.hass.data[DOMAIN][DEVICES]
        self.device = next((d for d in devices if d.id == self.device.id), self.device)

    def has_capability(self, capability):
        """Test if device has a capability."""
        capabilities = self.device.capabilities
        return bool([c for c in capabilities if c.name == capability])


@Throttle(SCAN_INTERVAL)
async def update_all_devices(hass):
    """Update all the devices."""
    try:
        data = hass.data[DOMAIN]
        user_dogs = await hass.async_add_executor_job(data[API].get_user_related_dogs)
        user_dogs = user_dogs["dog_relations"]
        if user_dogs:
            # for dog in user_dogs:
            #     _LOGGER.debug(dog)
            #     data[DEVICES] = dog["dog"]
            data[DEVICES] = user_dogs
        else:
            data[DEVICES] = {}
    except HTTPError as err:
        _LOGGER.warning("Cannot update devices: %s", err.response.status_code)
