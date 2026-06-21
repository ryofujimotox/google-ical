"""fetch_gomi の各段処理。"""

from __future__ import annotations

from collections.abc import Callable

from google_ical.config import app_config as config
from google_ical.content.events.models import CalendarEvent
from google_ical.content.openai_client import convert_pdf_to_events, investigate_gomi_pdf_url
from google_ical.exceptions import GomiError, OpenAIClientError


def fetch_gomi_pdf_url() -> str:
    """ゴミ収集日 PDF のダウンロード URL を返す。
    GOMI_PDF_URL_OVERRIDE あり: env の URL をそのまま返す。なし: ChatGPT が GOMI_REGION から調査。
    例: "https://www.city.example.jp/gomi.pdf"
    """
    if config.gomi_pdf_url_override:
        return config.gomi_pdf_url_override
    return _call_openai(
        lambda: investigate_gomi_pdf_url(
            region=config.gomi_region,
            api_key=config.openai_api_key,
            model=config.openai_model,
        ),
    )


def convert_gomi_pdf(pdf_bytes: bytes) -> tuple[CalendarEvent, ...]:
    """PDF をゴミ収集日イベント列へ変換する（ChatGPT 経由）。
    例: pdf_bytes → (CalendarEvent("可燃ごみ", ...), ...)
    """
    return _call_openai(
        lambda: convert_pdf_to_events(
            pdf_bytes=pdf_bytes,
            api_key=config.openai_api_key,
            model=config.openai_model,
        ),
    )


def _call_openai[T](step: Callable[[], T]) -> T:
    """ChatGPT 呼び出しを実行し、OpenAIClientError を GomiError に包む。
    例: investigate_gomi_pdf_url(...) → "https://..."
    """
    try:
        return step()
    except OpenAIClientError as exc:
        raise GomiError(f"ChatGPT 応答解析失敗: {exc}") from exc
