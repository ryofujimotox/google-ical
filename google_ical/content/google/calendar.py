"""Google Calendar API への薄いアダプタ。"""

from __future__ import annotations

from typing import Any, Protocol

from google_ical.exceptions import CalendarSyncError


class CalendarService(Protocol):
    def events(self) -> Any: ...


def build_calendar_service(credentials: object) -> CalendarService:
    """OAuth 資格情報から Calendar API クライアントを作る。
    例: Credentials(...) → calendar v3 service
    """
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
    google_ical_id_key: str,
    google_ical_source_key: str,
) -> dict[str, dict[str, Any]]:
    """本リポ管理の既存予定を google_ical_id キー付きで取得する。
    例: → {"a1b2...": {"id": "google_evt_id", "summary": "可燃ごみ", ...}, ...}
    """
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
                managed_id = private.get(google_ical_id_key)
                if managed_id and private.get(google_ical_source_key):
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
    """Google カレンダーへイベントを作成または更新する。
    existing あり: patch。なし: insert。戻り値は Google 側 event ID。
    """
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
    """JSON から消えた管理予定を Google カレンダーから削除する。"""
    try:
        service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
    except Exception as exc:
        raise CalendarSyncError(
            f"Google カレンダーイベント削除に失敗しました event_id={event_id}",
        ) from exc
