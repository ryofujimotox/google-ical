"""ゴミ収集日 PDF → 予定 JSON CLI。"""

from __future__ import annotations

from pathlib import Path

from google_ical.cli import run_command
from google_ical.config import load_config
from google_ical.content.events.writer import save_events_file
from google_ical.content.gomi.config import load_gomi_config, resolve_gomi_output_path
from google_ical.content.gomi.normalize import current_jst_target_month
from google_ical.content.gomi.pipeline import convert_gomi_pdf, fetch_gomi_pdf_url
from google_ical.content.pdf import download_pdf
from google_ical.pipeline_log import log_info, log_stage_start, log_stage_success


def main() -> int:
    output_path = ""

    def _run() -> None:
        nonlocal output_path

        log_stage_start("設定読込")
        config = load_config()
        gomi_config = load_gomi_config(config.gomi_config_path)
        output_path = str(resolve_gomi_output_path(config.events_json_dir, gomi_config.output_file))
        log_stage_success("設定読込")

        if gomi_config.pdf_url_override:
            url_detail = "pdf_url_override を使用"
        else:
            url_detail = f"region={gomi_config.region}"
        log_stage_start("PDF URL 取得", detail=url_detail)
        pdf_url = fetch_gomi_pdf_url(config, gomi_config)
        log_stage_success("PDF URL 取得", detail=pdf_url)

        log_stage_start("PDF ダウンロード", detail=pdf_url)
        pdf_bytes = download_pdf(pdf_url)
        log_stage_success("PDF ダウンロード", detail=f"bytes={len(pdf_bytes)}")

        log_stage_start("PDF→JSON 変換")
        target_month = current_jst_target_month()
        events = convert_gomi_pdf(config, pdf_bytes, target_month=target_month)
        log_stage_success("PDF→JSON 変換", detail=f"events={len(events)} month={target_month}")

        log_stage_start("JSON 保存", detail=output_path)
        save_events_file(Path(output_path), source="gomi", events=events)
        log_stage_success("JSON 保存", detail=output_path)

    code = run_command(_run)
    if code == 0:
        log_info(f"バッチ完了: fetch_gomi (output={output_path})")
    return code
