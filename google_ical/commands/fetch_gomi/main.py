"""ゴミ収集日 PDF → 予定 JSON CLI。"""

from __future__ import annotations

from google_ical.cli import run_command
from google_ical.config import app_config as config, check_fetch_gomi_config
from google_ical.content.events.writer import save_events_file
from google_ical.content.gomi.normalize import current_jst_target_month
from google_ical.content.gomi.pipeline import convert_gomi_pdf, fetch_gomi_pdf_url, gomi_event_source
from google_ical.content.pdf import download_pdf, save_pdf
from google_ical.pipeline_log import log_info, log_stage_start, log_stage_success


def main() -> int:
    output_path = ""

    def _run() -> None:
        nonlocal output_path

        log_stage_start("設定読込")
        check_fetch_gomi_config()
        output_path = str(config.ical_jsons_gomi)
        log_stage_success("設定読込")

        if config.gomi_pdf_url_override:
            url_detail = "pdf_url_override を使用"
        else:
            url_detail = f"region={config.gomi_region}"
        log_stage_start("PDF URL 取得", detail=url_detail)
        pdf_url = fetch_gomi_pdf_url()
        log_stage_success("PDF URL 取得", detail=pdf_url)

        log_stage_start("PDF ダウンロード", detail=pdf_url)
        pdf_bytes = download_pdf(pdf_url)
        log_stage_success("PDF ダウンロード", detail=f"bytes={len(pdf_bytes)}")

        log_stage_start("PDF 保存", detail=str(config.json_source_gomi))
        save_pdf(config.json_source_gomi, pdf_bytes)
        log_stage_success("PDF 保存", detail=str(config.json_source_gomi))

        log_stage_start("PDF→JSON 変換")
        target_month = current_jst_target_month()
        events = convert_gomi_pdf(pdf_bytes, target_month=target_month)
        log_stage_success("PDF→JSON 変換", detail=f"events={len(events)} month={target_month}")

        log_stage_start("JSON 保存", detail=output_path)
        save_events_file(
            config.ical_jsons_gomi,
            source=gomi_event_source(config.ical_jsons_gomi),
            events=events,
        )
        log_stage_success("JSON 保存", detail=output_path)

    code = run_command(_run)
    if code == 0:
        log_info(f"バッチ完了: fetch_gomi (output={output_path})")
    return code
