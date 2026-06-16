"""PDF の HTTP 取得と保存。"""

from __future__ import annotations

import os
from pathlib import Path

import httpx

from google_ical.exceptions import PdfDownloadError


def download_pdf(url: str, *, timeout: float = 60.0) -> bytes:
    """URL から PDF バイト列を HTTP 取得する。
    Content-Type が pdf でない応答は拒否する。
    例: "https://example.jp/gomi.pdf" → b"%PDF-1.4..."
    """
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


def save_pdf(path: Path, content: bytes) -> None:
    """PDF バイト列を JSON 変換用ソースとして原子的にディスクへ書き出す。
    例: Path("config/json_sources/gomi.pdf"), b"%PDF..." → ファイル作成
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.tmp")
    try:
        with tmp_path.open("wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()
