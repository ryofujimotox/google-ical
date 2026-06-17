"""テスト共通フィクスチャ。"""

from __future__ import annotations

import pytest

from google_ical.config import (
    SOURCES_DIR,
    SOURCE_GOMI_PDF,
    ICAL_JSONS_DIR,
    ICAL_JSONS_GOMI,
    OAUTH_TOKEN_PATH,
    AppConfig,
    install_app_config,
)


@pytest.fixture
def app_config() -> AppConfig:
    return AppConfig(
        google_client_id="client-id",
        google_client_secret="client-secret",
        google_calendar_id="cal-id",
        oauth_token_path=OAUTH_TOKEN_PATH,
        openai_api_key="test-key",
        openai_model="gpt-4.1-mini",
        gomi_region="東京都〇〇区",
        gomi_pdf_url_override=None,
        sources_dir=SOURCES_DIR,
        sources_gomi_pdf=SOURCES_DIR / SOURCE_GOMI_PDF,
        ical_jsons_dir=ICAL_JSONS_DIR,
        ical_jsons_gomi=ICAL_JSONS_DIR / ICAL_JSONS_GOMI,
    )


@pytest.fixture(autouse=True)
def _install_app_config(app_config: AppConfig) -> None:
    install_app_config(app_config)
