"""Google Calendar API への薄いアダプタ。"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Protocol

from google_ical.content.events.writer import PRIVATE_NAMESPACE, PRIVATE_SOURCE_ID

SCOPES = ("https://www.googleapis.com/auth/calendar",)


class CalendarService(Protocol):
    def events(self) -> Any: ...


def build_calendar_service(service_account_file: Path) -> CalendarService:
    """サービスアカウントで Calendar API クライアントを作る。"""

    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
    except ModuleNotFoundError as exc:
        raise RuntimeError("Google Calendar同期には google-api-python-client と google-auth のインストールが必要です") from exc

    credentials = service_account.Credentials.from_service_account_file(
        str(service_account_file), scopes=SCOPES
    )
    return build("calendar", "v3", credentials=credentials, cache_discovery=False)


def list_managed_events(
    service: CalendarService,
    *,
    calendar_id: str,
    namespace: str,
    time_min: datetime,
    time_max: datetime,
) -> dict[str, dict[str, Any]]:
    """同期対象期間内にある、このバッチ管理の既存予定を取得する。"""

    request = service.events().list(
        calendarId=calendar_id,
        timeMin=time_min.isoformat(),
        timeMax=time_max.isoformat(),
        singleEvents=True,
        orderBy="startTime",
        privateExtendedProperty=f"{PRIVATE_NAMESPACE}={namespace}",
    )
    managed: dict[str, dict[str, Any]] = {}
    while request is not None:
        response = request.execute()
        for item in response.get("items", []):
            private = item.get("extendedProperties", {}).get("private", {})
            source_id = private.get(PRIVATE_SOURCE_ID)
            if source_id:
                managed[source_id] = item
        request = service.events().list_next(request, response)
    return managed


def upsert_event(
    service: CalendarService,
    *,
    calendar_id: str,
    body: dict[str, Any],
    existing: dict[str, Any] | None,
) -> str:
    """既存があれば更新、なければ作成し、Google 側 ID を返す。"""

    if existing:
        response = service.events().update(
            calendarId=calendar_id,
            eventId=existing["id"],
            body=body,
        ).execute()
    else:
        response = service.events().insert(calendarId=calendar_id, body=body).execute()
    return str(response["id"])


def delete_event(service: CalendarService, *, calendar_id: str, event_id: str) -> None:
    """入力から消えた管理予定を削除する。"""

    service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
