from __future__ import annotations

import json
from datetime import date, datetime

from google_ical.content.events.models import JST, CalendarEvent, EventWindow
from google_ical.content.events.writer import filter_window, load_events_from_json, to_google_event


def test_load_events_from_json_accepts_events_object(tmp_path) -> None:
    path = tmp_path / "events.json"
    path.write_text(json.dumps({"events": [{"title": "終日", "start": "2026-06-20"}]}), encoding="utf-8")

    events = load_events_from_json(path)

    assert len(events) == 1
    assert events[0].title == "終日"


def test_to_google_event_all_day() -> None:
    event = CalendarEvent(source="test", title="終日", start=date(2026, 6, 20), uid="all-day")

    body = to_google_event(event, namespace="ns")

    assert body["summary"] == "終日"
    assert body["start"] == {"date": "2026-06-20"}
    assert body["end"] == {"date": "2026-06-21"}
    assert body["extendedProperties"]["private"]["google_ical_namespace"] == "ns"


def test_to_google_event_timed_with_reminder() -> None:
    event = CalendarEvent(
        source="test",
        title="会議",
        start=datetime(2026, 6, 20, 10, 0, tzinfo=JST),
        end=datetime(2026, 6, 20, 11, 0, tzinfo=JST),
        reminders=(30,),
    )

    body = to_google_event(event, namespace="ns")

    assert body["start"]["dateTime"] == "2026-06-20T10:00:00+09:00"
    assert body["reminders"]["overrides"] == [{"method": "popup", "minutes": 30}]


def test_filter_window_keeps_overlapping_events() -> None:
    events = [
        CalendarEvent(source="test", title="in", start=date(2026, 6, 20)),
        CalendarEvent(source="test", title="out", start=date(2026, 6, 25)),
    ]
    window = EventWindow.from_days(date(2026, 6, 20), 2)

    assert [event.title for event in filter_window(events, window)] == ["in"]
