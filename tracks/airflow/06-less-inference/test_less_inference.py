"""The checks for this chapter: the same as before, plus fast checks for `decide`."""

import datetime as dt
import os
from pathlib import Path

import pytest

from binday import dagtest
from binday.chapter import load
from binday.council.server import serve
from binday.facts import KNOWN_DAYS, BinDayFacts

bin_day = load(Path(__file__).parent / "dags/bin_day.py")

DUE_27_AUG = BinDayFacts(next_collection_date=dt.date(2026, 8, 27), containers_due={"BLUE RECYCLING WHEELIE BIN", "FOOD BOX"})
DUE_2_JAN = BinDayFacts(next_collection_date=dt.date(2027, 1, 2), containers_due={"BLUE RECYCLING WHEELIE BIN", "FOOD BOX"})


# Fast checks: no model.

def test_decides_tonight_the_day_before():
    assert bin_day.decide(DUE_27_AUG, dt.date(2026, 8, 26)) == "Put out the blue recycling wheelie bin and food box tonight, for Thursday 27 August."


def test_decides_nothing_two_days_before():
    assert bin_day.decide(DUE_27_AUG, dt.date(2026, 8, 25)) is None


def test_decides_nothing_on_the_collection_day_itself():
    assert bin_day.decide(DUE_27_AUG, dt.date(2026, 8, 27)) is None


def test_decides_nothing_after_the_collection():
    assert bin_day.decide(DUE_27_AUG, dt.date(2026, 8, 28)) is None


def test_decides_tonight_across_the_new_year():
    assert bin_day.decide(DUE_2_JAN, dt.date(2027, 1, 1)) is not None


def test_never_tells_me_twice(tmp_path):
    bin_day.act(DUE_27_AUG, dt.date(2026, 8, 26), tmp_path / "alerts.log")
    assert bin_day.act(DUE_27_AUG, dt.date(2026, 8, 26), tmp_path / "alerts.log").startswith("Alert: already sent")
    assert len((tmp_path / "alerts.log").read_text().splitlines()) == 1


# Agent checks: run the Dag, which asks the skill.

@pytest.fixture(scope="module")
def council(airflow_db):
    if not os.environ.get("BINDAY_MODEL"):
        pytest.skip("BINDAY_MODEL isn't set in this terminal; see docs/models.md")
    if not (bin_day.SKILLS / "bin-day/SKILL.md").exists():
        pytest.skip("Make the bin-day skill in step 1 first")
    with serve() as base:
        yield base


@pytest.fixture
def alerts_file(council, tmp_path, monkeypatch):
    """Point the Dag at the test's council and a fresh alerts file."""
    monkeypatch.setenv("BIN_SERVICE_URL", council)
    monkeypatch.setenv("BINDAY_ALERTS", str(tmp_path / "alerts.log"))
    return tmp_path / "alerts.log"


@pytest.mark.agent
@pytest.mark.parametrize("name", KNOWN_DAYS)
def test_the_step_2_checks_still_pass(alerts_file, name):
    today, expected = KNOWN_DAYS[name]
    got = dagtest.run(bin_day.bin_day_dag, today)["ask_the_agent"]
    assert BinDayFacts.model_validate(got) == expected


@pytest.mark.agent
def test_tells_me_the_night_before(alerts_file):
    status = dagtest.run(bin_day.bin_day_dag, dt.date(2026, 8, 26))["tell_me"]
    assert status.startswith("Alert: sent."), status
    assert alerts_file.read_text().startswith("2026-08-27 ")


@pytest.mark.agent
def test_stays_quiet_two_nights_before(alerts_file):
    status = dagtest.run(bin_day.bin_day_dag, dt.date(2026, 8, 25))["tell_me"]
    assert status.startswith("Alert: none tonight"), status
    assert not alerts_file.exists()
