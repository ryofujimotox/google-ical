from __future__ import annotations

import os
from pathlib import Path

import pytest

from google_ical.config import ConfigError, load_config


KEYS = {
    "GOOGLE_SERVICE_ACCOUNT_FILE",
    "GOOGLE_CALENDAR_ID",
    "EVENT_JSON_PATHS",
    "GOMI_PDF_SOURCES",
    "GOMI_YEAR",
    "SYNC_DAYS",
    "SYNC_NAMESPACE",
}


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in KEYS:
        monkeypatch.delenv(key, raising=False)


def test_load_config_requires_google_service_account() -> None:
    with pytest.raises(ConfigError, match="GOOGLE_SERVICE_ACCOUNT_FILE"):
        load_config(env_file=None)


def test_load_config_parses_csv_and_ints(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_SERVICE_ACCOUNT_FILE", "/tmp/service.json")
    monkeypatch.setenv("GOOGLE_CALENDAR_ID", "calendar@example.com")
    monkeypatch.setenv("EVENT_JSON_PATHS", "/tmp/a.json, /tmp/b.json")
    monkeypatch.setenv("GOMI_PDF_SOURCES", "https://example.com/a.pdf, /tmp/b.pdf")
    monkeypatch.setenv("GOMI_YEAR", "2026")
    monkeypatch.setenv("SYNC_DAYS", "90")

    config = load_config(env_file=None)

    assert config.google_service_account_file == Path("/tmp/service.json")
    assert config.event_json_paths == (Path("/tmp/a.json"), Path("/tmp/b.json"))
    assert config.gomi_pdf_sources == ("https://example.com/a.pdf", "/tmp/b.pdf")
    assert config.gomi_year == 2026
    assert config.sync_days == 90


def test_load_config_rejects_invalid_sync_days(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_SERVICE_ACCOUNT_FILE", "/tmp/service.json")
    monkeypatch.setenv("GOOGLE_CALENDAR_ID", "calendar@example.com")
    monkeypatch.setenv("EVENT_JSON_PATHS", "/tmp/a.json")
    monkeypatch.setenv("SYNC_DAYS", "0")

    with pytest.raises(ConfigError, match="SYNC_DAYS"):
        load_config(env_file=None)
