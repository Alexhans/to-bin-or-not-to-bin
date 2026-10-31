"""Check the bin-day skill from step 1 against a day whose answer you know."""

import datetime as dt
import json
import subprocess
from pathlib import Path

import pytest
from binday.council.server import serve
from binday.facts import BinDayFacts

SANDBOX = Path(__file__).parents[1] / "01-do-it-for-me" / "sandbox"


def ask_agent(site: str) -> BinDayFacts:
    """Ask the step 1 skill about one council site, and return its answer as facts."""
    done = subprocess.run(
        [
            "claude", "-p",
            f"Use the bin-day skill, with the council site at {site} instead of http://localhost:8111 "
            f"(for every URL, including the API endpoints). Do I need to put the bins out?",
            "--allowedTools", "Bash(curl:*)", "Skill",
            "--json-schema", json.dumps(BinDayFacts.model_json_schema()),
            "--output-format", "json",
        ],
        cwd=SANDBOX, capture_output=True, text=True, check=True,
    )
    return BinDayFacts.model_validate(json.loads(done.stdout)["structured_output"])


@pytest.fixture(scope="module")
def council():
    """Run a council for the test, on a free port, so yours can keep running."""
    if not (SANDBOX / ".claude/skills/bin-day/SKILL.md").exists():
        pytest.skip("Make the bin-day skill in step 1 first")
    with serve() as base:
        yield base


def test_ordinary_week(council):
    facts = ask_agent(f"{council}/w/2026-08-22/")
    assert facts == BinDayFacts(
        next_collection_date=dt.date(2026, 8, 27),
        containers_due={"BLUE RECYCLING WHEELIE BIN", "FOOD BOX"},
    )
