"""GPIO access layer for the feeder hardware."""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Optional

try:
    import RPi.GPIO as GPIO
except Exception:  # pragma: no cover - not available on dev machines
    GPIO = None  # type: ignore


_LOGGER = logging.getLogger(__name__)


@dataclass
class HardwareState:
    limit_switch_active: Optional[bool] = None
    last_activation: Optional[float] = None


class FeederHardware:
    """Interface for either relay or servo operated release mechanisms."""

    def __init__(self, config) -> None:
        self.config = config
        self.state = HardwareState()
        self._setup_gpio()

    def _setup_gpio(self) -> None:
        if GPIO is None:
            _LOGGER.warning("RPi.GPIO not available; running in simulation mode")
            return
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.config.release_pin, GPIO.OUT)
        GPIO.setup(self.config.limit_switch_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        if self.config.gpio_mode == "servo":
            self._pwm = GPIO.PWM(self.config.release_pin, 50)
            self._pwm.start(0)
        else:
            GPIO.output(
                self.config.release_pin,
                GPIO.HIGH if not self.config.relay_active_high else GPIO.LOW,
            )
            self._pwm = None

    def cleanup(self) -> None:
        if GPIO is None:
            return
        if getattr(self, "_pwm", None):
            self._pwm.stop()
        GPIO.cleanup()

    def read_limit_switch(self) -> Optional[bool]:
        if GPIO is None:
            return None
        value = GPIO.input(self.config.limit_switch_pin) == GPIO.HIGH
        if self.config.limit_switch_invert:
            value = not value
        self.state.limit_switch_active = value
        return value

    def trigger_release(self, pulse_seconds: Optional[float] = None) -> None:
        pulse = pulse_seconds or self.config.default_release_seconds
        now = time.monotonic()
        if (
            self.state.last_activation
            and now - self.state.last_activation < self.config.release_cooldown_seconds
        ):
            _LOGGER.warning("Release ignored due to cooldown")
            return
        self.state.last_activation = now

        if GPIO is None:
            _LOGGER.info("Simulated release for %.2f seconds", pulse)
            time.sleep(min(pulse, 0.1))
            return

        if self.config.gpio_mode == "servo":
            self._activate_servo(pulse)
        else:
            self._activate_relay(pulse)

    def _activate_relay(self, pulse: float) -> None:
        active_level = GPIO.HIGH if self.config.relay_active_high else GPIO.LOW
        GPIO.output(self.config.release_pin, active_level)
        time.sleep(pulse)
        GPIO.output(self.config.release_pin, GPIO.LOW if active_level == GPIO.HIGH else GPIO.HIGH)

    def _activate_servo(self, pulse: float) -> None:
        if self._pwm is None:
            _LOGGER.error("Servo PWM not initialised")
            return
        # Sweep servo to release position
        release_us = self.config.servo_max_us
        rest_us = self.config.servo_min_us
        self._set_servo_us(release_us)
        time.sleep(pulse)
        self._set_servo_us(rest_us)

    def _set_servo_us(self, micros: int) -> None:
        if self._pwm is None:
            return
        duty = (micros / 20000.0) * 100.0
        self._pwm.ChangeDutyCycle(duty)
        time.sleep(0.02)
        self._pwm.ChangeDutyCycle(0)


__all__ = ["FeederHardware", "HardwareState"]
