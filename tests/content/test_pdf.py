"""content/pdf.py の単体テスト。"""

from __future__ import annotations

import pytest

from google_ical.content.pdf import download_pdf
from google_ical.exceptions import PdfDownloadError


def test_download_pdf_rejects_html_response_even_for_pdf_url(monkeypatch: pytest.MonkeyPatch) -> None:
    class _FakeResponse:
        status_code = 200
        content = b"<html>error</html>"

        @staticmethod
        def raise_for_status() -> None:
            return None

        @property
        def headers(self) -> dict[str, str]:
            return {"content-type": "text/html; charset=utf-8"}

    monkeypatch.setattr("google_ical.content.pdf.httpx.get", lambda *args, **kwargs: _FakeResponse())

    with pytest.raises(PdfDownloadError, match="PDF ではない応答"):
        download_pdf("https://example.jp/gomi.pdf")


def test_download_pdf_accepts_application_pdf(monkeypatch: pytest.MonkeyPatch) -> None:
    class _FakeResponse:
        status_code = 200
        content = b"%PDF-1.4"

        @staticmethod
        def raise_for_status() -> None:
            return None

        @property
        def headers(self) -> dict[str, str]:
            return {"content-type": "application/pdf"}

    monkeypatch.setattr("google_ical.content.pdf.httpx.get", lambda *args, **kwargs: _FakeResponse())

    assert download_pdf("https://example.jp/download?id=123") == b"%PDF-1.4"
