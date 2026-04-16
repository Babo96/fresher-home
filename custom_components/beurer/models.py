"""Data models for Beurer FreshHome."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AwsFunction(Enum):
    """AWS function types for device commands."""

    power = "power"
    fan = "fan"
    mode = "mode"
    timerMin = "timerMin"
    sleep = "sleep"
    uv = "uv"
    tempUnitSwitcher = "tempUnitSwitcher"
    filterReset = "filterReset"
    read = "read"
    buzzer = "buzzer"


class DeviceType(Enum):
    """Beurer device types."""

    LR500 = "LR500"
    LR400 = "LR400"
    LR405 = "LR405"


@dataclass
class AwsCmdModel:
    """Model for AWS command messages."""

    function: str
    value: Any
    version: str = "2018-08-31"
    valueType: str = "int"
    type: str = "cmd"
    source: str = "Android"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "function": self.function,
            "value": self.value,
            "version": self.version,
            "valueType": self.valueType,
            "type": self.type,
            "source": self.source,
        }


@dataclass
class BeurerDevice:
    """Model for a Beurer device."""

    id: str
    name: str
    model: str
    user: str

    @property
    def device_type(self) -> DeviceType:
        """Get device type enum from model string."""
        return DeviceType(self.model)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "model": self.model,
            "user": self.user,
        }


@dataclass
class LoginResponse:
    """Model for login API response."""

    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_in": self.expires_in,
            "token_type": self.token_type,
        }


@dataclass
class DeviceState:
    """Model for device state containing all sensor and control fields."""

    pm: int | None = None
    airquality: int | None = None
    humidity: int | None = None
    temperature: int | None = None
    filterLeft: int | None = None
    filterReplace: int | None = None
    power: int | None = None
    fan: int | None = None
    mode: int | None = None
    timerMin: int | None = None
    sleep: int | None = None
    uv: int | None = None
    buzzer: int | None = None
    tempUnitSwitcher: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "pm": self.pm,
            "airquality": self.airquality,
            "humidity": self.humidity,
            "temperature": self.temperature,
            "filterLeft": self.filterLeft,
            "filterReplace": self.filterReplace,
            "power": self.power,
            "fan": self.fan,
            "mode": self.mode,
            "timerMin": self.timerMin,
            "sleep": self.sleep,
            "uv": self.uv,
            "buzzer": self.buzzer,
            "tempUnitSwitcher": self.tempUnitSwitcher,
        }
