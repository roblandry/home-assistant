"""Constants for the asuswrt_integration integration."""

DOMAIN = "asuswrt_config"
# DOMAIN = "asuswrt"

CONF_PUB_KEY = "pub_key"
CONF_REQUIRE_IP = "require_ip"
CONF_SENSORS = "sensors"
CONF_SSH_KEY = "ssh_key"

DATA_ASUSWRT = DOMAIN
DEFAULT_SSH_PORT = 22

SECRET_GROUP = "Password or SSH Key"

SENSOR_TYPES = [
    "upload_speed",
    "download_speed",
    "download",
    "upload",
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
]
