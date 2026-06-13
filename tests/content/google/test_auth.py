"""content/google/auth.py の OAuth フロー選択テスト。"""

from __future__ import annotations

import json
import stat

import pytest

from google_ical.content.google.auth import (
    _console_redirect_uri,
    _run_console_flow,
    save_token_json,
    should_use_console_oauth_flow,
)


def test_should_use_console_oauth_flow_when_env_flag_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SSH_CONNECTION", raising=False)
    monkeypatch.delenv("DISPLAY", raising=False)
    monkeypatch.setenv("GOOGLE_ICAL_OAUTH_CONSOLE", "1")

    assert should_use_console_oauth_flow() is True


def test_should_use_console_oauth_flow_when_env_flag_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SSH_CONNECTION", "127.0.0.1 12345 22")
    monkeypatch.setenv("GOOGLE_ICAL_OAUTH_CONSOLE", "0")

    assert should_use_console_oauth_flow() is False


def test_should_use_console_oauth_flow_on_ssh_connection(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GOOGLE_ICAL_OAUTH_CONSOLE", raising=False)
    monkeypatch.setenv("SSH_CONNECTION", "127.0.0.1 12345 22")

    assert should_use_console_oauth_flow() is True


def test_should_use_console_oauth_flow_on_headless_linux(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GOOGLE_ICAL_OAUTH_CONSOLE", raising=False)
    monkeypatch.delenv("SSH_CONNECTION", raising=False)
    monkeypatch.delenv("DISPLAY", raising=False)
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    monkeypatch.setattr("google_ical.content.google.auth.sys.platform", "linux")

    assert should_use_console_oauth_flow() is True


def test_save_token_json_writes_private_permissions(tmp_path) -> None:
    token_path = tmp_path / "google_token.json"
    token_data = {"token": "secret", "refresh_token": "refresh"}

    save_token_json(token_data, token_path)

    assert token_path.read_text(encoding="utf-8") == json.dumps(token_data, ensure_ascii=False, indent=2) + "\n"
    assert stat.S_IMODE(token_path.stat().st_mode) == 0o600


def test_console_redirect_uri_uses_client_config() -> None:
    flow = type("Flow", (), {"client_config": {"redirect_uris": ["http://localhost"]}})()

    assert _console_redirect_uri(flow) == "http://localhost"


def test_run_console_flow_sets_redirect_uri_before_authorization_url(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeFlow:
        client_config = {"redirect_uris": ["http://localhost"]}
        redirect_uri: str | None = None
        credentials = object()

        def authorization_url(self, **kwargs: object) -> tuple[str, str]:
            assert self.redirect_uri == "http://localhost"
            assert kwargs == {"access_type": "offline", "prompt": "consent"}
            return "https://example.com/auth", "state"

        def fetch_token(self, *, code: str) -> None:
            assert code == "auth-code"

    monkeypatch.setattr("builtins.input", lambda _prompt: "auth-code")
    flow = FakeFlow()

    assert _run_console_flow(flow) is flow.credentials
