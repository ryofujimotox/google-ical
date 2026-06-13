"""content/openai_client.py の応答抽出・URL検証テスト。"""

from __future__ import annotations

import pytest

from google_ical.constants import DEFAULT_OPENAI_MODEL
from google_ical.content.openai_client import (
    _create_openai_client,
    _extract_output_text,
    _is_valid_pdf_url_only,
    investigate_gomi_pdf_url,
)
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


def test_create_openai_client_disables_sdk_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class FakeOpenAI:
        def __init__(self, **kwargs: object) -> None:
            captured.update(kwargs)

    monkeypatch.setattr("openai.OpenAI", FakeOpenAI)

    _create_openai_client("test-key")

    assert captured == {"api_key": "test-key", "max_retries": 0}


def test_investigate_gomi_pdf_url_uses_client_without_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    captured_client: dict[str, object] = {}
    captured_create: dict[str, object] = {}

    class FakeOpenAI:
        def __init__(self, **kwargs: object) -> None:
            captured_client.update(kwargs)

        class responses:
            @staticmethod
            def create(**kwargs: object) -> dict[str, str]:
                captured_create.update(kwargs)
                return {"output_text": "https://example.jp/gomi.pdf"}

    monkeypatch.setattr("openai.OpenAI", FakeOpenAI)

    url = investigate_gomi_pdf_url(region="東京都〇〇区", api_key="test-key", model=DEFAULT_OPENAI_MODEL)

    assert url == "https://example.jp/gomi.pdf"
    assert captured_client["max_retries"] == 0
    assert captured_create["tool_choice"] == "required"
    assert captured_create["tools"] == [{"type": "web_search"}]
