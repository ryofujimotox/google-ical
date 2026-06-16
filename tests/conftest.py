"""テスト共通フィクスチャ。"""

from __future__ import annotations

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


@pytest.fixture
def app_config() -> AppConfig:
    return AppConfig(
        google_client_id="client-id",
        google_client_secret="client-secret",
        google_calendar_id="cal-id",
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


@pytest.fixture(autouse=True)
def _install_app_config(app_config: AppConfig) -> None:
    install_app_config(app_config)
