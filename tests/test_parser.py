from datetime import datetime, timezone

import pytest

from elicznik import Reading, ResponseError, parse_csv
from elicznik.parser import is_csv

HEADER = "Data; Strefa; Wartość ;Rodzaj;Status;"


def utc(*args):
    return datetime(*args, tzinfo=timezone.utc)


def row(ts, value, kind="pobór [kWh]"):
    return f"{ts};T1;{value};{kind}; licznik; "


def test_partial_day_real_sample():
    text = "\n".join(
        [
            HEADER,
            "2026-11-19 1:00;T3;0,171;pobór [kWh]; licznik; ",
            "2026-11-19 2:00;T3;0,161;pobór [kWh]; licznik; ",
            "2026-11-19 6:00;T3;0,143;pobór [kWh]; licznik; ",
            "",
        ]
    )
    assert is_csv(text)
    assert parse_csv(text) == [
        Reading(utc(2026, 11, 18, 23), consumption=0.171),
        Reading(utc(2026, 11, 19, 0), consumption=0.161),
        Reading(utc(2026, 11, 19, 4), consumption=0.143),
    ]


def test_spring_forward_day_has_23_hours():
    rows = [row(f"2026-03-29 {h}:00", "1,0") for h in range(1, 24)]
    starts = [r.start for r in parse_csv("\n".join([HEADER, *rows, row("2026-03-30 1:00", "2,0")]))]
    assert starts[0] == utc(2026, 3, 28, 23)
    assert starts[22] == utc(2026, 3, 29, 21)
    assert starts[23] == utc(2026, 3, 29, 22)
    assert len(set(starts)) == 24


def test_autumn_back_day_has_25_hours():
    rows = [row(f"2026-10-25 {h}:00", "1,0") for h in range(1, 26)]
    starts = [r.start for r in parse_csv("\n".join([HEADER, *rows, row("2026-10-26 1:00", "2,0")]))]
    assert starts[0] == utc(2026, 10, 24, 22)
    assert starts[24] == utc(2026, 10, 25, 22)
    assert starts[25] == utc(2026, 10, 25, 23)
    assert len(set(starts)) == 26


def test_repeated_label_becomes_next_hour():
    text = "\n".join([HEADER, row("2026-10-25 2:00", "1"), row("2026-10-25 3:00", "1"), row("2026-10-25 3:00", "1")])
    assert [r.start for r in parse_csv(text)] == [utc(2026, 10, 24, 23), utc(2026, 10, 25, 0), utc(2026, 10, 25, 1)]


def test_energy_types_are_merged_per_hour():
    text = "\n".join(
        [
            HEADER,
            row("2022-07-20 6:00", "0,02", "pobór [kWh]"),
            row("2022-07-20 7:00", "0", "pobór [kWh]"),
            row("2022-07-20 6:00", "0,226", "oddanie [kWh]"),
            row("2022-07-20 7:00", "1,058", "oddanie [kWh]"),
            row("2022-07-20 6:00", "0", "pobrana po zbilansowaniu [kWh]"),
            row("2022-07-20 6:00", "0,206", "oddana po zbilansowaniu [kWh]"),
            row("2022-07-20 6:00", "9", "something new"),
        ]
    )
    assert parse_csv(text) == [
        Reading(utc(2022, 7, 20, 3), 0.02, 0.226, 0.0, 0.206),
        Reading(utc(2022, 7, 20, 4), 0.0, 1.058, None, None),
    ]


def test_html_page_raises():
    assert not is_csv("<!DOCTYPE html><html>login</html>")
    with pytest.raises(ResponseError):
        parse_csv("<!DOCTYPE html><html>login</html>")


def test_bom_and_empty_export():
    assert parse_csv("﻿" + HEADER + "\n") == []
