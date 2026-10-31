"""Ask the bin-day skill which bins go out next, whenever you trigger this Dag.

It does in Airflow what you did in step 1: `ask_the_agent` runs your skill, and `tell_me`
prints the answer. It has no schedule, so it only runs when you trigger it.
"""

import os
from pathlib import Path

import httpx
from airflow.providers.common.ai.operators.agent import AgentOperator
from airflow.providers.common.ai.toolsets.skills import AgentSkillsToolset
from airflow.sdk import dag, task
from pydantic_ai.toolsets import FunctionToolset

from binday.facts import BinDayFacts, describe

# Your skills from step 1, or BINDAY_SKILLS if you copied them elsewhere.
SKILLS = Path(os.environ.get("BINDAY_SKILLS") or Path(__file__).resolve().parents[4] / "steps/01-do-it-for-me/sandbox/.claude/skills")


def get(path: str) -> str:
    """GET a page or file from the council's website, for example "/w/2026-08-22/" or "/w/2026-08-22/static/app.js"."""
    return httpx.get(os.environ.get("BIN_SERVICE_URL", "http://localhost:8111") + path, timeout=30).text


def post(path: str, fields: dict[str, str]) -> str:
    """POST form fields to the council's website, for example "/w/2026-08-22/api/addresses" with {"postcode": "FX1 2ZZ"}."""
    return httpx.post(os.environ.get("BIN_SERVICE_URL", "http://localhost:8111") + path, data=fields, timeout=30).text


@dag(schedule=None)
def bin_day():
    ask_the_agent = AgentOperator(
        task_id="ask_the_agent",
        llm_conn_id="binday_llm",
        # {{ ds }} is the run's logical date, so a run for 22 August reads the website as it was that day.
        prompt=(
            "Use the bin-day skill, with the council's website at the path /w/{{ ds }}/ instead of "
            "http://localhost:8111, for every URL, including the API endpoints. You can't run curl: "
            "use the get and post tools, which take paths. Which bins do I put out next, and when?"
        ),
        output_type=BinDayFacts,
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
        message = describe(BinDayFacts.model_validate(answer))
        print(message)
        return message

    tell_me(ask_the_agent.output)


bin_day_dag = bin_day()
