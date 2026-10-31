"""The checks from step 2, now run against the Dag. They ask the model, so they're marked `agent`."""

import os
from pathlib import Path

import pytest

from binday import dagtest
from binday.chapter import load
from binday.council.server import serve
from binday.facts import KNOWN_DAYS, BinDayFacts

bin_day = load(Path(__file__).parent / "dags/bin_day.py")


@pytest.fixture(scope="module")
def council(airflow_db):
    if not os.environ.get("BINDAY_MODEL"):
        pytest.skip("BINDAY_MODEL isn't set in this terminal; see docs/models.md")
    if not (bin_day.SKILLS / "bin-day/SKILL.md").exists():
        pytest.skip("Make the bin-day skill in step 1 first")
    with serve() as base:
        yield base


@pytest.mark.agent
@pytest.mark.parametrize("name", KNOWN_DAYS)
def test_the_step_2_checks_still_pass(council, monkeypatch, name):
    monkeypatch.setenv("BIN_SERVICE_URL", council)
    today, expected = KNOWN_DAYS[name]
    got = dagtest.run(bin_day.bin_day_dag, today)["ask_the_agent"]
    assert BinDayFacts.model_validate(got) == expected
