"""What an agent has to tell us about bin day, and the days whose answers we know.

Both tracks check their agent against the same cases, so "it still works" means the
same thing whichever box the agent runs in.
"""

import datetime as dt
from typing import Annotated

from pydantic import BaseModel, Field, WithJsonSchema, field_validator

# A set, so the order of containers doesn't matter. Its JSON schema is a plain array of
# strings, because some providers (Bedrock among them) reject `uniqueItems`.
Containers = Annotated[set[str], WithJsonSchema({"type": "array", "items": {"type": "string"}})]


class BinDayFacts(BaseModel):
    """The answer to "which bins go out next, and when?", in a shape a test can compare."""

    next_collection_date: dt.date = Field(description="The next collection date, as the council site lists it")
    containers_due: Containers = Field(description="Every container collected on that date, named as the site names it")

    @field_validator("containers_due", mode="after")
    @classmethod
    def _ignore_capitals(cls, names: set[str]) -> set[str]:
        """Which bins go out is what matters, not how the agent wrote their names."""
        return {" ".join(n.split()).upper() for n in names}


RECYCLING = "BLUE RECYCLING WHEELIE BIN"
RUBBISH = "BLACK RUBBISH WHEELIE BIN"
FOOD = "FOOD BOX"

KNOWN_DAYS = {
    "ordinary week": (
        dt.date(2026, 8, 22),
        BinDayFacts(next_collection_date=dt.date(2026, 8, 27), containers_due={RECYCLING, FOOD}),
    ),
    "new year's week": (
        dt.date(2026, 12, 27),
        BinDayFacts(next_collection_date=dt.date(2027, 1, 2), containers_due={RECYCLING, FOOD}),
    ),
}
"""For 2 Wibble Way: the day you ask, and what the council says on that day."""


def describe(facts: BinDayFacts) -> str:
    """One line with the next collection, for a person to read."""
    bins = " and ".join(sorted(b.lower() for b in facts.containers_due))
    return f"Next collection: {facts.next_collection_date:%A %-d %B %Y}, {bins}."
