# Core version
"""Support for WeMo switches."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any

# CrockPot +>>
from pywemo import CrockPot, CoffeeMaker, Insight, Maker, StandbyState, Switch
# <<

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_OFF, STATE_ON, STATE_STANDBY, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

# CrockPot +>>
from .const import DOMAIN as WEMO_DOMAIN, SERVICE_SET_TIMER
# <<
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
# CrockPot
ATTR_CROCKPOT_MODE = "crockpot_mode"
ATTR_CROCKPOT_TIME = "crockpot_time"
ATTR_CROCKPOT_COOKEDTIME = "crockpot_cookedtime"
ATTR_CROCKPOT_TIMESTAMP = "crockpot_timestamp"
ATTR_TARGET_TIME = "target_time"
# <<

MAKER_SWITCH_MOMENTARY = "momentary"
MAKER_SWITCH_TOGGLE = "toggle"

# CrockPot >>
CROCKPOT_SWITCHES = {"Warm": 50, "Low": 51, "High": 52}
# <<


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

    # All wemo devices used with WemoSwitch are subclasses of Switch.
    wemo: Switch

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

        if isinstance(self.wemo, (Insight, CoffeeMaker)):
            attr[ATTR_CURRENT_STATE_DETAIL] = self.detail_state

        if isinstance(self.wemo, Insight):
            attr[ATTR_ON_LATEST_TIME] = self.as_uptime(self.wemo.on_for)
            attr[ATTR_ON_TODAY_TIME] = self.as_uptime(self.wemo.today_on_time)
            attr[ATTR_ON_TOTAL_TIME] = self.as_uptime(self.wemo.total_on_time)
            attr[ATTR_POWER_THRESHOLD] = self.wemo.threshold_power_watts

        if isinstance(self.wemo, CoffeeMaker):
            attr[ATTR_COFFEMAKER_MODE] = self.wemo.mode

        # Crockpot >>
        if isinstance(self.wemo, CrockPot):

            if self.crockpot_params:
                attr[ATTR_CURRENT_STATE_DETAIL] = self.detail_state

            if self.crockpot_params is not None:
                attr[ATTR_CROCKPOT_MODE] = self.crockpot_params["mode"]
                attr[ATTR_CROCKPOT_TIME] = self.crockpot_params["time"]
                attr[ATTR_CROCKPOT_COOKEDTIME] = self.crockpot_params["cookedTime"]
                t = datetime.fromtimestamp(float(self.crockpot_params["timeStamp"]))
                attr[ATTR_CROCKPOT_TIMESTAMP] = t.strftime("%Y-%m-%d %H:%M:%S")
            # _LOGGER.debug(f"Attr: {attr}")
        # <<

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
        if isinstance(self.wemo, CoffeeMaker):
            return self.wemo.mode_string
        if isinstance(self.wemo, Insight):
            standby_state = self.wemo.standby_state
            if standby_state == StandbyState.ON:
                return STATE_ON
            if standby_state == StandbyState.OFF:
                return STATE_OFF
            if standby_state == StandbyState.STANDBY:
                return STATE_STANDBY
            return STATE_UNKNOWN
        # CrockPot >>
        if isinstance(self.wemo, CrockPot):
            if self.crockpot_params is not None:
                return self._mode_string
        # <<
        assert False  # Unreachable code statement.

    @property
    def icon(self) -> str | None:
        """Return the icon of device based on its type."""
        if isinstance(self.wemo, CoffeeMaker):
            return "mdi:coffee"
        # CrockPot >>
        if isinstance(self.wemo, CrockPot):
            return "mdi:pot-steam"
        # <<
        return None

    def turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        with self._wemo_call_wrapper("turn on"):
            # CrockPot >>
            if isinstance(self.wemo, CrockPot):
                self.wemo.set_state(int(CROCKPOT_SWITCHES[self._theSwitch]))
            else:
            # <<
                self.wemo.on()

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        with self._wemo_call_wrapper("turn off"):
            self.wemo.off()

    # CrockPot >>
    def set_timer(self, **kwargs: Any) -> None:
        """Set Timer."""
        with self._wemo_call_wrapper("set timer"):
            if timer:
                # self.wemo.set_time(timer)
                self.wemo.set_state(int(CROCKPOT_SWITCHES[self._theSwitch]), timer)
    # <<
