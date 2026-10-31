"""Every evening, ask the council's website directly, and alert me once per collection.

No agent and no model: `council.next_collection` calls the two addresses the skill named,
and `decide` works out whether the collection is tomorrow.
"""

import datetime as dt
import os
from pathlib import Path

import pendulum
from airflow.sdk import dag, task

from binday import alerts
from binday.facts import BinDayFacts, describe
from council import next_collection


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


@dag(schedule="0 19 * * *", start_date=pendulum.datetime(2026, 8, 1, tz="Europe/London"), catchup=False)
def bin_day():
    @task
    def ask_the_council(today: str) -> dict:
        # The website as it was on the day of the run.
        council = os.environ.get("BIN_SERVICE_URL", "http://localhost:8111")
        return next_collection(f"{council}/w/{today}/").model_dump()

    @task
    def tell_me(answer: dict, today: str) -> str:
        facts = BinDayFacts.model_validate(answer)
        print(describe(facts))
        status = act(facts, dt.date.fromisoformat(today), alerts.alerts_file())
        print(status)
        return status

    tell_me(ask_the_council("{{ ds }}"), "{{ ds }}")


bin_day_dag = bin_day()
