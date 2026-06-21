"""Google カレンダーへの予定同期。

extendedProperties.private に google_ical_id / google_ical_source を保存し、
本リポ管理イベントのみ作成・更新・削除する。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal
from zoneinfo import ZoneInfo

from google_ical.config import (
    DATETIME_FORMAT,
    GOOGLE_ICAL_ID_KEY,
    GOOGLE_ICAL_SOURCE_KEY,
    TIMEZONE,
    app_config as config,
)
from google_ical.content.events.datetime_parse import format_jst_datetime, parse_strict_jst_datetime
from google_ical.content.events.models import MergedEvent
from google_ical.content.google.auth import load_calendar_credentials
from google_ical.content.google.calendar import build_calendar_service, delete_event, list_managed_events, upsert_event
from google_ical.exceptions import CalendarSyncError, GoogleAuthError


@dataclass(frozen=True)
class _AppliedMutation:
    """同期失敗時に元へ戻すため、成功した API 変更を記録する。"""

    kind: Literal["insert", "update", "delete"]
    google_event_id: str
    rollback_body: dict[str, Any] | None


def sync_events_to_google_calendar(events: tuple[MergedEvent, ...]) -> None:
    """合成済み予定を Google カレンダーへ反映する（作成・更新・削除）。
    例: (MergedEvent(...),) → カレンダーが JSON と同じ状態になる
    """
    calendar_id = config.google_calendar_id
    try:
        service = build_calendar_service(load_calendar_credentials(config.oauth_token_path))
        existing = list_managed_events(
            service,
            calendar_id=calendar_id,
            google_ical_id_key=GOOGLE_ICAL_ID_KEY,
            google_ical_source_key=GOOGLE_ICAL_SOURCE_KEY,
        )
        desired = _build_desired_events(events)
        _apply_sync(service, calendar_id, existing, desired)
    except (CalendarSyncError, GoogleAuthError):
        raise
    except Exception as exc:
        raise CalendarSyncError(
            f"Google カレンダー同期に失敗しました calendar_id={calendar_id}",
        ) from exc


def _build_desired_events(events: tuple[MergedEvent, ...]) -> dict[str, dict[str, Any]]:
    """MergedEvent 列を Google API 用 body 辞書へ変換する（内部 ID をキーにする）。"""
    desired: dict[str, dict[str, Any]] = {}
    for event in events:
        if event.event_id in desired:
            raise CalendarSyncError(f"iCalJSON の内部 ID が重複しています: {event.event_id}")
        desired[event.event_id] = _event_to_google_body(event)
    return desired


def _apply_sync(
    service: object,
    calendar_id: str,
    existing: dict[str, dict[str, Any]],
    desired: dict[str, dict[str, Any]],
) -> None:
    """desired に合わせて insert / update / delete する。途中失敗時はロールバックする。"""
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
    """MergedEvent を Google Calendar API のイベント body に変換する。
    例: 終日イベント → {"summary": "可燃ごみ", "start": {"date": "2026-06-03"}, ...}
    """
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
    """アプリ日時文字列を Google API の start/end 形式へ変換する。"""
    parsed = parse_strict_jst_datetime(value)
    if all_day:
        return {"date": parsed.date().isoformat()}
    return {
        "dateTime": format_jst_datetime(parsed),
        "timeZone": TIMEZONE,
    }


def _needs_update(current: dict[str, Any], desired: dict[str, Any]) -> bool:
    """既存 Google イベントと desired body に差分があるか判定する。"""
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
    """Google 返却と desired body をアプリ TZ 基準の比較キーにそろえる。"""
    if "date" in value:
        return (str(value["date"]), "")
    dt_raw = str(value.get("dateTime", ""))
    if not dt_raw:
        return ("", "")
    normalized = dt_raw.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        tz_name = str(value.get("timeZone") or TIMEZONE)
        parsed = parsed.replace(tzinfo=ZoneInfo(tz_name))
    localized = parsed.astimezone(ZoneInfo(TIMEZONE))
    return (localized.strftime(DATETIME_FORMAT), TIMEZONE)


def _text_value(value: object) -> str:
    return value if isinstance(value, str) else ""
