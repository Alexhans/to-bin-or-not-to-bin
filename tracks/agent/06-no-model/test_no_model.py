"""The checks for this chapter. None of them needs a model now, so they all run in a second."""

import datetime as dt
import subprocess
import sys
from pathlib import Path

import pytest

from binday.council.server import serve
from binday.facts import KNOWN_DAYS, BinDayFacts

from binday.chapter import load

bin_day = load(Path(__file__).parent / "bin_day.py")

COMMAND = Path(__file__).parent / "bin_day.py"
DUE_27_AUG = BinDayFacts(next_collection_date=dt.date(2026, 8, 27), containers_due={"BLUE RECYCLING WHEELIE BIN", "FOOD BOX"})
DUE_2_JAN = BinDayFacts(next_collection_date=dt.date(2027, 1, 2), containers_due={"BLUE RECYCLING WHEELIE BIN", "FOOD BOX"})


# Checks of the decision.

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


# Checks against the council's website.

@pytest.fixture(scope="module")
def council():
    with serve() as base:
        yield base


def run_for(day: dt.date, council: str, alerts_file: Path) -> str:
    done = subprocess.run([sys.executable, str(COMMAND), "--today", day.isoformat(), "--council", council,
                           "--alerts", str(alerts_file)], capture_output=True, text=True, timeout=900)
    assert done.returncode == 0, done.stderr[-800:]
    print(done.stdout)
    return done.stdout


@pytest.mark.parametrize("name", KNOWN_DAYS)
def test_the_step_2_checks_still_pass(council, name):
    today, expected = KNOWN_DAYS[name]
    assert bin_day.next_collection(f"{council}/w/{today.isoformat()}/") == expected


def test_answers_for_a_day_it_has_not_seen(council):
    assert bin_day.next_collection(f"{council}/w/2026-10-14/") == BinDayFacts(
        next_collection_date=dt.date(2026, 10, 15), containers_due={"BLACK RUBBISH WHEELIE BIN", "FOOD BOX"})


def test_tells_me_the_night_before(council, tmp_path):
    out = run_for(dt.date(2026, 8, 26), council, tmp_path / "alerts.log")
    assert "Alert: sent." in out
    assert (tmp_path / "alerts.log").read_text().startswith("2026-08-27 ")


def test_stays_quiet_two_nights_before(council, tmp_path):
    out = run_for(dt.date(2026, 8, 25), council, tmp_path / "alerts.log")
    assert "Alert: none tonight" in out
    assert not (tmp_path / "alerts.log").exists()
