"""The checks for this chapter.

The fast ones test what the code does with an answer, with no model. The ones marked
`agent` ask the skill about days whose answers I know, so they're slower and cost a little.
"""

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


def answer(put_out_tonight: bool) -> bin_day.BinDayAlert:
    return bin_day.BinDayAlert(next_collection_date=dt.date(2026, 8, 27),
                               containers_due={"BLUE RECYCLING WHEELIE BIN", "FOOD BOX"},
                               put_out_tonight=put_out_tonight, message="Put the recycling and food out tonight.")


# Fast checks: no model.

def test_sends_when_the_agent_says_tonight(tmp_path):
    assert bin_day.act(answer(True), tmp_path / "alerts.log").startswith("Alert: sent.")
    assert (tmp_path / "alerts.log").read_text().startswith("2026-08-27 ")


def test_sends_nothing_when_the_agent_says_not_tonight(tmp_path):
    assert bin_day.act(answer(False), tmp_path / "alerts.log").startswith("Alert: none tonight.")
    assert not (tmp_path / "alerts.log").exists()


def test_never_tells_me_twice(tmp_path):
    bin_day.act(answer(True), tmp_path / "alerts.log")
    assert bin_day.act(answer(True), tmp_path / "alerts.log").startswith("Alert: already sent")
    assert len((tmp_path / "alerts.log").read_text().splitlines()) == 1


# Agent checks: ask the skill.

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


@pytest.mark.agent
@pytest.mark.parametrize("name", KNOWN_DAYS)
def test_the_step_2_checks_still_pass(council, name):
    today, expected = KNOWN_DAYS[name]
    got, usage = bin_day.ask_agent(f"{council}/w/{today.isoformat()}/", today)
    print(usage.line())
    assert BinDayFacts.model_validate(got.model_dump(include={"next_collection_date", "containers_due"})) == expected


@pytest.mark.agent
def test_tells_me_the_night_before(council, tmp_path):
    out = run_for(dt.date(2026, 8, 26), council, tmp_path / "alerts.log")
    assert "Alert: sent." in out
    assert (tmp_path / "alerts.log").read_text().startswith("2026-08-27 ")


@pytest.mark.agent
def test_stays_quiet_two_nights_before(council, tmp_path):
    out = run_for(dt.date(2026, 8, 25), council, tmp_path / "alerts.log")
    assert "Alert: none tonight" in out
    assert not (tmp_path / "alerts.log").exists()
