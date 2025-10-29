"""Background scheduler for releasing the feeder."""
from __future__ import annotations

import logging
import threading
import time
from datetime import datetime

import pytz

from .database import Database
from .hardware import FeederHardware

_LOGGER = logging.getLogger(__name__)


class ScheduleRunner(threading.Thread):
    """Thread that periodically checks the database for due schedules."""

    def __init__(self, *, db: Database, hardware: FeederHardware, timezone: str) -> None:
        super().__init__(daemon=True)
        self.db = db
        self.hardware = hardware
        self.tz = pytz.timezone(timezone)
        self._stop_event = threading.Event()

    def stop(self) -> None:
        self._stop_event.set()

    def run(self) -> None:  # pragma: no cover - background thread
        _LOGGER.info("Schedule runner started")
        while not self._stop_event.is_set():
            now = datetime.now(self.tz)
            weekday = now.strftime("%a").lower()
            due = self.db.get_due_schedules(now, weekday)
            for schedule in due:
                limit_ok = self.hardware.read_limit_switch()
                if limit_ok is not None and not limit_ok:
                    _LOGGER.warning(
                        "Skip schedule %s because limit switch reports not ready", schedule.label
                    )
                    continue
                _LOGGER.info(
                    "Activating schedule %s at %s", schedule.label, now.isoformat()
                )
                self.hardware.trigger_release(schedule.pulse_seconds)
                self.db.update_last_run(schedule.id, now.date())
                self.db.record_manual_run(schedule.id)
            time.sleep(30)
        _LOGGER.info("Schedule runner stopped")


__all__ = ["ScheduleRunner"]
