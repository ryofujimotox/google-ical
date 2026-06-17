"""config.py の単体テスト。"""

from __future__ import annotations

import pytest

from google_ical.config import (
    SOURCES_DIR,
    SOURCE_GOMI_PDF,
    ICAL_JSONS_DIR,
    ICAL_JSONS_GOMI,
    OAUTH_TOKEN_PATH,
    app_config as config,
    check_auth_config,
    check_fetch_gomi_config,
    check_sync_calendar_config,
)
from google_ical.exceptions import ConfigError

FETCH_GOMI_REQUIRED_ENV_NAMES = (
    "OPENAI_API_KEY",
    "OPENAI_MODEL",
    "GOMI_REGION",
)

SYNC_CALENDAR_REQUIRED_ENV_NAMES = (
    "GOOGLE_CALENDAR_ID",
    "GOOGLE_CLIENT_ID",
    "GOOGLE_CLIENT_SECRET",
)


def clear_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        *FETCH_GOMI_REQUIRED_ENV_NAMES,
        *SYNC_CALENDAR_REQUIRED_ENV_NAMES,
        "GOMI_PDF_URL_OVERRIDE",
    ):
        monkeypatch.delenv(name, raising=False)


def set_fetch_gomi_env(monkeypatch: pytest.MonkeyPatch, **overrides: str) -> None:
    clear_env(monkeypatch)
    values = {
        "OPENAI_API_KEY": "openai-key",
        "OPENAI_MODEL": "gpt-4.1-mini",
        "GOMI_REGION": "東京都〇〇区",
        **overrides,
    }
    for name, value in values.items():
        monkeypatch.setenv(name, value)


def set_sync_calendar_env(monkeypatch: pytest.MonkeyPatch, **overrides: str) -> None:
    clear_env(monkeypatch)
    values = {
        "GOOGLE_CALENDAR_ID": "cal-id",
        "GOOGLE_CLIENT_ID": "client-id",
        "GOOGLE_CLIENT_SECRET": "client-secret",
        **overrides,
    }
    for name, value in values.items():
        monkeypatch.setenv(name, value)


def test_check_auth_config_succeeds_with_google_oauth_only(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    clear_env(monkeypatch)
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "client-id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "client-secret")

    check_auth_config(tmp_path / ".env")

    assert config.google_client_id == "client-id"
    assert config.google_client_secret == "client-secret"
    assert config.oauth_token_path == OAUTH_TOKEN_PATH


def test_check_auth_config_fails_when_google_client_id_missing(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    clear_env(monkeypatch)
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "client-secret")

    with pytest.raises(ConfigError, match="GOOGLE_CLIENT_ID が未設定"):
        check_auth_config(tmp_path / ".env")


@pytest.mark.parametrize("missing_name", FETCH_GOMI_REQUIRED_ENV_NAMES)
def test_check_fetch_gomi_config_fails_when_required_env_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    missing_name: str,
) -> None:
    set_fetch_gomi_env(monkeypatch)
    monkeypatch.delenv(missing_name, raising=False)

    with pytest.raises(ConfigError, match=f"{missing_name} が未設定"):
        check_fetch_gomi_config(tmp_path / ".env")


def test_check_fetch_gomi_config_succeeds_with_all_required_env(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    set_fetch_gomi_env(monkeypatch)

    check_fetch_gomi_config(tmp_path / ".env")

    assert config.openai_api_key == "openai-key"
    assert config.openai_model == "gpt-4.1-mini"
    assert config.gomi_region == "東京都〇〇区"
    assert config.sources_dir == SOURCES_DIR
    assert config.sources_gomi_pdf == SOURCES_DIR / SOURCE_GOMI_PDF
    assert config.ical_jsons_dir == ICAL_JSONS_DIR
    assert config.ical_jsons_gomi == ICAL_JSONS_DIR / ICAL_JSONS_GOMI
    assert config.gomi_pdf_url_override is None


def test_check_fetch_gomi_config_succeeds_with_pdf_url_override_without_region(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    set_fetch_gomi_env(monkeypatch)
    monkeypatch.setenv("GOMI_PDF_URL_OVERRIDE", "https://example.jp/gomi.pdf")
    monkeypatch.delenv("GOMI_REGION", raising=False)

    check_fetch_gomi_config(tmp_path / ".env")

    assert config.gomi_pdf_url_override == "https://example.jp/gomi.pdf"
    assert config.gomi_region is None


def test_check_fetch_gomi_config_reads_optional_gomi_region_with_override(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    set_fetch_gomi_env(monkeypatch)
    monkeypatch.setenv("GOMI_PDF_URL_OVERRIDE", "https://example.jp/gomi.pdf")

    check_fetch_gomi_config(tmp_path / ".env")

    assert config.gomi_region == "東京都〇〇区"


@pytest.mark.parametrize("missing_name", SYNC_CALENDAR_REQUIRED_ENV_NAMES)
def test_check_sync_calendar_config_fails_when_required_env_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    missing_name: str,
) -> None:
    set_sync_calendar_env(monkeypatch)
    monkeypatch.delenv(missing_name, raising=False)

    with pytest.raises(ConfigError, match=f"{missing_name} が未設定"):
        check_sync_calendar_config(tmp_path / ".env")


def test_check_sync_calendar_config_succeeds_without_fetch_gomi_env(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    set_sync_calendar_env(monkeypatch)

    check_sync_calendar_config(tmp_path / ".env")

    assert config.google_calendar_id == "cal-id"
    assert config.google_client_id == "client-id"
    assert config.google_client_secret == "client-secret"
    assert config.ical_jsons_dir == ICAL_JSONS_DIR
    assert config.oauth_token_path == OAUTH_TOKEN_PATH
