"""ChatGPT 返却の events[] をゴミ収集日用 CalendarEvent へ正規化。"""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from pydantic import ValidationError

from google_ical.config import TIMEZONE
from google_ical.content.events.datetime_parse import parse_strict_jst_datetime
from google_ical.content.events.models import CalendarEvent
from google_ical.content.events.schemas import EventRecordSchema
from google_ical.exceptions import OpenAIClientError

_TARGET_MONTH_RE = re.compile(r"^\d{4}-\d{2}$")


def current_jst_target_month() -> str:
    """月次バッチの対象月を返す（JST の YYYY-MM）。
    例: 2026年6月実行 → "2026-06"
    """
    return datetime.now(ZoneInfo(TIMEZONE)).strftime("%Y-%m")


def normalize_gomi_events(
    output_text: str,
    *,
    target_month: str | None = None,
) -> tuple[CalendarEvent, ...]:
    """ChatGPT 返却 JSON を検証し、CalendarEvent 列へ正規化する。
    例: '[{"summary":"可燃ごみ","start":"2026-06-03T00:00:00",...}]' → (CalendarEvent(...),)
    """
    if target_month is not None:
        _validate_target_month(target_month)

    raw = _loads_json_only(output_text)
    if isinstance(raw, dict):
        raw = raw.get("events")
    if not isinstance(raw, list):
        raise OpenAIClientError("events[] が見つかりません")
    if not raw:
        return ()

    events = tuple(_normalize_event(item) for item in raw)
    sorted_events = tuple(sorted(events, key=lambda event: (event.start, event.end, event.summary)))
    deduplicated = _deduplicate_events(sorted_events)
    if target_month is None:
        return deduplicated
    return _filter_events_for_target_month(deduplicated, target_month)


def _deduplicate_events(events: tuple[CalendarEvent, ...]) -> tuple[CalendarEvent, ...]:
    """summary/start/end が同一の重複を除く。
    例: 同じ可燃ごみ×2件 → 1件にまとめる
    """
    seen: set[tuple[str, str, str]] = set()
    unique: list[CalendarEvent] = []
    for event in events:
        key = (event.summary, event.start, event.end)
        if key in seen:
            continue
        seen.add(key)
        unique.append(event)
    return tuple(unique)


def _validate_target_month(target_month: str) -> None:
    """target_month が YYYY-MM 形式か検証する。"""
    if not _TARGET_MONTH_RE.fullmatch(target_month):
        raise OpenAIClientError(f"target_month の形式が不正です: {target_month!r}")


def _filter_events_for_target_month(
    events: tuple[CalendarEvent, ...],
    target_month: str,
) -> tuple[CalendarEvent, ...]:
    """対象月のイベントだけ残す。
    例: target_month="2026-06" → start が 6 月のものだけ
    """
    return tuple(event for event in events if _event_start_month(event) == target_month)


def _event_start_month(event: CalendarEvent) -> str:
    return parse_strict_jst_datetime(event.start).strftime("%Y-%m")


def _loads_json_only(output_text: str) -> Any:
    """ChatGPT 応答から JSON だけを読み取る（Markdown コードブロックは拒否）。"""
    text = output_text.strip()
    if text.startswith("```"):
        raise OpenAIClientError("JSON 以外の Markdown が含まれています")
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise OpenAIClientError("ChatGPT 応答のJSON解析に失敗しました") from exc


def _normalize_event(raw: object) -> CalendarEvent:
    """events[] の 1 要素を検証して CalendarEvent にする（ゴミ収集日は all_day 必須）。"""
    if not isinstance(raw, dict):
        raise OpenAIClientError("events[] の要素がオブジェクトではありません")

    if raw.get("all_day") is not True:
        raise OpenAIClientError("ゴミ収集日は all_day: true が必要です")

    try:
        parsed = EventRecordSchema.model_validate(raw)
    except ValidationError as exc:
        raise OpenAIClientError(_validation_error_message(exc)) from exc

    if not parsed.summary.strip():
        raise OpenAIClientError("summary が空です")

    return CalendarEvent(
        summary=parsed.summary.strip(),
        start=parsed.start,
        end=parsed.end,
        description=parsed.description.strip() if parsed.description else None,
        all_day=parsed.all_day,
    )


def _validation_error_message(exc: ValidationError) -> str:
    for error in exc.errors():
        message = error.get("msg")
        if isinstance(message, str) and message:
            return message.removeprefix("Value error, ")
    return "events[] の形式が不正です"
