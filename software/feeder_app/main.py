"""Entry point for the feeder application."""
from __future__ import annotations

import logging
import signal
import sys

from waitress import serve

from . import Database, FeederHardware, ScheduleRunner, create_app, load_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def main() -> int:
    config = load_config()
    db = Database(config.database_path)
    hardware = FeederHardware(config)
    runner = ScheduleRunner(db=db, hardware=hardware, timezone=config.timezone)
    runner.start()

    app = create_app(config, db, hardware)

    def handle_signal(signum, frame):  # pragma: no cover - signal path
        logging.info("Stopping due to signal %s", signum)
        runner.stop()
        hardware.cleanup()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    logging.info("Starting web server on http://0.0.0.0:8080")
    serve(app, host="0.0.0.0", port=8080)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
