"""`CalendarEvent` と Google Calendar API リソースの相互変換。"""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

from google_ical.content.events.models import CalendarEvent, EventWindow, JST, parse_event, sort_events

PRIVATE_SOURCE_ID = "google_ical_source_id"
PRIVATE_NAMESPACE = "google_ical_namespace"


def load_events_from_json(path: Path) -> list[CalendarEvent]:
    """固定予定JSONを読む。トップレベルは配列または `{events: [...]}`。"""

    with path.open(encoding="utf-8") as file:
        payload = json.load(file)
    items = payload.get("events", payload) if isinstance(payload, dict) else payload
    if not isinstance(items, list):
        raise ValueError(f"{path} はイベント配列、または events 配列を持つJSONにしてください")
    return [parse_event(item, source=str(path)) for item in items]


def load_events(paths: tuple[Path, ...]) -> list[CalendarEvent]:
    events: list[CalendarEvent] = []
    for path in paths:
        events.extend(load_events_from_json(path))
    return sort_events(events)


def to_google_event(event: CalendarEvent, *, namespace: str) -> dict[str, Any]:
    """Google Calendar API の `events.insert/update` 用リソースを作る。"""

    body: dict[str, Any] = {
        "summary": event.title,
        "description": event.description,
        "location": event.location,
        "extendedProperties": {
            "private": {
                PRIVATE_NAMESPACE: namespace,
                PRIVATE_SOURCE_ID: event.stable_id(namespace),
            }
        },
    }
    if event.color_id:
        body["colorId"] = event.color_id

    end = event.normalized_end()
    if event.kind == "all_day":
        body["start"] = {"date": _date_text(event.start)}
        body["end"] = {"date": _date_text(end)}
    else:
        body["start"] = {"dateTime": _datetime_text(event.start), "timeZone": "Asia/Tokyo"}
        body["end"] = {"dateTime": _datetime_text(end), "timeZone": "Asia/Tokyo"}

    if event.reminders:
        body["reminders"] = {
            "useDefault": False,
            "overrides": [{"method": "popup", "minutes": minutes} for minutes in event.reminders],
        }
    return body


def filter_window(events: list[CalendarEvent], window: EventWindow) -> list[CalendarEvent]:
    """同期対象期間に重なる予定だけに絞る。"""

    return sort_events([event for event in events if event.overlaps(window.start, window.end)])


def _date_text(value: date | datetime) -> str:
    return value.date().isoformat() if isinstance(value, datetime) else value.isoformat()


def _datetime_text(value: date | datetime) -> str:
    if not isinstance(value, datetime):
        value = datetime.combine(value, datetime.min.time(), tzinfo=JST)
    if value.tzinfo is None:
        value = value.replace(tzinfo=JST)
    return value.astimezone(JST).isoformat()
