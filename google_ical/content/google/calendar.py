"""Google Calendar API への薄いアダプタ。"""

from __future__ import annotations

from typing import Any, Protocol

from google_ical.constants import GOOGLE_ICAL_ID_KEY, GOOGLE_ICAL_SOURCE_KEY
from google_ical.exceptions import CalendarSyncError


class CalendarService(Protocol):
    def events(self) -> Any: ...


def build_calendar_service(credentials: object) -> CalendarService:
    """OAuth 資格情報から Calendar API クライアントを作る。"""
    try:
        from googleapiclient.discovery import build
    except ModuleNotFoundError as exc:
        raise CalendarSyncError(
            "Google Calendar API クライアント作成には google-api-python-client が必要です",
        ) from exc

    try:
        return build("calendar", "v3", credentials=credentials, cache_discovery=False)
    except Exception as exc:
        raise CalendarSyncError("Google Calendar API クライアント作成に失敗しました") from exc


def list_managed_events(
    service: CalendarService,
    *,
    calendar_id: str,
) -> dict[str, dict[str, Any]]:
    """google_ical_id を持つ本リポ管理の既存予定をすべて取得する。"""
    managed: dict[str, dict[str, Any]] = {}
    try:
        request = service.events().list(
            calendarId=calendar_id,
            showDeleted=False,
        )
        while request is not None:
            response = request.execute()
            for item in response.get("items", []):
                private = item.get("extendedProperties", {}).get("private", {})
                managed_id = private.get(GOOGLE_ICAL_ID_KEY)
                if managed_id and private.get(GOOGLE_ICAL_SOURCE_KEY):
                    managed[managed_id] = item
            request = service.events().list_next(request, response)
    except Exception as exc:
        raise CalendarSyncError(
            f"Google カレンダーの既存イベント取得に失敗しました calendar_id={calendar_id}",
        ) from exc
    return managed


def upsert_event(
    service: CalendarService,
    *,
    calendar_id: str,
    body: dict[str, Any],
    existing: dict[str, Any] | None,
) -> str:
    """既存があれば patch、なければ insert し、Google 側 ID を返す。"""
    try:
        if existing:
            response = (
                service.events()
                .patch(calendarId=calendar_id, eventId=existing["id"], body=body)
                .execute()
            )
        else:
            response = service.events().insert(calendarId=calendar_id, body=body).execute()
    except Exception as exc:
        if existing:
            raise CalendarSyncError(
                f"Google カレンダーイベント更新に失敗しました event_id={existing['id']}",
            ) from exc
        raise CalendarSyncError(
            f"Google カレンダーイベント作成に失敗しました summary={body['summary']}",
        ) from exc
    return str(response["id"])


def delete_event(service: CalendarService, *, calendar_id: str, event_id: str) -> None:
    """入力から消えた管理予定を削除する。"""
    try:
        service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
    except Exception as exc:
        raise CalendarSyncError(
            f"Google カレンダーイベント削除に失敗しました event_id={event_id}",
        ) from exc
