"""Ask the council's website directly, with no model, and alert me the night before.

    uv run python tracks/agent/06-no-model/bin_day.py
    uv run python tracks/agent/06-no-model/bin_day.py --today 2026-08-26
    uv run python tracks/agent/06-no-model/bin_day.py --no-alert     # just answer

`council.next_collection` calls the two addresses the skill named. Nothing here asks a model.
"""

import argparse
import datetime as dt
import time
from pathlib import Path

from binday import alerts
from binday.facts import BinDayFacts, describe

from council import next_collection

ALERTS = Path(__file__).resolve().parents[1] / "alerts.log"


def decide(facts: BinDayFacts, today: dt.date) -> str | None:
    """Return tonight's message, or None if the next collection isn't tomorrow."""
    if facts.next_collection_date != today + dt.timedelta(days=1):
        return None
    bins = " and ".join(sorted(b.lower() for b in facts.containers_due))
    return f"Put out the {bins} tonight, for {facts.next_collection_date:%A %-d %B}."


def act(facts: BinDayFacts, today: dt.date, alerts_file: Path) -> str:
    """Send tonight's alert if there is one and it hasn't been sent; say what happened."""
    message = decide(facts, today)
    if message is None:
        return "Alert: none tonight, the collection isn't tomorrow."
    if alerts.already_sent(facts.next_collection_date, alerts_file):
        return "Alert: already sent for this collection, not sending again."
    alerts.send(facts.next_collection_date, message, alerts_file)
    return f"Alert: sent. {message}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--today", type=dt.date.fromisoformat, default=dt.date.today())
    parser.add_argument("--council", default="http://localhost:8111")
    parser.add_argument("--alerts", type=Path, default=ALERTS)
    parser.add_argument("--no-alert", action="store_true", help="answer the question, don't alert")
    args = parser.parse_args()

    started = time.monotonic()
    facts = next_collection(f"{args.council}/w/{args.today.isoformat()}/")
    print(f"[bin_day] model=none tokens_read=0 tokens_written=0 seconds={time.monotonic() - started:.2f}")
    print(describe(facts))
    if not args.no_alert:
        print(act(facts, args.today, args.alerts))


if __name__ == "__main__":
    main()
