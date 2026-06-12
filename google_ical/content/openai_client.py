"""ChatGPT（OpenAI Responses API）呼び出し。"""

from __future__ import annotations

from google_ical.content.events.models import CalendarEvent


def investigate_gomi_pdf_url(*, region: str, api_key: str, model: str) -> str:
    raise NotImplementedError("ゴミ収集日 PDF URL 調査は未実装です")


def convert_pdf_to_events(*, pdf_bytes: bytes, api_key: str, model: str) -> tuple[CalendarEvent, ...]:
    raise NotImplementedError("PDF→JSON 変換は未実装です")
