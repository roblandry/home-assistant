"""API for Fitbark bound to HASS OAuth."""
from asyncio import run_coroutine_threadsafe
import json
import logging
from typing import Dict, Union

import pyfitbark
import requests

from homeassistant import config_entries, core
from homeassistant.helpers import config_entry_oauth2_flow

_LOGGER = logging.getLogger(__name__)


class ConfigEntryFitbarkApi(pyfitbark.FitbarkApi):
    """Provide a Fitbark API tied into an OAuth2 based config entry."""

    def __init__(
        self,
        hass: core.HomeAssistant,
        config_entry: config_entries.ConfigEntry,
        implementation: config_entry_oauth2_flow.AbstractOAuth2Implementation,
    ):
        """Initialize the Config Entry Fitbark API."""
        self.hass = hass
        self.config_entry = config_entry
        self.session = config_entry_oauth2_flow.OAuth2Session(
            hass, config_entry, implementation
        )
        super().__init__(None, None, token=self.session.token)

    def refresh_tokens(self,) -> Dict[str, Union[str, int]]:
        """Refresh and return new Fitbark tokens using Home Assistant OAuth2 session."""
        run_coroutine_threadsafe(
            self.session.async_ensure_token_valid(), self.hass.loop
        ).result()

        return self.session.token


class UpdateRedirectUri:
    """Add and remove redirect url for auth."""

    def __init__(self, client_id, client_secret, callback_url):
        """Init."""
        self._client_id = client_id
        self._client_secret = client_secret
        self._callback_url = f"{callback_url}/auth/external/callback"

    def add_hass_url(self):
        """Add callback url for auth."""
        self.access_token = self.get_token()
        redirect_uri = self.get_redirect_urls()
        if self._callback_url not in redirect_uri:
            redirect_uri = f"{redirect_uri}\r{self._callback_url}"
            self.add_redirect_urls(redirect_uri)
            _LOGGER.debug("Added %s redirect url", self._callback_url)

    def remove_hass_url(self):
        """Remove the callback url for auth."""
        self.access_token = self.get_token()
        redirect_uri = self.get_redirect_urls()
        if self._callback_url in redirect_uri:
            redirect_uri = redirect_uri.replace(f"\r{self._callback_url}", "")
            self.add_redirect_urls(redirect_uri)
            _LOGGER.debug("Removed %s redirect url", self._callback_url)

    def make_request(self, method, url, payload, headers):
        """Request wrapper."""
        response = requests.request(method, url, json=payload, headers=headers)

        json_data = json.loads(response.text)
        # print(json_data)
        return json_data

    def get_token(self):
        """Get the token."""
        url = "https://app.fitbark.com/oauth/token"
        payload = {
            "grant_type": "client_credentials",
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "scope": "fitbark_open_api_2745H78RVS",
        }
        headers = {"Content-Type": "application/json", "Cache-Control": "no-cache"}

        json_data = self.make_request("POST", url, payload, headers)
        access_token = json_data["access_token"]
        return access_token

    def get_redirect_urls(self):
        """Get a list of redirect URLs."""
        url = "https://app.fitbark.com/api/v2/redirect_urls"
        payload = {}
        headers = {"Authorization": f"Bearer {self.access_token}"}
        json_data = self.make_request("GET", url, payload, headers)
        redirect_uri = json_data["redirect_uri"]
        return redirect_uri

    def add_redirect_urls(self, redirect_uri):
        """Add the redirect url."""
        url = "https://app.fitbark.com/api/v2/redirect_urls"
        payload = {"redirect_uri": redirect_uri}
        headers = {"Authorization": f"Bearer {self.access_token}"}
        json_data = self.make_request("POST", url, payload, headers)
        return json_data
