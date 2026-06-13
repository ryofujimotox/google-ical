"""予定 JSON ディレクトリの読込とイベント合成。"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from google_ical.content.events.models import CalendarEvent, EventsFile, MergedEvent, generate_event_id
from google_ical.content.events.schemas import EventsFileSchema
from google_ical.exceptions import EventsError


def load_events_files(events_json_dir: Path) -> tuple[EventsFile, ...]:
    """ディレクトリ内の *.json をファイル名辞書順で読み、EventsFile のタプルを返す。"""
    if not events_json_dir.is_dir():
        raise EventsError(f"予定 JSON ディレクトリがありません: {events_json_dir}")

    json_paths = sorted(events_json_dir.glob("*.json"), key=lambda path: path.name)
    if not json_paths:
        raise EventsError(f"予定 JSON が 1 件もありません: {events_json_dir}")

    return tuple(_load_events_file(path) for path in json_paths)


def load_merged_events(events_json_dir: Path) -> tuple[MergedEvent, ...]:
    """全 JSON の events[] を合成し、内部 ID 付きで返す。"""
    merged: list[MergedEvent] = []
    for events_file in load_events_files(events_json_dir):
        for event in events_file.events:
            merged.append(
                MergedEvent(
                    event_id=generate_event_id(
                        source=events_file.source,
                        filename=events_file.filename,
                        summary=event.summary,
                        start=event.start,
                        end=event.end,
                    ),
                    source=events_file.source,
                    filename=events_file.filename,
                    summary=event.summary,
                    start=event.start,
                    end=event.end,
                    description=event.description,
                    all_day=event.all_day,
                ),
            )
    return tuple(merged)


def _load_events_file(path: Path) -> EventsFile:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        parsed = EventsFileSchema.model_validate(raw)
    except json.JSONDecodeError as exc:
        raise EventsError(f"予定 JSON の解析に失敗しました: {path}") from exc
    except ValidationError as exc:
        raise EventsError(f"予定 JSON の形式が不正です: {path}") from exc

    events = tuple(
        CalendarEvent(
            summary=item.summary,
            start=item.start,
            end=item.end,
            description=item.description,
            all_day=item.all_day,
        )
        for item in parsed.events
    )
    return EventsFile(source=parsed.source, filename=path.name, events=events)
