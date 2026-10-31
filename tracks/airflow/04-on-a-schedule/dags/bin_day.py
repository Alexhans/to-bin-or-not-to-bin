"""Every evening, ask the bin-day skill whether the bins go out tonight, and alert me once per collection.

The agent answers and decides. Its only tools reach the council's website, so it has no
way to send anything: the `tell_me` task sends the alert, and only once per collection.
"""

import os
from pathlib import Path

import httpx
import pendulum
from airflow.providers.common.ai.operators.agent import AgentOperator
from airflow.providers.common.ai.toolsets.skills import AgentSkillsToolset
from airflow.sdk import dag, task
from pydantic import Field
from pydantic_ai.toolsets import FunctionToolset

from binday import alerts
from binday.facts import BinDayFacts, describe

# Your skills from step 1, or BINDAY_SKILLS if you copied them elsewhere.
SKILLS = Path(os.environ.get("BINDAY_SKILLS") or Path(__file__).resolve().parents[4] / "steps/01-do-it-for-me/sandbox/.claude/skills")


class BinDayAlert(BinDayFacts):
    """The facts, plus the agent's decision about tonight."""

    put_out_tonight: bool = Field(description="True only if the next collection is tomorrow")
    message: str = Field(description="One short line telling me which bins to put out tonight, or why not")


def get(path: str) -> str:
    """GET a page or file from the council's website, for example "/w/2026-08-26/" or "/w/2026-08-26/static/app.js"."""
    return httpx.get(os.environ.get("BIN_SERVICE_URL", "http://localhost:8111") + path, timeout=30).text


def post(path: str, fields: dict[str, str]) -> str:
    """POST form fields to the council's website, for example "/w/2026-08-26/api/addresses" with {"postcode": "FX1 2ZZ"}."""
    return httpx.post(os.environ.get("BIN_SERVICE_URL", "http://localhost:8111") + path, data=fields, timeout=30).text


def act(answer: BinDayAlert, alerts_file: Path) -> str:
    """Send the alert if the agent said so and it hasn't been sent; say what happened."""
    if not answer.put_out_tonight:
        return f"Alert: none tonight. {answer.message}"
    if alerts.already_sent(answer.next_collection_date, alerts_file):
        return "Alert: already sent for this collection, not sending again."
    alerts.send(answer.next_collection_date, answer.message, alerts_file)
    return f"Alert: sent. {answer.message}"


@dag(schedule="0 19 * * *", start_date=pendulum.datetime(2026, 8, 1, tz="Europe/London"), catchup=False)
def bin_day():
    ask_the_agent = AgentOperator(
        task_id="ask_the_agent",
        llm_conn_id="binday_llm",
        # {{ ds }} is the day of the run, so a run for 26 August reads the website as it was that day.
        prompt=(
            "Use the bin-day skill, with the council's website at the path /w/{{ ds }}/ instead of "
            "http://localhost:8111, for every URL, including the API endpoints. You can't run curl: "
            "use the get and post tools, which take paths. "
            "Today is {{ logical_date.strftime('%A %-d %B %Y') }}. Do I need to put the bins out tonight?"
        ),
        output_type=BinDayAlert,
        serialize_output=True,
        toolsets=[
            # Step 1's skill is instructions only; excluding run_skill_script keeps it that way.
            AgentSkillsToolset(sources=[str(SKILLS)], exclude_tools={"run_skill_script"}),
            FunctionToolset([get, post], id="council"),
        ],
        usage_limits={"request_limit": 15},
    )

    @task
    def tell_me(answer: dict) -> str:
        alert = BinDayAlert.model_validate(answer)
        print(describe(alert))
        status = act(alert, alerts.alerts_file())
        print(status)
        return status

    tell_me(ask_the_agent.output)


bin_day_dag = bin_day()
