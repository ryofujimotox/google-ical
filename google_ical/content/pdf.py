"""PDF の HTTP 取得。"""

from __future__ import annotations

import httpx

from google_ical.exceptions import PdfDownloadError


def download_pdf(url: str, *, timeout: float = 60.0) -> bytes:
    try:
        response = httpx.get(url, timeout=timeout, follow_redirects=True)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        status = exc.response.status_code if isinstance(exc, httpx.HTTPStatusError) else "?"
        raise PdfDownloadError(f"PDF 取得失敗 url={url} status={status}") from exc

    content_type = response.headers.get("content-type", "")
    if "pdf" not in content_type.lower():
        raise PdfDownloadError(f"PDF 取得失敗 url={url} status={response.status_code}（PDF ではない応答）")

    return response.content
