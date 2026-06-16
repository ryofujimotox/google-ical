"""content/gomi/pipeline.py の単体テスト。"""

from __future__ import annotations

from dataclasses import replace

import pytest

from google_ical.config import (
    JSON_SOURCE_DIR,
    JSON_SOURCE_GOMI,
    ICAL_JSONS_DIR,
    ICAL_JSONS_GOMI,
    GOOGLE_TOKEN_PATH,
    AppConfig,
    install_app_config,
)
from google_ical.content.gomi import pipeline


@pytest.fixture
def _fetch_gomi_app_config() -> AppConfig:
    return AppConfig(
        google_client_id="",
        google_client_secret="",
        google_calendar_id="",
        google_token_path=GOOGLE_TOKEN_PATH,
        openai_api_key="test-key",
        openai_model="gpt-4.1-mini",
        gomi_region="東京都〇〇区",
        gomi_pdf_url_override=None,
        json_source_dir=JSON_SOURCE_DIR,
        json_source_gomi=JSON_SOURCE_DIR / JSON_SOURCE_GOMI,
        ical_jsons_dir=ICAL_JSONS_DIR,
        ical_jsons_gomi=ICAL_JSONS_DIR / ICAL_JSONS_GOMI,
    )


def test_fetch_gomi_pdf_url_returns_override_when_set(_fetch_gomi_app_config: AppConfig) -> None:
    install_app_config(
        replace(_fetch_gomi_app_config, gomi_pdf_url_override="https://example.jp/gomi.pdf"),
    )

    assert pipeline.fetch_gomi_pdf_url() == "https://example.jp/gomi.pdf"


def test_fetch_gomi_pdf_url_investigates_region_when_override_unset(
    _fetch_gomi_app_config: AppConfig,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_app_config(_fetch_gomi_app_config)
    calls: list[str] = []

    def fake_investigate(*, region: str, api_key: str, model: str) -> str:
        calls.append(region)
        assert api_key == "test-key"
        assert model == "gpt-4.1-mini"
        return "https://example.jp/investigated.pdf"

    monkeypatch.setattr(pipeline, "investigate_gomi_pdf_url", fake_investigate)

    assert pipeline.fetch_gomi_pdf_url() == "https://example.jp/investigated.pdf"
    assert calls == ["東京都〇〇区"]
