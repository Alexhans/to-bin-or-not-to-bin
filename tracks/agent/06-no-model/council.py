"""Ask the council's website for the next collection, with no model involved.

This is what the bin-day skill describes, written as code: look up the address for the
postcode, then ask for that address's collections, and take the earliest date.
"""

import datetime as dt

import httpx

from binday.facts import BinDayFacts

POSTCODE = "FX1 2ZZ"
ADDRESS = "2 Wibble Way"


def next_collection(site: str, postcode: str = POSTCODE, address: str = ADDRESS) -> BinDayFacts:
    """Return the next collection date and every container due on it."""
    site = site.rstrip("/")
    addresses = httpx.post(f"{site}/api/addresses", data={"postcode": postcode}, timeout=30).json()["addresses"]
    matches = [a["uprn"] for a in addresses if a["address"].startswith(address)]
    if len(matches) != 1:
        raise ValueError(f"Expected one address starting {address!r} at {postcode}, found {len(matches)}")
    rows = httpx.post(f"{site}/api/collections", data={"uprn": matches[0]}, timeout=30).json()["collections"]
    if not rows:
        raise ValueError(f"The council listed no collections for {address}")
    first = min(dt.date.fromisoformat(r["next_collection"]) for r in rows)
    due = {r["container"] for r in rows if dt.date.fromisoformat(r["next_collection"]) == first}
    return BinDayFacts(next_collection_date=first, containers_due=due)
