"""Support for the FitBark API."""
import logging

from homeassistant.const import ATTR_ATTRIBUTION
from homeassistant.helpers.entity import Entity

from . import API, DEVICES, DOMAIN

_LOGGER = logging.getLogger(__name__)


ATTR_CLIENT_ID = "client_id"
ATTR_CLIENT_SECRET = "client_secret"
ATTR_REDIRECT_URI = "redirect_uri"
ATTR_ACCESS_TOKEN = "access_token"
ATTR_REFRESH_TOKEN = "refresh_token"
ATTR_EXPIRES_DATE = "expires_date"

ATTRIBUTION = "Data provided by fitbark.com"

FITBARK_CONFIG_FILE = "fitbark_auth.json"


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Somfy switch platform."""

    def get_dogs():
        """Retrieve sensors."""
        devices = hass.data[DOMAIN][DEVICES]

        return [
            FitBarkSensor(device, hass.data[DOMAIN][API])
            for device in devices
            # if Category.CAMERA.value in device.categories
        ]

    async_add_entities(await hass.async_add_executor_job(get_dogs), True)


class FitBarkSensor(Entity):
    """Implementation of a FitBark sensor."""

    def __init__(self, dog, api):
        """Initialize the FitBark sensor."""
        dog = dog["dog"]
        self._api = api
        self._name = None
        self._slug = dog["slug"]
        self.entity_id = "sensor." + self._slug.replace("-", "_")
        self._state = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return "mdi:dog-side"

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    def update(self):
        """Get the latest data from the FitBark API and update the states."""
        dog = self._api.get_dog(self._slug)
        dog = dog["dog"]

        # Delete unwanted attrs
        dog.pop("slug", True)
        dog.pop("picture_hash", True)
        dog.pop("country", True)
        dog.pop("zip", True)
        dog.pop("tzoffset", True)
        dog.pop("tzname", True)

        # get name and bluetooth_id for entity_id
        bluetooth_id = dog.pop("bluetooth_id", None)
        self._name = dog.pop("name", None)
        name = fmt_name(self._name)
        self.entity_id = f"sensor.{name}_{bluetooth_id}"

        # set state to hourly activity average
        self._state = int(dog["hourly_average"])

        # parse medical condition list into dict
        m_condition = []
        medical_conditions = dog.pop("medical_conditions", None)
        if medical_conditions:
            for condition in medical_conditions:
                m_condition.append(condition["name"])
            dog.update({"medical_conditions": m_condition})

        # sort dict alphabetically
        sorted_dog = {}
        for k, v in sorted(dog.items()):
            sorted_dog.update({k: v})

        # add attribution
        sorted_dog.update({ATTR_ATTRIBUTION: ATTRIBUTION})

        # update attrs
        self._attributes = sorted_dog


def fmt_name(name):
    """Format name."""
    name = name.lower()

    return name
