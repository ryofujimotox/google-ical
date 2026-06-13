"""Google Calendar へ同期する予定の共通モデル。"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Literal
from zoneinfo import ZoneInfo

JST = ZoneInfo("Asia/Tokyo")

EventKind = Literal["all_day", "timed"]


@dataclass(frozen=True)
class CalendarEvent:
    """JSON とゴミPDFの両方から作る予定。"""

    source: str
    title: str
    start: date | datetime
    end: date | datetime | None = None
    description: str = ""
    location: str = ""
    uid: str | None = None
    color_id: str | None = None
    reminders: tuple[int, ...] = field(default_factory=tuple)

    @property
    def kind(self) -> EventKind:
        return "all_day" if isinstance(self.start, date) and not isinstance(self.start, datetime) else "timed"

    def normalized_end(self) -> date | datetime:
        """Google Calendar が必要とする排他的な終了を補う。"""

        if self.end is not None:
            return self.end
        if self.kind == "all_day":
            return self.start + timedelta(days=1)  # type: ignore[operator]
        start_dt = self.start if isinstance(self.start, datetime) else datetime.combine(self.start, time.min)
        return start_dt + timedelta(hours=1)

    def stable_id(self, namespace: str) -> str:
        """同じ入力から同じ Google 予定を探すための短いID。"""

        if self.uid:
            seed = f"{namespace}:{self.source}:{self.uid}"
        else:
            seed = f"{namespace}:{self.source}:{self.title}:{self.start}:{self.normalized_end()}"
        return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:32]

    def overlaps(self, start: datetime, end: datetime) -> bool:
        event_start = as_datetime(self.start)
        event_end = as_datetime(self.normalized_end())
        return event_start < end and start < event_end


@dataclass(frozen=True)
class EventWindow:
    """同期対象の半開区間。"""

    start: datetime
    end: datetime

    @classmethod
    def from_days(cls, today: date, days: int) -> "EventWindow":
        return cls(
            start=datetime.combine(today, time.min, tzinfo=JST),
            end=datetime.combine(today + timedelta(days=days), time.min, tzinfo=JST),
        )


def as_datetime(value: date | datetime) -> datetime:
    """date / datetime を比較可能な JST datetime にそろえる。"""

    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=JST)
        return value.astimezone(JST)
    return datetime.combine(value, time.min, tzinfo=JST)


def parse_event(raw: dict[str, Any], *, source: str) -> CalendarEvent:
    """固定予定JSONの1要素を `CalendarEvent` に変換する。"""

    title = str(raw.get("title") or raw.get("summary") or "").strip()
    if not title:
        raise ValueError("イベントの title は必須です")

    start_raw = str(raw.get("start") or "").strip()
    if not start_raw:
        raise ValueError(f"イベント {title} の start は必須です")
    start = parse_date_or_datetime(start_raw)

    end_raw = str(raw.get("end") or "").strip()
    end = parse_date_or_datetime(end_raw) if end_raw else None

    reminders_raw = raw.get("reminders", ())
    reminders = tuple(int(minutes) for minutes in reminders_raw) if reminders_raw else ()

    return CalendarEvent(
        source=source,
        title=title,
        start=start,
        end=end,
        description=str(raw.get("description") or ""),
        location=str(raw.get("location") or ""),
        uid=str(raw.get("uid") or raw.get("id") or "").strip() or None,
        color_id=str(raw.get("color_id") or raw.get("colorId") or "").strip() or None,
        reminders=reminders,
    )


def parse_date_or_datetime(value: str) -> date | datetime:
    """ISO8601 の日付または日時を受け付ける。"""

    normalized = value.replace("Z", "+00:00")
    if "T" not in normalized:
        return date.fromisoformat(normalized)
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=JST)
    else:
        parsed = parsed.astimezone(JST)
    return parsed


def sort_events(events: list[CalendarEvent]) -> list[CalendarEvent]:
    """同期やテストの出力順を決定的にする。"""

    return sorted(events, key=lambda event: (event.source, as_datetime(event.start), event.uid or event.title))
