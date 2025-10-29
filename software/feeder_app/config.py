"""Application configuration loading for the feeder controller."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


@dataclass
class AppConfig:
    """Configuration values for the feeder application."""

    database_path: Path
    gpio_mode: str
    release_pin: int
    servo_min_us: int
    servo_max_us: int
    relay_active_high: bool
    limit_switch_pin: int
    limit_switch_invert: bool
    default_release_seconds: float
    release_cooldown_seconds: float
    timezone: str


DEFAULTS = {
    "database_path": "~/feeder/feeder.db",
    "gpio_mode": "relay",  # or "servo"
    "release_pin": "18",
    "servo_min_us": "500",
    "servo_max_us": "2400",
    "relay_active_high": "true",
    "limit_switch_pin": "23",
    "limit_switch_invert": "false",
    "default_release_seconds": "2.5",
    "release_cooldown_seconds": "10",
    "timezone": "Europe/Helsinki",
}


def _get_env_bool(name: str, default: str) -> bool:
    value = os.getenv(name, default).strip().lower()
    return value in {"1", "true", "yes", "on"}


def load_config() -> AppConfig:
    """Create an :class:`AppConfig` from environment variables."""

    def get(name: str) -> str:
        env_name = f"FEEDER_{name.upper()}"
        return os.getenv(env_name, DEFAULTS[name])

    database_path = Path(os.path.expanduser(get("database_path"))).resolve()
    return AppConfig(
        database_path=database_path,
        gpio_mode=get("gpio_mode").lower(),
        release_pin=int(get("release_pin")),
        servo_min_us=int(get("servo_min_us")),
        servo_max_us=int(get("servo_max_us")),
        relay_active_high=_get_env_bool("FEEDER_RELAY_ACTIVE_HIGH", DEFAULTS["relay_active_high"]),
        limit_switch_pin=int(get("limit_switch_pin")),
        limit_switch_invert=_get_env_bool("FEEDER_LIMIT_SWITCH_INVERT", DEFAULTS["limit_switch_invert"]),
        default_release_seconds=float(get("default_release_seconds")),
        release_cooldown_seconds=float(get("release_cooldown_seconds")),
        timezone=get("timezone"),
    )


__all__ = ["AppConfig", "load_config"]
