"""Constants for the Beurer FreshHome integration."""

from __future__ import annotations

DOMAIN = "beurer"

# Config flow constants
CONF_EMAIL = "email"
CONF_PASSWORD = "password"

# API URLs
BASE_URL = "https://freshhome.connect.beurer.com"
AUTH_URL = "https://beurer-sso-prod.azurewebsites.net"
SIGNALR_URL = "wss://freshhome.connect.beurer.com/messageHub"

# API endpoints
API_LOGIN = "/connect/token"
API_GET_DEVICES = "/api/users/list"
API_ADD_DEVICE = "/api/users/deviceAdd"
API_DELETE_DEVICE = "/api/users/deviceDelete"
API_RENAME_DEVICE = "/api/users/deviceRename"
API_GET_BORDER_VALUES = "/api/devices/borderValues"
API_SET_BORDER_VALUES = "/api/devices/borderValues"
API_GET_STATISTICS = "/api/devices/statistics"
API_GET_SCHEDULES = "/api/deviceSchedules/list"
API_ADD_SCHEDULE = "/api/deviceSchedules/add"
API_DELETE_SCHEDULE = "/api/deviceSchedules/delete"

# SignalR method names
SEND_METHOD = "SendCommand"
RECEIVE_METHOD = "ReceiveMessage"

# Timeout constants
DISCONNECT_TIMEOUT = 15

# Protocol constants
PROTOCOL_VERSION = "2018-08-31"
DEFAULT_SOURCE = "Android"
DEFAULT_VALUE_TYPE = "int"
DEFAULT_TYPE = "cmd"
MESSAGE_TYPE_DEVICE = "device"

# Device types
DEVICE_TYPE_LR500 = "LR500"
DEVICE_TYPE_LR400 = "LR400"
DEVICE_TYPE_LR405 = "LR405"

# Fan speed mappings (value -> percentage)
FAN_SPEED_MAP = {
    1: 33,
    2: 66,
    3: 100,
}

# Mode mappings (value -> name)
MODE_MAP = {
    0: "Unknown",
    1: "Manual",
    2: "Auto",
    3: "Sleep",
}

# Temperature unit mappings
TEMP_UNIT_MAP = {
    0: "°C",
    1: "°F",
}
