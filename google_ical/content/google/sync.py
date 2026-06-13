"""Google カレンダーへの予定同期。

extendedProperties.private に google_ical_id / google_ical_source を保存し、
本リポ管理イベントのみ作成・更新・削除する。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from google_ical.config import AppConfig
from google_ical.constants import (
    DEFAULT_EVENT_SOURCE,
    GOMI_EVENT_SOURCE,
    GOOGLE_ICAL_ID_KEY,
    GOOGLE_ICAL_SOURCE_KEY,
    JST_DATETIME_FORMAT,
    JST_TIMEZONE,
)
from google_ical.content.events.models import MergedEvent
from google_ical.content.google.auth import load_calendar_credentials
from google_ical.content.google.calendar import build_calendar_service, delete_event, list_managed_events, upsert_event
from google_ical.exceptions import CalendarSyncError, GoogleAuthError


def sync_events_to_google_calendar(
    config: AppConfig,
    events: tuple[MergedEvent, ...],
) -> None:
    """予定JSONの合成結果に合わせ、管理イベントを作成・更新・削除する。"""
    calendar_id = config.google_calendar_id
    try:
        service = build_calendar_service(load_calendar_credentials())
        sources = _managed_sources(events)
        existing = list_managed_events(service, calendar_id=calendar_id, sources=sources)
        desired = _build_desired_events(events)
        _apply_sync(service, calendar_id, existing, desired)
    except (CalendarSyncError, GoogleAuthError):
        raise
    except Exception as exc:
        raise CalendarSyncError(
            f"Google カレンダー同期に失敗しました calendar_id={calendar_id}",
        ) from exc


def _managed_sources(events: tuple[MergedEvent, ...]) -> tuple[str, ...]:
    """削除漏れを防ぐため、既知 source と今回 JSON の source を和集合にする。"""
    sources = {DEFAULT_EVENT_SOURCE, GOMI_EVENT_SOURCE}
    sources.update(event.source for event in events)
    return tuple(sorted(sources))


def _build_desired_events(events: tuple[MergedEvent, ...]) -> dict[str, dict[str, Any]]:
    desired: dict[str, dict[str, Any]] = {}
    for event in events:
        if event.event_id in desired:
            raise CalendarSyncError(f"予定 JSON の内部 ID が重複しています: {event.event_id}")
        desired[event.event_id] = _event_to_google_body(event)
    return desired


def _apply_sync(
    service: object,
    calendar_id: str,
    existing: dict[str, dict[str, Any]],
    desired: dict[str, dict[str, Any]],
) -> None:
    for event_id, body in desired.items():
        current = existing.get(event_id)
        if current is None or _needs_update(current, body):
            upsert_event(service, calendar_id=calendar_id, body=body, existing=current)

    for event_id, current in existing.items():
        if event_id not in desired:
            delete_event(service, calendar_id=calendar_id, event_id=current["id"])


def _event_to_google_body(event: MergedEvent) -> dict[str, Any]:
    body: dict[str, Any] = {
        "summary": event.summary,
        "start": _google_time(event.start, all_day=event.all_day),
        "end": _google_time(event.end, all_day=event.all_day),
        "extendedProperties": {
            "private": {
                GOOGLE_ICAL_ID_KEY: event.event_id,
                GOOGLE_ICAL_SOURCE_KEY: event.source,
            },
        },
    }
    body["description"] = event.description or ""
    return body


def _google_time(value: str, *, all_day: bool) -> dict[str, str]:
    parsed = datetime.strptime(value, JST_DATETIME_FORMAT)
    if all_day:
        return {"date": parsed.date().isoformat()}
    return {"dateTime": value, "timeZone": JST_TIMEZONE}


def _needs_update(current: dict[str, Any], desired: dict[str, Any]) -> bool:
    if current.get("summary") != desired.get("summary"):
        return True
    if _text_value(current.get("description")) != _text_value(desired.get("description")):
        return True
    if current.get("start") != desired.get("start"):
        return True
    if current.get("end") != desired.get("end"):
        return True

    current_private = current.get("extendedProperties", {}).get("private", {})
    desired_private = desired.get("extendedProperties", {}).get("private", {})
    return any(current_private.get(key) != value for key, value in desired_private.items())


def _text_value(value: object) -> str:
    return value if isinstance(value, str) else ""
