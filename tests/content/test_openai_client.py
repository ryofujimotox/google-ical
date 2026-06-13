"""content/openai_client.py の応答抽出・URL検証テスト。"""

from __future__ import annotations

import pytest

from google_ical.content.openai_client import _extract_output_text, _is_valid_pdf_url_only
from google_ical.exceptions import OpenAIClientError


def test_is_valid_pdf_url_only_accepts_pdf_url() -> None:
    assert _is_valid_pdf_url_only("https://example.jp/calendar/gomi.pdf") is True
    assert _is_valid_pdf_url_only("http://example.jp/calendar/gomi.pdf") is True


def test_is_valid_pdf_url_only_accepts_download_endpoint_without_pdf_suffix() -> None:
    assert _is_valid_pdf_url_only("https://example.jp/download?id=123") is True


def test_is_valid_pdf_url_only_rejects_landing_page_without_pdf() -> None:
    assert _is_valid_pdf_url_only("https://city.example.jp/garbage-calendar") is False


def test_is_valid_pdf_url_only_rejects_extra_text() -> None:
    assert _is_valid_pdf_url_only("URL: https://example.jp/calendar/gomi.pdf") is False


def test_extract_output_text_reads_dict_shaped_response() -> None:
    response = {
        "output": [
            {
                "content": [
                    {"text": "https://example.jp/gomi.pdf"},
                ],
            },
        ],
    }

    assert _extract_output_text(response) == "https://example.jp/gomi.pdf"


def test_extract_output_text_reads_output_text_field() -> None:
    response = {"output_text": "https://example.jp/gomi.pdf"}

    assert _extract_output_text(response) == "https://example.jp/gomi.pdf"


def test_extract_output_text_fails_when_no_text() -> None:
    with pytest.raises(OpenAIClientError, match="テキストがありません"):
        _extract_output_text({"output": []})
