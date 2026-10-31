"""The council site answers the way a person reading it by hand would.

Expected values are written out by hand from the rules in `schedule.py`, never computed
by calling it, so a bug in the schedule shows up here as a failure.
"""

import json
import urllib.request
from urllib.parse import urlencode

import pytest

from binday.council.server import serve


@pytest.fixture(scope="module")
def site():
    with serve() as base:
        yield base


def post(url: str, **fields: str) -> dict:
    request = urllib.request.Request(url, data=urlencode(fields).encode(), method="POST")
    with urllib.request.urlopen(request) as response:
        return json.load(response)


def collections(site: str, world: str, uprn: str) -> dict[str, str]:
    body = post(f"{site}/w/{world}/api/collections", uprn=uprn)
    return {row["container"]: row["next_collection"] for row in body["collections"]}


def test_postcode_lists_six_addresses_in_any_spacing_or_case(site):
    body = post(f"{site}/api/addresses", postcode="fx12zz")
    assert [a["address"] for a in body["addresses"]] == [
        "1 Wibble Way, Ollie Woley",
        "2 Wibble Way, Ollie Woley",
        "3 Wibble Way, Ollie Woley",
        "Flat A, 12 Wobble Road, Ollie Woley",
        "Flat B, 12 Wobble Road, Ollie Woley",
        "14 Wobble Road, Ollie Woley",
    ]


def test_unknown_postcode_has_no_addresses(site):
    assert post(f"{site}/api/addresses", postcode="AB1 2CD") == {"addresses": []}


def test_thursday_round_in_august(site):
    assert collections(site, "2026-08-22", "OW-0002") == {
        "BLUE RECYCLING WHEELIE BIN": "2026-08-27",
        "FOOD BOX": "2026-08-27",
        "BLACK RUBBISH WHEELIE BIN": "2026-09-03",
    }


def test_tuesday_round_in_august(site):
    assert collections(site, "2026-08-22", "OW-0012") == {
        "BLACK RUBBISH WHEELIE BIN": "2026-08-25",
        "FOOD BOX": "2026-08-25",
        "BLUE RECYCLING WHEELIE BIN": "2026-09-01",
    }


def test_collection_day_itself_counts_as_next(site):
    assert collections(site, "2026-08-27", "OW-0002")["FOOD BOX"] == "2026-08-27"


def test_boxing_day_substitute_moves_tuesday_to_wednesday(site):
    assert collections(site, "2026-12-27", "OW-0012") == {
        "BLACK RUBBISH WHEELIE BIN": "2026-12-30",
        "FOOD BOX": "2026-12-30",
        "BLUE RECYCLING WHEELIE BIN": "2027-01-05",
    }


def test_new_years_day_moves_thursday_to_saturday(site):
    assert collections(site, "2027-01-01", "OW-0002") == {
        "BLUE RECYCLING WHEELIE BIN": "2027-01-02",
        "FOOD BOX": "2027-01-02",
        "BLACK RUBBISH WHEELIE BIN": "2027-01-07",
    }


def test_page_shows_the_worlds_date_and_has_no_addresses_in_its_html(site):
    with urllib.request.urlopen(f"{site}/w/2026-08-22/") as response:
        html = response.read().decode()
    assert "Saturday 22 August 2026" in html
    assert "Wibble" not in html
