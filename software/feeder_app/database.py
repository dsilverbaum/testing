"""SQLite database helper for the feeder controller."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable, Iterator, List, Optional


@dataclass
class Schedule:
    id: int
    label: str
    hour: int
    minute: int
    days: str
    active: bool
    pulse_seconds: float
    last_run: Optional[str]

    @property
    def time_display(self) -> str:
        return f"{self.hour:02d}:{self.minute:02d}"


class Database:
    """Small wrapper around SQLite for storing schedules."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS schedules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    label TEXT NOT NULL,
                    hour INTEGER NOT NULL,
                    minute INTEGER NOT NULL,
                    days TEXT NOT NULL,
                    active INTEGER NOT NULL DEFAULT 1,
                    pulse_seconds REAL NOT NULL DEFAULT 2.5,
                    last_run TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS manual_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    schedule_id INTEGER,
                    run_at TEXT NOT NULL,
                    FOREIGN KEY(schedule_id) REFERENCES schedules(id)
                )
                """
            )
            conn.commit()

    @contextmanager
    def _cursor(self) -> Iterator[sqlite3.Cursor]:
        with self._connect() as conn:
            cur = conn.cursor()
            try:
                yield cur
                conn.commit()
            finally:
                cur.close()

    def get_schedules(self) -> List[Schedule]:
        with self._cursor() as cur:
            rows = cur.execute(
                "SELECT id, label, hour, minute, days, active, pulse_seconds, last_run FROM schedules ORDER BY hour, minute"
            ).fetchall()
        return [Schedule(*row) for row in rows]

    def add_schedule(
        self,
        *,
        label: str,
        hour: int,
        minute: int,
        days: Iterable[str],
        pulse_seconds: float,
    ) -> None:
        day_list = ",".join(sorted(days))
        with self._cursor() as cur:
            cur.execute(
                """
                INSERT INTO schedules (label, hour, minute, days, pulse_seconds)
                VALUES (?, ?, ?, ?, ?)
                """,
                (label, hour, minute, day_list, pulse_seconds),
            )

    def delete_schedule(self, schedule_id: int) -> None:
        with self._cursor() as cur:
            cur.execute("DELETE FROM schedules WHERE id = ?", (schedule_id,))

    def toggle_schedule(self, schedule_id: int, active: bool) -> None:
        with self._cursor() as cur:
            cur.execute("UPDATE schedules SET active = ? WHERE id = ?", (1 if active else 0, schedule_id))

    def update_last_run(self, schedule_id: int, run_date: date) -> None:
        with self._cursor() as cur:
            cur.execute("UPDATE schedules SET last_run = ? WHERE id = ?", (run_date.isoformat(), schedule_id))

    def record_manual_run(self, schedule_id: Optional[int]) -> None:
        with self._cursor() as cur:
            cur.execute("INSERT INTO manual_runs (schedule_id, run_at) VALUES (?, datetime('now'))", (schedule_id,))

    def get_due_schedules(self, now, weekday_name: str) -> List[Schedule]:
        """Return active schedules whose time has passed and were not run today."""
        with self._cursor() as cur:
            rows = cur.execute(
                """
                SELECT id, label, hour, minute, days, active, pulse_seconds, last_run
                FROM schedules
                WHERE active = 1
                ORDER BY hour, minute
                """
            ).fetchall()
        results: List[Schedule] = []
        for row in rows:
            schedule = Schedule(*row)
            if schedule.last_run == now.date().isoformat():
                continue
            days = {d.strip().lower() for d in schedule.days.split(",") if d.strip()}
            if days and weekday_name not in days and "daily" not in days:
                continue
            if schedule.hour < now.hour or (schedule.hour == now.hour and schedule.minute <= now.minute):
                results.append(schedule)
        return results


__all__ = ["Database", "Schedule"]
