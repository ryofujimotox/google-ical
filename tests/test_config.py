"""config.py の単体テスト。"""

from __future__ import annotations

import pytest

from google_ical.config import load_auth_config, load_config
from google_ical.exceptions import ConfigError


REQUIRED_ENV_NAMES = (
    "OPENAI_API_KEY",
    "GOOGLE_CALENDAR_ID",
    "GOOGLE_CLIENT_ID",
    "GOOGLE_CLIENT_SECRET",
)


def clear_required_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in REQUIRED_ENV_NAMES:
        monkeypatch.delenv(name, raising=False)


def test_load_auth_config_succeeds_with_google_oauth_only(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    clear_required_env(monkeypatch)
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "client-id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "client-secret")

    config = load_auth_config(tmp_path / ".env")

    assert config.google_client_id == "client-id"
    assert config.google_client_secret == "client-secret"


def test_load_auth_config_fails_when_google_client_id_missing(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    clear_required_env(monkeypatch)
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "client-secret")

    with pytest.raises(ConfigError, match="GOOGLE_CLIENT_ID が未設定"):
        load_auth_config(tmp_path / ".env")


def test_load_config_fails_when_openai_api_key_missing(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    clear_required_env(monkeypatch)
    monkeypatch.setenv("GOOGLE_CALENDAR_ID", "cal-id")
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "client-id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "client-secret")

    with pytest.raises(ConfigError, match="OPENAI_API_KEY が未設定"):
        load_config(tmp_path / ".env")


def test_load_config_fails_when_google_calendar_id_missing(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    clear_required_env(monkeypatch)
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "client-id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "client-secret")

    with pytest.raises(ConfigError, match="GOOGLE_CALENDAR_ID が未設定"):
        load_config(tmp_path / ".env")


def test_load_config_fails_when_google_client_id_missing(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    clear_required_env(monkeypatch)
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    monkeypatch.setenv("GOOGLE_CALENDAR_ID", "cal-id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "client-secret")

    with pytest.raises(ConfigError, match="GOOGLE_CLIENT_ID が未設定"):
        load_config(tmp_path / ".env")


def test_load_config_fails_when_google_client_secret_missing(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    clear_required_env(monkeypatch)
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    monkeypatch.setenv("GOOGLE_CALENDAR_ID", "cal-id")
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "client-id")

    with pytest.raises(ConfigError, match="GOOGLE_CLIENT_SECRET が未設定"):
        load_config(tmp_path / ".env")


def test_load_config_uses_defaults_for_optional_paths(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    clear_required_env(monkeypatch)
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    monkeypatch.setenv("GOOGLE_CALENDAR_ID", "cal-id")
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "client-id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "client-secret")

    config = load_config(tmp_path / ".env")

    assert str(config.events_json_dir) == "config/events"
    assert str(config.gomi_config_path) == "config/gomi_config.json"
    assert config.openai_model == "gpt-4o-mini"
    assert config.debug is False


@pytest.mark.parametrize("value", ("1", "true", "TRUE", "yes", "on"))
def test_load_config_enables_debug_from_env_flag(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    value: str,
) -> None:
    clear_required_env(monkeypatch)
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    monkeypatch.setenv("GOOGLE_CALENDAR_ID", "cal-id")
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "client-id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "client-secret")
    monkeypatch.setenv("GOOGLE_ICAL_DEBUG", value)

    config = load_config(tmp_path / ".env")

    assert config.debug is True
