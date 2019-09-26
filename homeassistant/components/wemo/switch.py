"""Support for WeMo switches."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any

from pywemo import CoffeeMaker, Insight, Maker, StandbyState, Switch

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_OFF, STATE_ON, STATE_STANDBY, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN as WEMO_DOMAIN
from .entity import WemoBinaryStateEntity
from .wemo_device import DeviceCoordinator

SCAN_INTERVAL = timedelta(seconds=10)
PARALLEL_UPDATES = 0

ATTR_COFFEMAKER_MODE = "coffeemaker_mode"
ATTR_CURRENT_STATE_DETAIL = "state_detail"
ATTR_ON_LATEST_TIME = "on_latest_time"
ATTR_ON_TODAY_TIME = "on_today_time"
ATTR_ON_TOTAL_TIME = "on_total_time"
ATTR_POWER_THRESHOLD = "power_threshold_w"
ATTR_SENSOR_STATE = "sensor_state"
ATTR_SWITCH_MODE = "switch_mode"
<<<<<<< HEAD
=======
ATTR_CURRENT_STATE_DETAIL = "state_detail"
ATTR_COFFEMAKER_MODE = "coffeemaker_mode"
ATTR_CROCKPOT_MODE = "crockpot_mode"
ATTR_CROCKPOT_TIME = "crockpot_time"
ATTR_CROCKPOT_COOKEDTIME = "crockpot_cookedtime"
ATTR_CROCKPOT_TIMESTAMP = "crockpot_timestamp"

>>>>>>> 3d5c72c6d1 (WeMo Crockpot)

MAKER_SWITCH_MOMENTARY = "momentary"
MAKER_SWITCH_TOGGLE = "toggle"


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WeMo switches."""

    async def _discovered_wemo(coordinator: DeviceCoordinator) -> None:
        """Handle a discovered Wemo device."""
        async_add_entities([WemoSwitch(coordinator)])

    async_dispatcher_connect(hass, f"{WEMO_DOMAIN}.switch", _discovered_wemo)

    await asyncio.gather(
        *(
            _discovered_wemo(coordinator)
            for coordinator in hass.data[WEMO_DOMAIN]["pending"].pop("switch")
        )
    )


class WemoSwitch(WemoBinaryStateEntity, SwitchEntity):
    """Representation of a WeMo switch."""

<<<<<<< HEAD
    # All wemo devices used with WemoSwitch are subclasses of Switch.
    wemo: Switch
=======
    def __init__(self, device):
        """Initialize the WeMo switch."""
        self.wemo = device
        self.insight_params = None
        self.maker_params = None
        self.coffeemaker_mode = None
        self.crockpot_params = None
        self._state = None
        self._mode_string = None
        self._available = True
        self._update_lock = None
        self._model_name = self.wemo.model_name
        self._name = self.wemo.name
        self._serialnumber = self.wemo.serialnumber

    def _subscription_callback(self, _device, _type, _params):
        """Update the state by the Wemo device."""
        _LOGGER.info("Subscription update for %s", self.name)
        updated = self.wemo.subscription_update(_type, _params)
        self.hass.add_job(self._async_locked_subscription_callback(not updated))

    async def _async_locked_subscription_callback(self, force_update):
        """Handle an update from a subscription."""
        # If an update is in progress, we don't do anything
        if self._update_lock.locked():
            return

        await self._async_locked_update(force_update)
        self.async_schedule_update_ha_state()

    @property
    def unique_id(self):
        """Return the ID of this WeMo switch."""
        return self._serialnumber

    @property
    def name(self):
        """Return the name of the switch if any."""
        return self._name

    @property
    def device_info(self):
        """Return the device info."""
        return {"name": self._name, "identifiers": {(WEMO_DOMAIN, self._serialnumber)}}
