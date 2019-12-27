"""Support for ASUSWRT devices."""
import asyncio
import logging

import voluptuous as vol  # pylint: disable=import-error

from homeassistant.core import HomeAssistant  # pylint: disable=import-error

# pylint: disable=import-error
from homeassistant.config_entries import ConfigEntry

# pylint: disable=import-error
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_USERNAME,
    CONF_PORT,
    CONF_MODE,
    CONF_PROTOCOL,
)

# pylint: disable=import-error
from homeassistant.helpers import config_validation as cv

# pylint: disable=import-error
from homeassistant.helpers.discovery import async_load_platform

# pylint: disable=import-error
from .const import (
    DOMAIN,
    CONF_PUB_KEY,
    CONF_REQUIRE_IP,
    CONF_SENSORS,
    CONF_SSH_KEY,
    DATA_ASUSWRT,
    DEFAULT_SSH_PORT,
    SECRET_GROUP,
    SENSOR_TYPES,
)

_LOGGER = logging.getLogger(__name__)


CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_HOST): cv.string,
                vol.Required(CONF_USERNAME): cv.string,
                vol.Optional(CONF_PROTOCOL, default="ssh"): vol.In(["ssh", "telnet"]),
                vol.Optional(CONF_MODE, default="router"): vol.In(["router", "ap"]),
                vol.Optional(CONF_PORT, default=DEFAULT_SSH_PORT): cv.port,
                vol.Optional(CONF_REQUIRE_IP, default=True): cv.boolean,
                vol.Exclusive(CONF_PASSWORD, SECRET_GROUP): cv.string,
                vol.Exclusive(CONF_SSH_KEY, SECRET_GROUP): cv.isfile,
                vol.Exclusive(CONF_PUB_KEY, SECRET_GROUP): cv.isfile,
                vol.Optional(CONF_SENSORS): vol.All(
                    cv.ensure_list, [vol.In(SENSOR_TYPES)]
                ),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

PLATFORMS = ["device_tracker, sensor"]


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the asuswrt component."""
    from aioasuswrt.asuswrt import AsusWrt

    conf = config[DOMAIN]

    api = AsusWrt(
        conf[CONF_HOST],
        conf.get(CONF_PORT),
        conf.get(CONF_PROTOCOL) == "telnet",
        conf[CONF_USERNAME],
        conf.get(CONF_PASSWORD, ""),
        conf.get("ssh_key", conf.get("pub_key", "")),
        conf.get(CONF_MODE),
        conf.get(CONF_REQUIRE_IP),
    )

    await api.connection.async_connect()
    if not api.is_connected:
        _LOGGER.error("Unable to setup asuswrt component")
        return False

    hass.data[DATA_ASUSWRT] = api

    hass.async_create_task(
        async_load_platform(
            hass, "sensor", DOMAIN, config[DOMAIN].get(CONF_SENSORS), config
        )
    )
    hass.async_create_task(
        async_load_platform(hass, "device_tracker", DOMAIN, {}, config)
    )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up asuswrt_integration from a config entry."""
    # for component in PLATFORMS:
    #    hass.async_create_task(
    #        hass.config_entries.async_forward_entry_setup(entry, component)
    #    )

    # return True
    _LOGGER.error("SETUP of ASUSwrt Config")

    from aioasuswrt.asuswrt import AsusWrt

    api = AsusWrt(
        entry.data[CONF_HOST],
        entry.data[CONF_PORT],
        entry.data[CONF_PROTOCOL] == "telnet",
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD, ""],
        (entry.data["ssh_key"], entry.data["pub_key", ""]),
        entry.data[CONF_MODE],
        entry.data[CONF_REQUIRE_IP],
    )

    await api.connection.async_connect()
    if not api.is_connected:
        _LOGGER.error("Unable to setup asuswrt component")
        return False

    hass.data[DATA_ASUSWRT] = api

    hass.async_create_task(
        async_load_platform(hass, "sensor", DOMAIN, entry.data[CONF_SENSORS], entry)
    )
    hass.async_create_task(
        async_load_platform(hass, "device_tracker", DOMAIN, {}, entry)
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
