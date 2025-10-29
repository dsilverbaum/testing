"""Flask web UI for schedule management."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import List

from flask import Flask, flash, redirect, render_template, request, url_for

from .config import AppConfig
from .database import Database, Schedule
from .hardware import FeederHardware

_LOGGER = logging.getLogger(__name__)

DAYS = [
    ("mon", "Maanantai"),
    ("tue", "Tiistai"),
    ("wed", "Keskiviikko"),
    ("thu", "Torstai"),
    ("fri", "Perjantai"),
    ("sat", "Lauantai"),
    ("sun", "Sunnuntai"),
]


def _parse_days(form) -> List[str]:
    selected = [value for value in form.getlist("days") if value]
    if not selected:
        selected = ["daily"]
    return selected


def create_app(config: AppConfig, db: Database, hardware: FeederHardware) -> Flask:
    app = Flask(__name__)
    app.secret_key = "change-me"  # Replace during installation

    @app.context_processor
    def inject_globals():
        return {
            "days": DAYS,
            "config": config,
        }

    @app.route("/")
    def index():
        schedules = db.get_schedules()
        now = datetime.now()
        return render_template("index.html", schedules=schedules, now=now)

    @app.post("/schedule")
    def add_schedule():
        try:
            label = request.form["label"].strip() or "Ajastus"
            hour, minute = request.form["time"].split(":")
            pulse_seconds = float(request.form.get("pulse", config.default_release_seconds))
            days = _parse_days(request.form)
            db.add_schedule(
                label=label,
                hour=int(hour),
                minute=int(minute),
                days=days,
                pulse_seconds=pulse_seconds,
            )
            flash("Ajastus lisätty.", "success")
        except Exception as exc:  # pragma: no cover - validation path
            _LOGGER.exception("Failed to add schedule")
            flash(f"Virhe ajastusta lisätessä: {exc}", "error")
        return redirect(url_for("index"))

    @app.post("/schedule/<int:schedule_id>/toggle")
    def toggle_schedule(schedule_id: int):
        active = request.form.get("active") == "1"
        db.toggle_schedule(schedule_id, active)
        flash("Ajastuksen tila päivitetty.", "success")
        return redirect(url_for("index"))

    @app.post("/schedule/<int:schedule_id>/delete")
    def delete_schedule(schedule_id: int):
        db.delete_schedule(schedule_id)
        flash("Ajastus poistettu.", "success")
        return redirect(url_for("index"))

    @app.post("/manual-release")
    def manual_release():
        try:
            duration = float(request.form.get("pulse", config.default_release_seconds))
            hardware.trigger_release(duration)
            db.record_manual_run(None)
            flash("Levy vapautettu manuaalisesti.", "success")
        except Exception as exc:  # pragma: no cover - runtime issues
            _LOGGER.exception("Manual release failed")
            flash(f"Manuaalinen vapautus epäonnistui: {exc}", "error")
        return redirect(url_for("index"))

    return app


__all__ = ["create_app"]
