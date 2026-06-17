"""iCalJSON ディレクトリの読込とイベント合成。"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from google_ical.content.events.models import CalendarEvent, EventsFile, MergedEvent, generate_event_id
from google_ical.content.events.schemas import EventsFileSchema
from google_ical.exceptions import EventsError


def event_source_from_json_path(path: Path) -> str:
    """JSON ファイル名（拡張子なし）から google_ical_source 用ラベルを返す。
    例: Path("config/ical_jsons/gomi.json") → "gomi"
    """
    if path.suffix != ".json":
        raise EventsError(f"JSON ファイル名から source を決められません: {path}")
    source = path.stem
    if not source or source.startswith("."):
        raise EventsError(f"JSON ファイル名から source を決められません: {path}")
    return source


def load_events_files(ical_jsons_dir: Path) -> tuple[EventsFile, ...]:
    """iCalJSON ディレクトリ内の *.json をファイル名順で読む。
    例: Path("config/ical_jsons") → (EventsFile(source="gomi", ...), EventsFile(source="sample", ...))
    """
    if not ical_jsons_dir.is_dir():
        raise EventsError(f"iCalJSON ディレクトリがありません: {ical_jsons_dir}")

    json_paths = sorted(ical_jsons_dir.glob("*.json"), key=lambda path: path.name)
    if not json_paths:
        raise EventsError(f"iCalJSON が 1 件もありません: {ical_jsons_dir}")

    return tuple(_load_events_file(path) for path in json_paths)


def load_merged_events(ical_jsons_dir: Path) -> tuple[MergedEvent, ...]:
    """全 JSON の events[] を合成し、内部 ID を付与する。
    例: Path("config/ical_jsons") → (MergedEvent(event_id="a1b2...", summary="可燃ごみ", ...), ...)
    """
    merged: list[MergedEvent] = []
    seen_ids: dict[str, str] = {}
    for events_file in load_events_files(ical_jsons_dir):
        for event in events_file.events:
            event_id = generate_event_id(
                filename=events_file.filename,
                summary=event.summary,
                start=event.start,
                end=event.end,
            )
            if event_id in seen_ids:
                raise EventsError(
                    "iCalJSON の内部 ID が重複しています: "
                    f"{event_id} ({seen_ids[event_id]} と {events_file.filename})",
                )
            seen_ids[event_id] = events_file.filename
            merged.append(
                MergedEvent(
                    event_id=event_id,
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
            raise EventsError(f"iCalJSON の形式が不正です: {path}")
        parsed = EventsFileSchema.model_validate(raw)
    except json.JSONDecodeError as exc:
        raise EventsError(f"iCalJSON の解析に失敗しました: {path}") from exc
    except ValidationError as exc:
        raise EventsError(f"iCalJSON の形式が不正です: {path}") from exc

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
    return EventsFile(source=event_source_from_json_path(path), filename=path.name, events=events)
