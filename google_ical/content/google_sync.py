"""Google カレンダーへの予定同期。

extendedProperties.private に google_ical_id / google_ical_source を保存し、
本リポ管理イベントのみ作成・更新・削除する。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from google_ical.config import AppConfig
from google_ical.constants import JST_DATETIME_FORMAT, JST_TIMEZONE
from google_ical.content.events.models import MergedEvent
from google_ical.content.google_auth import load_calendar_credentials
from google_ical.exceptions import CalendarSyncError, GoogleAuthError

_MANAGED_ID_KEY = "google_ical_id"
_MANAGED_SOURCE_KEY = "google_ical_source"


def sync_events_to_google_calendar(
    config: AppConfig,
    events: tuple[MergedEvent, ...],
) -> None:
    """予定JSONの合成結果に合わせ、管理イベントを作成・更新・削除する。"""
    calendar_id = config.google_calendar_id
    try:
        credentials = load_calendar_credentials()
        service = _build_calendar_service(credentials)
        existing = _list_managed_events(service, calendar_id)
        desired = _build_desired_events(events)
        _apply_sync(service, calendar_id, existing, desired)
    except (CalendarSyncError, GoogleAuthError):
        raise
    except Exception as exc:
        raise CalendarSyncError(
            f"Google カレンダー同期に失敗しました calendar_id={calendar_id}",
        ) from exc


def _build_calendar_service(credentials: object) -> object:
    from googleapiclient.discovery import build

    try:
        return build("calendar", "v3", credentials=credentials, cache_discovery=False)
    except Exception as exc:
        raise CalendarSyncError("Google Calendar API クライアント作成に失敗しました") from exc


def _list_managed_events(service: object, calendar_id: str) -> dict[str, dict[str, Any]]:
    managed: dict[str, dict[str, Any]] = {}
    page_token: str | None = None

    while True:
        try:
            result = (
                service.events()
                .list(
                    calendarId=calendar_id,
                    singleEvents=True,
                    showDeleted=False,
                    maxResults=2500,
                    pageToken=page_token,
                )
                .execute()
            )
        except Exception as exc:
            raise CalendarSyncError(
                f"Google カレンダーの既存イベント取得に失敗しました calendar_id={calendar_id}",
            ) from exc

        for item in result.get("items", []):
            private = item.get("extendedProperties", {}).get("private", {})
            managed_id = private.get(_MANAGED_ID_KEY)
            if managed_id and private.get(_MANAGED_SOURCE_KEY):
                managed[managed_id] = item

        page_token = result.get("nextPageToken")
        if not page_token:
            return managed


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
        if current is None:
            _insert_event(service, calendar_id, body)
        elif _needs_update(current, body):
            _update_event(service, calendar_id, current["id"], body)

    for event_id, current in existing.items():
        if event_id not in desired:
            _delete_event(service, calendar_id, current["id"])


def _insert_event(service: object, calendar_id: str, body: dict[str, Any]) -> None:
    try:
        service.events().insert(calendarId=calendar_id, body=body).execute()
    except Exception as exc:
        raise CalendarSyncError(
            f"Google カレンダーイベント作成に失敗しました summary={body['summary']}",
        ) from exc


def _update_event(service: object, calendar_id: str, google_event_id: str, body: dict[str, Any]) -> None:
    try:
        service.events().patch(calendarId=calendar_id, eventId=google_event_id, body=body).execute()
    except Exception as exc:
        raise CalendarSyncError(
            f"Google カレンダーイベント更新に失敗しました event_id={google_event_id}",
        ) from exc


def _delete_event(service: object, calendar_id: str, google_event_id: str) -> None:
    try:
        service.events().delete(calendarId=calendar_id, eventId=google_event_id).execute()
    except Exception as exc:
        raise CalendarSyncError(
            f"Google カレンダーイベント削除に失敗しました event_id={google_event_id}",
        ) from exc


def _event_to_google_body(event: MergedEvent) -> dict[str, Any]:
    body: dict[str, Any] = {
        "summary": event.summary,
        "start": _google_time(event.start, all_day=event.all_day),
        "end": _google_time(event.end, all_day=event.all_day),
        "extendedProperties": {
            "private": {
                _MANAGED_ID_KEY: event.event_id,
                _MANAGED_SOURCE_KEY: event.source,
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
