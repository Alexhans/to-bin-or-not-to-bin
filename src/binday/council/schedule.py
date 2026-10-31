"""Dilly Dally Borough's collection rules: who gets collected, on which day, with which bin.

Everything here is made up. The rules are the same shape as a typical London borough's:
rubbish and recycling on alternate weeks, food every week, and collections pushed back
a day around bank holidays.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

RUBBISH = "BLACK RUBBISH WHEELIE BIN"
RECYCLING = "BLUE RECYCLING WHEELIE BIN"
FOOD = "FOOD BOX"


@dataclass(frozen=True)
class Round:
    """A collection round: one weekday, and a date on which it collected recycling."""

    weekday: str
    recycling_anchor: dt.date


THURSDAY = Round("Thursday", dt.date(2026, 8, 27))
TUESDAY = Round("Tuesday", dt.date(2026, 9, 1))


@dataclass(frozen=True)
class Address:
    """One property in the borough."""

    uprn: str
    line: str
    postcode: str
    round: Round


ADDRESSES = [
    Address("OW-0001", "1 Wibble Way, Ollie Woley", "FX1 2ZZ", THURSDAY),
    Address("OW-0002", "2 Wibble Way, Ollie Woley", "FX1 2ZZ", THURSDAY),
    Address("OW-0003", "3 Wibble Way, Ollie Woley", "FX1 2ZZ", THURSDAY),
    Address("OW-0011", "Flat A, 12 Wobble Road, Ollie Woley", "FX1 2ZZ", TUESDAY),
    Address("OW-0012", "Flat B, 12 Wobble Road, Ollie Woley", "FX1 2ZZ", TUESDAY),
    Address("OW-0014", "14 Wobble Road, Ollie Woley", "FX1 2ZZ", TUESDAY),
]

# Bank holidays move a collection to a later day. Listed by hand, the way a council
# publishes its festive calendar, so a reader can check any answer against this table.
SHIFTED = {
    dt.date(2026, 12, 29): dt.date(2026, 12, 30),  # Mon 28 Dec is the Boxing Day substitute
    dt.date(2026, 12, 31): dt.date(2027, 1, 2),  # Fri 1 Jan is New Year's Day
}


def normalise_postcode(postcode: str) -> str:
    """Upper-case and single-space a postcode, so "fx12zz" matches "FX1 2ZZ"."""
    compact = "".join(postcode.split()).upper()
    return f"{compact[:-3]} {compact[-3:]}" if len(compact) > 3 else compact


def addresses_for(postcode: str) -> list[Address]:
    """Return the properties at a postcode, or an empty list."""
    wanted = normalise_postcode(postcode)
    return [a for a in ADDRESSES if a.postcode == wanted]


def find(uprn: str) -> Address | None:
    """Return the property with this UPRN, if there is one."""
    return next((a for a in ADDRESSES if a.uprn == uprn), None)


def _scheduled(round_: Round, on_or_after: dt.date) -> list[dt.date]:
    """Return the round's next few scheduled weekdays, before holiday shifts."""
    weekday = round_.recycling_anchor.weekday()
    first = on_or_after - dt.timedelta(days=7)
    first += dt.timedelta(days=(weekday - first.weekday()) % 7)
    return [first + dt.timedelta(weeks=n) for n in range(5)]


def next_collections(address: Address, today: dt.date) -> dict[str, dt.date]:
    """Return, for each container, the next date it is collected on or after today."""
    nxt: dict[str, dt.date] = {}
    for scheduled in _scheduled(address.round, today):
        actual = SHIFTED.get(scheduled, scheduled)
        if actual < today:
            continue
        weeks = (scheduled - address.round.recycling_anchor).days // 7
        bin_ = RECYCLING if weeks % 2 == 0 else RUBBISH
        nxt.setdefault(bin_, actual)
        nxt.setdefault(FOOD, actual)
    return nxt