>>>>>>> 3d5c72c6d1 (WeMo Crockpot)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes of the device."""
        attr: dict[str, Any] = {}
        if isinstance(self.wemo, Maker):
            # Is the maker sensor on or off.
            if self.wemo.has_sensor:
                # Note a state of 1 matches the WeMo app 'not triggered'!
                if self.wemo.sensor_state:
                    attr[ATTR_SENSOR_STATE] = STATE_OFF
                else:
                    attr[ATTR_SENSOR_STATE] = STATE_ON

            # Is the maker switch configured as toggle(0) or momentary (1).
            if self.wemo.switch_mode:
                attr[ATTR_SWITCH_MODE] = MAKER_SWITCH_MOMENTARY
            else:
                attr[ATTR_SWITCH_MODE] = MAKER_SWITCH_TOGGLE

<<<<<<< HEAD
        if isinstance(self.wemo, (Insight, CoffeeMaker)):
=======
        if (
            self.insight_params
            or (self.coffeemaker_mode is not None)
            or (self.crockpot_params is not None)
        ):
>>>>>>> 3d5c72c6d1 (WeMo Crockpot)
            attr[ATTR_CURRENT_STATE_DETAIL] = self.detail_state

        if isinstance(self.wemo, Insight):
            attr[ATTR_ON_LATEST_TIME] = self.as_uptime(self.wemo.on_for)
            attr[ATTR_ON_TODAY_TIME] = self.as_uptime(self.wemo.today_on_time)
            attr[ATTR_ON_TOTAL_TIME] = self.as_uptime(self.wemo.total_on_time)
            attr[ATTR_POWER_THRESHOLD] = self.wemo.threshold_power_watts

        if isinstance(self.wemo, CoffeeMaker):
            attr[ATTR_COFFEMAKER_MODE] = self.wemo.mode

        if self.crockpot_params is not None:
            attr[ATTR_CROCKPOT_MODE] = self.crockpot_params["mode"]
            attr[ATTR_CROCKPOT_TIME] = self.crockpot_params["time"]
            attr[ATTR_CROCKPOT_COOKEDTIME] = self.crockpot_params["cookedTime"]
            t = datetime.fromtimestamp(float(self.crockpot_params["timeStamp"]))
            attr[ATTR_CROCKPOT_TIMESTAMP] = t.strftime("%Y-%m-%d %H:%M:%S")
            # attr[ATTR_CROCKPOT_TIMESTAMP] = time.strftime("%Z - %Y/%m/%d, %H:%M:%S", time.localtime(self.crockpot_params["timeStamp"]))

        # _LOGGER.debug(f"Attr: {attr}")

        return attr

    @staticmethod
    def as_uptime(_seconds: int) -> str:
        """Format seconds into uptime string in the format: 00d 00h 00m 00s."""
        uptime = datetime(1, 1, 1) + timedelta(seconds=_seconds)
        return "{:0>2d}d {:0>2d}h {:0>2d}m {:0>2d}s".format(
            uptime.day - 1, uptime.hour, uptime.minute, uptime.second
        )

    @property
    def detail_state(self) -> str:
        """Return the state of the device."""
<<<<<<< HEAD
        if isinstance(self.wemo, CoffeeMaker):
            return self.wemo.mode_string
        if isinstance(self.wemo, Insight):
            standby_state = self.wemo.standby_state
            if standby_state == StandbyState.ON:
=======
        if self.coffeemaker_mode is not None:
            return self._mode_string
        if self.crockpot_params is not None:
            return self._mode_string
        if self.insight_params:
            standby_state = int(self.insight_params["state"])
            if standby_state == WEMO_ON:
>>>>>>> 3d5c72c6d1 (WeMo Crockpot)
                return STATE_ON
            if standby_state == StandbyState.OFF:
                return STATE_OFF
            if standby_state == StandbyState.STANDBY:
                return STATE_STANDBY
            return STATE_UNKNOWN
        assert False  # Unreachable code statement.

    @property
    def icon(self) -> str | None:
        """Return the icon of device based on its type."""
        if isinstance(self.wemo, CoffeeMaker):
            return "mdi:coffee"
        return None

    def turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
<<<<<<< HEAD
        with self._wemo_call_wrapper("turn on"):
=======
        if self._model_name == "Crockpot":
            self.wemo.set_state(50)  # 50 = warm
        else:
>>>>>>> 3d5c72c6d1 (WeMo Crockpot)
            self.wemo.on()

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
<<<<<<< HEAD
        with self._wemo_call_wrapper("turn off"):
            self.wemo.off()
=======
        self.wemo.off()

    async def async_added_to_hass(self):
        """Wemo switch added to HASS."""
        # Define inside async context so we know our event loop
        self._update_lock = asyncio.Lock()

        registry = SUBSCRIPTION_REGISTRY
        await self.hass.async_add_job(registry.register, self.wemo)
        registry.on(self.wemo, None, self._subscription_callback)

    async def async_update(self):
        """Update WeMo state.

        Wemo has an aggressive retry logic that sometimes can take over a
        minute to return. If we don't get a state after 5 seconds, assume the
        Wemo switch is unreachable. If update goes through, it will be made
        available again.
        """
        # If an update is in progress, we don't do anything
        if self._update_lock.locked():
            return

        try:
            with async_timeout.timeout(5):
                await asyncio.shield(self._async_locked_update(True))
        except asyncio.TimeoutError:
            _LOGGER.warning("Lost connection to %s", self.name)
            self._available = False

    async def _async_locked_update(self, force_update):
        """Try updating within an async lock."""
        async with self._update_lock:
            await self.hass.async_add_job(self._update, force_update)

    def _update(self, force_update):
        """Update the device state."""
        try:
            self._state = self.wemo.get_state(force_update)

            if self._model_name == "Insight":
                self.insight_params = self.wemo.insight_params
                self.insight_params["standby_state"] = self.wemo.get_standby_state
            elif self._model_name == "Maker":
                self.maker_params = self.wemo.maker_params
            elif self._model_name == "CoffeeMaker":
                self.coffeemaker_mode = self.wemo.mode
                self._mode_string = self.wemo.mode_string
            elif self._model_name == "Crockpot":
                self.crockpot_params = self.wemo.attributes
                self._mode_string = self.wemo.mode_string

            if not self._available:
                _LOGGER.info("Reconnected to %s", self.name)
                self._available = True
        except AttributeError as err:
            _LOGGER.warning("Could not update status for %s (%s)", self.name, err)
            self._available = False
>>>>>>> 3d5c72c6d1 (WeMo Crockpot)
