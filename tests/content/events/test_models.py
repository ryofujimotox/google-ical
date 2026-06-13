from __future__ import annotations

from datetime import date, datetime

from google_ical.content.events.models import JST, CalendarEvent, parse_event


def test_parse_event_all_day() -> None:
    event = parse_event({"title": "記念日", "start": "2026-06-20"}, source="events.json")

    assert event.kind == "all_day"
    assert event.start == date(2026, 6, 20)
    assert event.normalized_end() == date(2026, 6, 21)


def test_parse_event_timed_normalizes_to_jst() -> None:
    event = parse_event(
        {"title": "会議", "start": "2026-06-20T01:00:00Z", "end": "2026-06-20T02:00:00Z"},
        source="events.json",
    )

    assert event.kind == "timed"
    assert event.start == datetime(2026, 6, 20, 10, 0, tzinfo=JST)
    assert event.end == datetime(2026, 6, 20, 11, 0, tzinfo=JST)


def test_stable_id_uses_uid() -> None:
    event_a = CalendarEvent(source="a.json", title="A", start=date(2026, 6, 20), uid="same")
    event_b = CalendarEvent(source="a.json", title="B", start=date(2026, 6, 21), uid="same")

    assert event_a.stable_id("ns") == event_b.stable_id("ns")
