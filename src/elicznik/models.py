"""Data model for meter readings."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from .const import TIME_ZONE

LOCAL_TZ = ZoneInfo(TIME_ZONE)
FIELDS = ("start", "end", "local_start", "consumption", "production", "net_consumption", "net_production")


def _iso_utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True, slots=True)
class Reading:
    """Energy in kWh for one hour. ``None`` means Tauron has not published the value."""

    start: datetime  # timezone-aware, UTC, start of the hour
    consumption: float | None = None
    production: float | None = None
    net_consumption: float | None = None
    net_production: float | None = None

    @property
    def end(self) -> datetime:
        return self.start + timedelta(hours=1)

    @property
    def local_start(self) -> datetime:
        return self.start.astimezone(LOCAL_TZ)

    def to_dict(self) -> dict:
        return {
            "start": _iso_utc(self.start),
            "end": _iso_utc(self.end),
            "local_start": self.local_start.isoformat(),
            "consumption": self.consumption,
            "production": self.production,
            "net_consumption": self.net_consumption,
            "net_production": self.net_production,
        }
