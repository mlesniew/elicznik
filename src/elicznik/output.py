"""Output writers. Every format uses the same fields as :meth:`Reading.to_dict`."""

from __future__ import annotations

import csv
import json
import os
import tempfile
from collections.abc import Callable, Sequence
from datetime import date
from pathlib import Path
from typing import TextIO

from .const import TIME_ZONE
from .models import FIELDS, Reading


def write_jsonl(readings: Sequence[Reading], out: TextIO, **_) -> None:
    for r in readings:
        out.write(json.dumps(r.to_dict(), ensure_ascii=False) + "\n")


def write_json(readings: Sequence[Reading], out: TextIO, *, start: date, end: date, site: str | None = None) -> None:
    doc = {
        "site": site,
        "from": start.isoformat(),
        "to": end.isoformat(),
        "unit": "kWh",
        "timezone": TIME_ZONE,
        "readings": [r.to_dict() for r in readings],
    }
    json.dump(doc, out, ensure_ascii=False, indent=2)
    out.write("\n")


def write_csv(readings: Sequence[Reading], out: TextIO, **_) -> None:
    writer = csv.DictWriter(out, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(r.to_dict() for r in readings)


def write_table(readings: Sequence[Reading], out: TextIO, **_) -> None:
    headers = ("local time", "consumption", "production", "net cons.", "net prod.")
    rows = [
        (
            r.local_start.strftime("%Y-%m-%d %H:%M %Z"),
            *("" if v is None else f"{v:.3f}" for v in (r.consumption, r.production, r.net_consumption, r.net_production)),
        )
        for r in readings
    ]
    widths = [max(len(h), *(len(row[i]) for row in rows)) for i, h in enumerate(headers)]
    lines = [headers, tuple("-" * w for w in widths), *rows]
    for row in lines:
        out.write("  ".join(c.ljust(w) if i == 0 else c.rjust(w) for i, (c, w) in enumerate(zip(row, widths))) + "\n")


WRITERS: dict[str, Callable[..., None]] = {
    "jsonl": write_jsonl,
    "json": write_json,
    "csv": write_csv,
    "table": write_table,
}


def write_atomic(path: str | os.PathLike, render: Callable[[TextIO], None]) -> None:
    """Write to a temp file in the target directory, then rename it into place."""
    path = Path(path)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            render(f)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise
