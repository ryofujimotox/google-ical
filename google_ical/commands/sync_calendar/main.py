"""JSON とゴミPDFの予定を Google Calendar に同期する。"""

from __future__ import annotations

import argparse
import sys
from datetime import date

from google_ical.config import ConfigError, load_config
from google_ical.content.events.models import EventWindow
from google_ical.content.events.writer import filter_window, load_events, to_google_event
from google_ical.content.gomi.pipeline import events_from_sources
from google_ical.google.calendar import build_calendar_service, delete_event, list_managed_events, upsert_event


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="JSON とゴミPDFから Google Calendar を同期します")
    parser.add_argument("--dry-run", action="store_true", help="Calendar APIへ書き込まず件数だけ表示します")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        config = load_config()
        today = date.today()
        window = EventWindow.from_days(today, config.sync_days)
        events = load_events(config.event_json_paths)
        if config.gomi_pdf_sources:
            gomi_year = config.gomi_year or today.year
            events.extend(events_from_sources(config.gomi_pdf_sources, year=gomi_year))
        target_events = filter_window(events, window)

        if args.dry_run:
            print(f"同期対象予定: {len(target_events)}件")
            return 0

        service = build_calendar_service(config.google_service_account_file)
        existing = list_managed_events(
            service,
            calendar_id=config.google_calendar_id,
            namespace=config.sync_namespace,
            time_min=window.start,
            time_max=window.end,
        )
        desired_ids: set[str] = set()
        for event in target_events:
            source_id = event.stable_id(config.sync_namespace)
            desired_ids.add(source_id)
            body = to_google_event(event, namespace=config.sync_namespace)
            google_id = upsert_event(
                service,
                calendar_id=config.google_calendar_id,
                body=body,
                existing=existing.get(source_id),
            )
            print(f"同期しました source_id={source_id} google_id={google_id} title={event.title}")

        for source_id, old_event in existing.items():
            if source_id not in desired_ids:
                delete_event(service, calendar_id=config.google_calendar_id, event_id=old_event["id"])
                print(f"削除しました source_id={source_id} google_id={old_event['id']}")
    except (ConfigError, OSError, ValueError) as exc:
        print(f"同期エラー: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
