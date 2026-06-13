"""Google カレンダーへの予定同期。

extendedProperties.private に google_ical_id / google_ical_source を保存し、
本リポ管理イベントのみ作成・更新・削除する。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal
from zoneinfo import ZoneInfo

from google_ical.config import AppConfig
from google_ical.constants import (
    GOOGLE_ICAL_ID_KEY,
    GOOGLE_ICAL_SOURCE_KEY,
    JST_DATETIME_FORMAT,
    JST_TIMEZONE,
)
from google_ical.content.events.datetime_parse import format_jst_datetime, parse_strict_jst_datetime
from google_ical.content.events.models import MergedEvent
from google_ical.content.google.auth import load_calendar_credentials
from google_ical.content.google.calendar import build_calendar_service, delete_event, list_managed_events, upsert_event
from google_ical.exceptions import CalendarSyncError, GoogleAuthError

_JST = ZoneInfo(JST_TIMEZONE)


@dataclass(frozen=True)
class _AppliedMutation:
    """同期失敗時に元へ戻すため、成功した API 変更を記録する。"""

    kind: Literal["insert", "update", "delete"]
    google_event_id: str
    rollback_body: dict[str, Any] | None


def sync_events_to_google_calendar(
    config: AppConfig,
    events: tuple[MergedEvent, ...],
) -> None:
    """予定JSONの合成結果に合わせ、管理イベントを作成・更新・削除する。"""
    calendar_id = config.google_calendar_id
    try:
        service = build_calendar_service(load_calendar_credentials())
        existing = list_managed_events(service, calendar_id=calendar_id)
        desired = _build_desired_events(events)
        _apply_sync(service, calendar_id, existing, desired)
    except (CalendarSyncError, GoogleAuthError):
        raise
    except Exception as exc:
        raise CalendarSyncError(
            f"Google カレンダー同期に失敗しました calendar_id={calendar_id}",
        ) from exc


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
    applied: list[_AppliedMutation] = []
    try:
        for event_id, body in desired.items():
            current = existing.get(event_id)
            if current is None:
                google_id = upsert_event(service, calendar_id=calendar_id, body=body, existing=None)
                applied.append(_AppliedMutation("insert", google_id, None))
            elif _needs_update(current, body):
                snapshot = _snapshot_event(current)
                upsert_event(service, calendar_id=calendar_id, body=body, existing=current)
                applied.append(_AppliedMutation("update", str(current["id"]), snapshot))

        for event_id, current in existing.items():
            if event_id not in desired:
                google_id = str(current["id"])
                delete_event(service, calendar_id=calendar_id, event_id=google_id)
                applied.append(_AppliedMutation("delete", google_id, _snapshot_event(current)))
    except CalendarSyncError:
        _rollback_mutations(service, calendar_id, applied)
        raise


def _rollback_mutations(
    service: object,
    calendar_id: str,
    applied: list[_AppliedMutation],
) -> None:
    """途中失敗時に、成功済みの insert / update / delete を逆順で取り消す。"""
    errors: list[str] = []
    for mutation in reversed(applied):
        try:
            if mutation.kind == "insert":
                delete_event(service, calendar_id=calendar_id, event_id=mutation.google_event_id)
            elif mutation.kind == "update":
                if mutation.rollback_body is None:
                    continue
                upsert_event(
                    service,
                    calendar_id=calendar_id,
                    body=mutation.rollback_body,
                    existing={"id": mutation.google_event_id},
                )
            elif mutation.kind == "delete":
                if mutation.rollback_body is None:
                    continue
                upsert_event(
                    service,
                    calendar_id=calendar_id,
                    body=mutation.rollback_body,
                    existing=None,
                )
        except CalendarSyncError as exc:
            errors.append(str(exc))
    if errors:
        raise CalendarSyncError(
            "Google カレンダーのロールバックに失敗しました: " + "; ".join(errors),
        )


def _snapshot_event(event: dict[str, Any]) -> dict[str, Any]:
    """update / delete のロールバック用に、Google イベントの主要フィールドだけ残す。"""
    return {
        "summary": event.get("summary"),
        "description": event.get("description", ""),
        "start": event.get("start"),
        "end": event.get("end"),
        "extendedProperties": event.get("extendedProperties"),
    }


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
    parsed = parse_strict_jst_datetime(value)
    if all_day:
        return {"date": parsed.date().isoformat()}
    return {"dateTime": format_jst_datetime(parsed), "timeZone": JST_TIMEZONE}


def _needs_update(current: dict[str, Any], desired: dict[str, Any]) -> bool:
    if current.get("summary") != desired.get("summary"):
        return True
    if _text_value(current.get("description")) != _text_value(desired.get("description")):
        return True
    if not _google_times_equal(current.get("start"), desired.get("start")):
        return True
    if not _google_times_equal(current.get("end"), desired.get("end")):
        return True

    current_private = current.get("extendedProperties", {}).get("private", {})
    desired_private = desired.get("extendedProperties", {}).get("private", {})
    return any(current_private.get(key) != value for key, value in desired_private.items())


def _google_times_equal(left: object, right: object) -> bool:
    if not isinstance(left, dict) or not isinstance(right, dict):
        return left == right
    return _normalize_google_time(left) == _normalize_google_time(right)


def _normalize_google_time(value: dict[str, Any]) -> tuple[str, str]:
    """Google 返却と desired body を JST 基準の比較キーにそろえる。"""
    if "date" in value:
        return (str(value["date"]), "")
    dt_raw = str(value.get("dateTime", ""))
    if not dt_raw:
        return ("", "")
    normalized = dt_raw.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        tz_name = str(value.get("timeZone") or JST_TIMEZONE)
        parsed = parsed.replace(tzinfo=ZoneInfo(tz_name))
    jst = parsed.astimezone(_JST)
    return (jst.strftime(JST_DATETIME_FORMAT), JST_TIMEZONE)


def _text_value(value: object) -> str:
    return value if isinstance(value, str) else ""
