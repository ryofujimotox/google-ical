"""予定 JSON のドメイン型と内部 ID 生成。"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass(frozen=True)
class CalendarEvent:
    """予定 JSON の events[] 1 件。"""

    summary: str
    start: str
    end: str
    description: str | None = None
    all_day: bool = False


@dataclass(frozen=True)
class EventsFile:
    """予定 JSON ファイル 1 件分。"""

    source: str
    filename: str
    events: tuple[CalendarEvent, ...]


@dataclass(frozen=True)
class MergedEvent:
    """合成後の 1 イベント（内部 ID 付き）。"""

    event_id: str
    source: str
    filename: str
    summary: str
    start: str
    end: str
    description: str | None
    all_day: bool


def generate_event_id(
    *,
    source: str,
    filename: str,
    summary: str,
    start: str,
    end: str,
) -> str:
    """source・ファイル名・summary・start・end から内部 ID を生成する。"""
    payload = "\n".join((source, filename, summary, start, end))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
