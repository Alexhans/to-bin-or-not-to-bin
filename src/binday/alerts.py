"""Tell me, at most once per collection. The agent never imports this."""

import datetime as dt
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


def alerts_file() -> Path:
    """Where alerts go: $BINDAY_ALERTS, or alerts.log next to Airflow's own files."""
    default = Path(os.environ.get("AIRFLOW_HOME", ".")) / "alerts.log"
    return Path(os.environ.get("BINDAY_ALERTS", default))


def already_sent(collection: dt.date, path: Path | None = None) -> bool:
    """Whether I've already been told about this collection."""
    path = path or alerts_file()
    return path.exists() and any(line.startswith(collection.isoformat()) for line in path.read_text().splitlines())


def send(collection: dt.date, message: str, path: Path | None = None) -> None:
    """Append the alert to the alerts file, and log it."""
    path = path or alerts_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as out:
        out.write(f"{collection.isoformat()} {message}\n")
    logger.info(f"Sent: {message}")
