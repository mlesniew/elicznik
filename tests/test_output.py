import io
import json
from datetime import date, datetime, timezone

from elicznik.output import WRITERS, write_atomic

from elicznik import Reading

READINGS = [
    Reading(datetime(2026, 11, 18, 23, tzinfo=timezone.utc), 0.171, 0.0, 0.171, 0.0),
    Reading(datetime(2026, 11, 19, 0, tzinfo=timezone.utc), 0.161, None, None, None),
]
KW = dict(start=date(2026, 11, 19), end=date(2026, 11, 19), site=None)


def render(fmt):
    buf = io.StringIO()
    WRITERS[fmt](READINGS, buf, **KW)
    return buf.getvalue()


def test_jsonl_schema():
    lines = render("jsonl").splitlines()
    assert json.loads(lines[0]) == {
        "start": "2026-11-18T23:00:00Z",
        "end": "2026-11-19T00:00:00Z",
        "local_start": "2026-11-19T00:00:00+01:00",
        "consumption": 0.171,
        "production": 0.0,
        "net_consumption": 0.171,
        "net_production": 0.0,
    }
    assert json.loads(lines[1])["production"] is None


def test_json_document():
    doc = json.loads(render("json"))
    assert doc["unit"] == "kWh" and doc["from"] == "2026-11-19" and len(doc["readings"]) == 2


def test_csv_has_header():
    lines = render("csv").splitlines()
    assert lines[0] == "start,end,local_start,consumption,production,net_consumption,net_production"
    assert lines[2].endswith("0.161,,,")


def test_table():
    out = render("table")
    assert "2026-11-19 00:00 CET" in out and "0.171" in out


def test_write_atomic(tmp_path):
    target = tmp_path / "out.jsonl"
    write_atomic(target, lambda f: WRITERS["jsonl"](READINGS, f))
    assert len(target.read_text().splitlines()) == 2
    assert list(tmp_path.iterdir()) == [target]
