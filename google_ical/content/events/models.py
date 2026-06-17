"""iCalJSON のドメイン型と内部 ID 生成。"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass(frozen=True)
class CalendarEvent:
    """iCalJSON の events[] 1 件。"""

    summary: str
    start: str
    end: str
    description: str | None = None
    all_day: bool = False


@dataclass(frozen=True)
class EventsFile:
    """iCalJSON ファイル 1 件分。"""

    source: str  # ファイル名（.json を除く）。Google の google_ical_source 用
    filename: str
    events: tuple[CalendarEvent, ...]


@dataclass(frozen=True)
class MergedEvent:
    """合成後の 1 イベント（内部 ID 付き）。"""

    event_id: str
    source: str  # EventsFile.source と同じ（google_ical_source 用）
    filename: str
    summary: str
    start: str
    end: str
    description: str | None
    all_day: bool


def generate_event_id(
    *,
    filename: str,
    summary: str,
    start: str,
    end: str,
) -> str:
    """予定の内容から冪等な内部 ID（SHA-256 hex）を生成する。
    例: filename="gomi.json", summary="可燃ごみ", start="2026-06-03T00:00:00", ... → 64 文字の hex
    """
    payload = "\n".join((filename, summary, start, end))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
