"""ical JSON ディレクトリの読込とイベント合成。"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from google_ical.content.events.models import CalendarEvent, EventsFile, MergedEvent, generate_event_id
from google_ical.content.events.schemas import EventsFileSchema
from google_ical.exceptions import EventsError


def load_events_files(ical_jsons_dir: Path) -> tuple[EventsFile, ...]:
    """ical JSON ディレクトリ内の *.json をファイル名順で読む。
    例: Path("config/ical_jsons") → (EventsFile(source="gomi", ...), EventsFile(source="manual", ...))
    """
    if not ical_jsons_dir.is_dir():
        raise EventsError(f"ical JSON ディレクトリがありません: {ical_jsons_dir}")

    json_paths = sorted(ical_jsons_dir.glob("*.json"), key=lambda path: path.name)
    if not json_paths:
        raise EventsError(f"ical JSON が 1 件もありません: {ical_jsons_dir}")

    return tuple(_load_events_file(path) for path in json_paths)


def load_merged_events(ical_jsons_dir: Path) -> tuple[MergedEvent, ...]:
    """全 JSON の events[] を合成し、内部 ID を付与する。
    例: Path("config/ical_jsons") → (MergedEvent(event_id="a1b2...", summary="可燃ごみ", ...), ...)
    """
    merged: list[MergedEvent] = []
    for events_file in load_events_files(ical_jsons_dir):
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
    """1 ファイルを検証して EventsFile に変換する。
    例: Path("config/ical_jsons/gomi.json") → EventsFile(source="gomi", filename="gomi.json", ...)
    """
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise EventsError(f"ical JSON の形式が不正です: {path}")
        parsed = EventsFileSchema.model_validate(raw)
    except json.JSONDecodeError as exc:
        raise EventsError(f"ical JSON の解析に失敗しました: {path}") from exc
    except ValidationError as exc:
        raise EventsError(f"ical JSON の形式が不正です: {path}") from exc

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
