"""ChatGPT 返却の events[] をゴミ収集日用 CalendarEvent へ正規化。"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from pydantic import ValidationError

from google_ical.constants import JST_DATETIME_FORMAT
from google_ical.content.events.models import CalendarEvent
from google_ical.content.events.schemas import EventRecordSchema
from google_ical.exceptions import OpenAIClientError


def normalize_gomi_events(output_text: str) -> tuple[CalendarEvent, ...]:
    """JSON 文字列を検証し、決定的な順序の CalendarEvent タプルを返す。

    例: '[{"summary":"可燃ごみ","start":"2026-06-03T00:00:00","end":"2026-06-04T00:00:00","all_day":true}]'
        → (CalendarEvent(summary="可燃ごみ", ...),)
    """
    raw = _loads_json_only(output_text)
    if isinstance(raw, dict):
        raw = raw.get("events")
    if not isinstance(raw, list) or not raw:
        raise OpenAIClientError("events[] が見つかりません")

    events = tuple(_normalize_event(item) for item in raw)
    return tuple(sorted(events, key=lambda event: (event.start, event.end, event.summary)))


def _loads_json_only(output_text: str) -> Any:
    text = output_text.strip()
    if text.startswith("```"):
        raise OpenAIClientError("JSON 以外の Markdown が含まれています")
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise OpenAIClientError("ChatGPT 応答のJSON解析に失敗しました") from exc


def _normalize_event(raw: object) -> CalendarEvent:
    if not isinstance(raw, dict):
        raise OpenAIClientError("events[] の要素がオブジェクトではありません")

    try:
        parsed = EventRecordSchema.model_validate(raw)
    except ValidationError as exc:
        raise OpenAIClientError("events[] の形式が不正です") from exc

    if not parsed.summary.strip():
        raise OpenAIClientError("summary が空です")
    start = _parse_datetime(parsed.start, "start")
    end = _parse_datetime(parsed.end, "end")
    if not parsed.all_day:
        raise OpenAIClientError("ゴミ収集日は all_day: true が必要です")
    if start >= end:
        raise OpenAIClientError("end は start より後にしてください")
    if start.time().isoformat() != "00:00:00" or end.time().isoformat() != "00:00:00":
        raise OpenAIClientError("終日イベントの start/end は 00:00:00 にしてください")
    if (end.date() - start.date()).days != 1:
        raise OpenAIClientError("ゴミ収集日は 1 日分の終日イベントにしてください")

    return CalendarEvent(
        summary=parsed.summary.strip(),
        start=parsed.start,
        end=parsed.end,
        description=parsed.description.strip() if parsed.description else None,
        all_day=parsed.all_day,
    )


def _parse_datetime(value: str, field_name: str) -> datetime:
    try:
        return datetime.strptime(value, JST_DATETIME_FORMAT)
    except ValueError as exc:
        raise OpenAIClientError(f"{field_name} の日時形式が不正です: {value}") from exc
