"""Asuswrt status sensors."""
import logging

from homeassistant.helpers.entity import Entity

from .const import DATA_ASUSWRT

_LOGGER = logging.getLogger(__name__)

SENSOR_W_ATTRS = {
    "dhcp",
    "model",
    "qos",
    "reboot",
    "wlan",
    "2g_wifi",
    "2g_guest_1",
    "2g_guest_2",
    "2g_guest_3",
    "5g_wifi",
    "5g_guest_1",
    "5g_guest_2",
    "5g_guest_3",
    "firmware",
}


async def async_setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the asuswrt sensors."""
    if discovery_info is None:
        return

    api = hass.data[DATA_ASUSWRT]

    devices = []

    if "download" in discovery_info:
        devices.append(AsuswrtTotalRXSensor(api))
    if "upload" in discovery_info:
        devices.append(AsuswrtTotalTXSensor(api))
    if "download_speed" in discovery_info:
        devices.append(AsuswrtRXSensor(api))
    if "upload_speed" in discovery_info:
        devices.append(AsuswrtTXSensor(api))
    for attr_sensor in SENSOR_W_ATTRS:
        if attr_sensor in discovery_info:
            devices.append(AsuswrtSensorWAttrs(api, attr_sensor))

    add_entities(devices)


class AsuswrtSensor(Entity):
    """Representation of a asuswrt sensor."""

    _name = "generic"

    def __init__(self, api):
        """Initialize the sensor."""
        self._api = api
        self._state = None
        self._rates = None
        self._speed = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    async def async_update(self):
        """Fetch status from asuswrt."""
        self._rates = await self._api.async_get_bytes_total()
        self._speed = await self._api.async_get_current_transfer_rates()


class AsuswrtRXSensor(AsuswrtSensor):
    """Representation of a asuswrt download speed sensor."""

    _name = "Asuswrt Download Speed"
    _unit = "Mbit/s"

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit

    async def async_update(self):
        """Fetch new state data for the sensor."""
        await super().async_update()
        if self._speed:
            self._state = round(self._speed[0] / 125000, 2)


class AsuswrtTXSensor(AsuswrtSensor):
    """Representation of a asuswrt upload speed sensor."""

    _name = "Asuswrt Upload Speed"
    _unit = "Mbit/s"

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit

    async def async_update(self):
        """Fetch new state data for the sensor."""
        await super().async_update()
        if self._speed:
            self._state = round(self._speed[1] / 125000, 2)


class AsuswrtTotalRXSensor(AsuswrtSensor):
    """Representation of a asuswrt total download sensor."""

    _name = "Asuswrt Download"
    _unit = "Gigabyte"

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit

    async def async_update(self):
        """Fetch new state data for the sensor."""
        await super().async_update()
        if self._rates:
            self._state = round(self._rates[0] / 1000000000, 1)


class AsuswrtTotalTXSensor(AsuswrtSensor):
    """Representation of a asuswrt total upload sensor."""

    _name = "Asuswrt Upload"
    _unit = "Gigabyte"

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit

    async def async_update(self):
        """Fetch new state data for the sensor."""
        await super().async_update()
        if self._rates:
            self._state = round(self._rates[1] / 1000000000, 1)


class AsuswrtSensorWAttrs(Entity):
    """Representation of a asuswrt sensor with attributes."""

    def __init__(self, api, attr_sensor):
        """Initialize the sensor."""
        self._api = api
        self._state = None
        self._name = f"Asuswrt {format_name(attr_sensor)}"
        self._type = attr_sensor
        self._sensor = attr_sensor.upper()
        self._attributes = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def device_state_attributes(self):
        """Return the attributes of the sensor."""
        return self._attributes

    async def async_update(self):
        """Fetch new state data for the sensor."""
        response = await self._api.async_get_nvram(self._sensor)

        if self._type == "2g_wifi":
            self._state = bool_onoff(response.pop("wl0_bss_enabled", None))
        elif self._type == "2g_guest_1":
            self._state = bool_onoff(response.pop("wl0.1_bss_enabled", None))
        elif self._type == "2g_guest_2":
            self._state = bool_onoff(response.pop("wl0.2_bss_enabled", None))
        elif self._type == "2g_guest_3":
            self._state = bool_onoff(response.pop("wl0.3_bss_enabled", None))
        elif self._type == "5g_wifi":
            self._state = bool_onoff(response.pop("wl1_bss_enabled", None))
        elif self._type == "5g_guest_1":
            self._state = bool_onoff(response.pop("wl1.1_bss_enabled", None))
        elif self._type == "5g_guest_2":
            self._state = bool_onoff(response.pop("wl1.2_bss_enabled", None))
        elif self._type == "5g_guest_3":
            self._state = bool_onoff(response.pop("wl1.3_bss_enabled", None))
        elif self._type == "dhcp":
            self._state = bool_onoff(response.pop("dhcp_enable_x", None))
        elif self._type == "qos":
            self._state = bool_onoff(response.pop("qos_enable", None))
        elif self._type == "model":
            self._state = response.pop("model", None)
        elif self._type == "wlan":
            self._state = response.pop("wan_ipaddr", None)
        elif self._type == "reboot":
            self._state = bool_onoff(response.pop("reboot_schedule_enable", None))
        elif self._type == "firmware":
            self._state = response.pop("buildno", None)
        else:
            self._state = None

        self._attributes = response


def bool_onoff(val):
    """Convert 1|0 to on|off."""
    if int(val) == 1:
        return "on"
    else:
        return "off"


def format_name(name):
    """Format name."""
    name = name.replace("_", " ")
    name = name.title()
    return name
