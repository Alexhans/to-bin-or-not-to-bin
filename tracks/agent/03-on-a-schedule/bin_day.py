"""Ask the bin-day skill whether the bins go out tonight, and alert me once per collection.

    uv run python tracks/agent/03-on-a-schedule/bin_day.py
    uv run python tracks/agent/03-on-a-schedule/bin_day.py --today 2026-08-26

Cron runs it every evening. The agent answers and decides; this code only sends the alert,
and only once per collection.
"""

import argparse
import datetime as dt
from pathlib import Path

from pydantic import Field

from binday import alerts, claude
from binday.facts import BinDayFacts, describe

ALERTS = Path(__file__).resolve().parents[1] / "alerts.log"


class BinDayAlert(BinDayFacts):
    """The facts, plus the agent's decision about tonight."""

    put_out_tonight: bool = Field(description="True only if the next collection is tomorrow")
    message: str = Field(description="One short line telling me which bins to put out tonight, or why not")


def ask_agent(site: str, today: dt.date) -> tuple[BinDayAlert, claude.Usage]:
    """Ask the skill about `today`, and let it decide whether the bins go out tonight."""
    question = f"Today is {today:%A %-d %B %Y}. Do I need to put the bins out tonight?"
    return claude.ask(question, site, BinDayAlert)


def act(answer: BinDayAlert, alerts_file: Path) -> str:
    """Send the alert if the agent said so and it hasn't been sent; say what happened."""
    if not answer.put_out_tonight:
        return f"Alert: none tonight. {answer.message}"
    if alerts.already_sent(answer.next_collection_date, alerts_file):
        return "Alert: already sent for this collection, not sending again."
    alerts.send(answer.next_collection_date, answer.message, alerts_file)
    return f"Alert: sent. {answer.message}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--today", type=dt.date.fromisoformat, default=dt.date.today())
    parser.add_argument("--council", default="http://localhost:8111")
    parser.add_argument("--alerts", type=Path, default=ALERTS)
    args = parser.parse_args()

    answer, usage = ask_agent(f"{args.council}/w/{args.today.isoformat()}/", args.today)
    print(usage.line())
    print(describe(answer))
    print(act(answer, args.alerts))


if __name__ == "__main__":
    main()
