"""予定 JSON → Google カレンダー同期 CLI。"""

from __future__ import annotations

from google_ical.cli import run_command
from google_ical.config import load_config
from google_ical.content.events.loader import load_merged_events
from google_ical.content.google.auth import ensure_token_file_exists
from google_ical.content.google.sync import sync_events_to_google_calendar
from google_ical.pipeline_log import log_info, log_stage_start, log_stage_success


def main() -> int:
    summary = ""

    def _run() -> None:
        nonlocal summary
        log_stage_start("設定読込")
        config = load_config()
        ensure_token_file_exists()
        log_stage_success("設定読込")

        log_stage_start("予定 JSON 読込", detail=str(config.events_json_dir))
        events = load_merged_events(config.events_json_dir)
        log_stage_success("予定 JSON 読込", detail=f"events={len(events)}")

        log_stage_start("Google 反映", detail=f"calendar_id={config.google_calendar_id}")
        sync_events_to_google_calendar(config, events)
        log_stage_success("Google 反映")
        summary = f"events={len(events)}, calendar_id={config.google_calendar_id}"

    code = run_command(_run)
    if code == 0:
        log_info(f"バッチ完了: sync_calendar ({summary})")
    return code
