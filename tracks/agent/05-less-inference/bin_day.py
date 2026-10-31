"""Ask the bin-day skill only for the facts, and decide here whether the bins go out tonight.

    uv run python tracks/agent/05-less-inference/bin_day.py
    uv run python tracks/agent/05-less-inference/bin_day.py --today 2026-08-26

Whether the next collection is tomorrow is date arithmetic, so `decide` works it out in
plain Python, the same way every time.
"""

import argparse
import datetime as dt
from pathlib import Path

from binday import alerts, claude
from binday.facts import BinDayFacts, describe

ALERTS = Path(__file__).resolve().parents[1] / "alerts.log"


def ask_agent(site: str, today: dt.date) -> tuple[BinDayFacts, claude.Usage]:
    """Ask the skill only for the next collection date and bins, as of `today`."""
    question = f"Today is {today:%A %-d %B %Y}. Which bins go out next, and when?"
    return claude.ask(question, site, BinDayFacts)


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
    args = parser.parse_args()

    facts, usage = ask_agent(f"{args.council}/w/{args.today.isoformat()}/", args.today)
    print(usage.line())
    print(describe(facts))
    print(act(facts, args.today, args.alerts))


if __name__ == "__main__":
    main()
