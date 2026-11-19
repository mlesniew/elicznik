"""Parser for the eLicznik hourly CSV export (no network access)."""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone

from .const import ENERGY_TYPES
from .errors import ResponseError
from .models import LOCAL_TZ, Reading

_LOGGER = logging.getLogger(__name__)


def is_csv(text: str) -> bool:
    return text.lstrip("﻿ \r\n").startswith("Data")


def _field_for(kind: str) -> str | None:
    kind = kind.lower()
    for prefix, field in ENERGY_TYPES.items():
        if kind.startswith(prefix):
            return field
    return None


def parse_csv(text: str) -> list[Reading]:
    """Parse the export into readings sorted by hour.

    Rows look like ``2026-11-19 1:00;T3;0,171;pobór [kWh]; licznik;``. The time is
    the *end* of the hour, numbered 1..24 (23/25 on DST days), so the hour start is
    UTC midnight of that local day plus (hour - 1) hours. A repeated label is
    treated as the next hour. Types are interleaved, so this is tracked per type.
    """
    if not is_csv(text):
        raise ResponseError("eLicznik did not return CSV data (session expired or site changed?)")

    values: dict[datetime, dict[str, float]] = defaultdict(dict)
    previous: dict[str, datetime] = {}
    for line in text.splitlines()[1:]:
        cols = [c.strip() for c in line.split(";")]
        if len(cols) < 4 or not cols[0] or not cols[2]:
            continue
        field = _field_for(cols[3])
        if field is None:
            _LOGGER.debug("Skipping unknown energy type %r", cols[3])
            continue
        try:
            day_str, _, time_str = cols[0].partition(" ")
            day = date.fromisoformat(day_str)
            hour = int(time_str.split(":")[0])
            value = float(cols[2].replace(",", "."))
        except ValueError as err:
            raise ResponseError(f"Malformed CSV row: {line!r}") from err

        midnight = datetime.combine(day, time.min, tzinfo=LOCAL_TZ).astimezone(timezone.utc)
        start = midnight + timedelta(hours=hour - 1)
        last = previous.get(field)
        if last is not None and start <= last:  # rows of one type are chronological
            start = last + timedelta(hours=1)
        values[start][field] = value
        previous[field] = start

    return [Reading(start, **fields) for start, fields in sorted(values.items())]
