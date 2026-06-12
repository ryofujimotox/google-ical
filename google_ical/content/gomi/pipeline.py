"""fetch_gomi の各段処理。"""

from __future__ import annotations

from collections.abc import Callable

from google_ical.config import AppConfig
from google_ical.content.events.models import CalendarEvent
from google_ical.content.gomi.config import GomiConfig
from google_ical.content.openai_client import convert_pdf_to_events, investigate_gomi_pdf_url
from google_ical.exceptions import GomiError, OpenAIClientError


def fetch_gomi_pdf_url(config: AppConfig, gomi_config: GomiConfig) -> str:
    """pdf_url_override があればそれを返す。なければ ChatGPT で URL を調査する。"""
    if gomi_config.pdf_url_override:
        return gomi_config.pdf_url_override
    return _call_openai(
        lambda: investigate_gomi_pdf_url(
            region=gomi_config.region,
            api_key=config.openai_api_key,
            model=config.openai_model,
        ),
    )


def convert_gomi_pdf(config: AppConfig, pdf_bytes: bytes) -> tuple[CalendarEvent, ...]:
    return _call_openai(
        lambda: convert_pdf_to_events(
            pdf_bytes=pdf_bytes,
            api_key=config.openai_api_key,
            model=config.openai_model,
        ),
    )


def _call_openai[T](step: Callable[[], T]) -> T:
    try:
        return step()
    except OpenAIClientError as exc:
        raise GomiError(f"ChatGPT 応答解析失敗: {exc}") from exc
