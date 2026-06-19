"""ChatGPT（OpenAI Responses API）呼び出し。"""

from __future__ import annotations

import io
import re
from urllib.parse import urlparse

from google_ical.content.events.models import CalendarEvent
from google_ical.content.gomi.normalize import normalize_gomi_events
from google_ical.exceptions import OpenAIClientError

_URL_ONLY_RE = re.compile(r"^https?://[^\s<>'\"{}|\\^`]+$", re.IGNORECASE)

PDF_URL_PROMPT = """\
Region: {region}
Find the latest official garbage-collection calendar PDF (web search required).
Prefer the municipality's official domain. Return the exact PDF URL only—no other text.
"""

PDF_TO_EVENTS_PROMPT = """\
Extract all garbage collection dates from the PDF (all months shown, ~6 months typical).
Return a JSON array only:
[{"summary":"可燃ごみ","start":"2026-06-01T00:00:00","end":"2026-06-02T00:00:00","all_day":true}]
Rules: JST YYYY-MM-DDTHH:MM:SS; all_day with end at next-day 00:00:00; PDF dates only; skip unreadable; [] if none.
"""


def investigate_gomi_pdf_url(*, region: str, api_key: str, model: str) -> str:
    """自治体名からゴミ収集日 PDF の URL を ChatGPT で調査する。
    例: region="東京都〇〇区" → "https://www.city.example.jp/gomi.pdf"
    """
    region = region.strip()
    if not region:
        raise OpenAIClientError("region が空です")

    client = _create_openai_client(api_key)
    try:
        response = client.responses.create(
            model=model,
            tools=[{"type": "web_search"}],
            tool_choice="required",
            input=PDF_URL_PROMPT.format(region=region),
        )
    except Exception as exc:
        raise OpenAIClientError(f"PDF URL 調査の呼び出しに失敗しました region={region}") from exc

    url = _extract_output_text(response).strip()
    if not _is_valid_pdf_url_only(url):
        raise OpenAIClientError(f"PDF URL として不正な応答です: {url!r}")
    return url


def convert_pdf_to_events(
    *,
    pdf_bytes: bytes,
    api_key: str,
    model: str,
) -> tuple[CalendarEvent, ...]:
    """PDF を ChatGPT で読み取り、CalendarEvent 列へ正規化する。
    例: pdf_bytes → (CalendarEvent("可燃ごみ", ...), ...)
    """
    if not pdf_bytes:
        raise OpenAIClientError("PDF が空です")

    client = _create_openai_client(api_key)
    pdf_file = io.BytesIO(pdf_bytes)
    pdf_file.name = "gomi.pdf"

    uploaded_id: str | None = None
    try:
        uploaded = client.files.create(file=pdf_file, purpose="user_data")
        uploaded_id = _uploaded_file_id(uploaded)
        response = client.responses.create(
            model=model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": PDF_TO_EVENTS_PROMPT},
                        {"type": "input_file", "file_id": uploaded_id},
                    ],
                },
            ],
        )
    except Exception as exc:
        raise OpenAIClientError("PDF→JSON 変換の呼び出しに失敗しました") from exc
    finally:
        if uploaded_id:
            _delete_uploaded_file(client, uploaded_id)

    return normalize_gomi_events(_extract_output_text(response))


def _create_openai_client(api_key: str) -> object:
    """OpenAI SDK の自動リトライを無効化してクライアントを作る（AGENTS.md: リトライしない）。"""
    from openai import OpenAI

    return OpenAI(api_key=api_key, max_retries=0)


def _extract_output_text(response: object) -> str:
    """Responses API の返却からテキスト部分だけを取り出す。"""
    output_text = _get_value(response, "output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text

    # SDKの差異に備え、output[].content[].text も見る。
    texts: list[str] = []
    for item in _get_value(response, "output", default=[]) or []:
        for content in _get_value(item, "content", default=[]) or []:
            text = _get_value(content, "text")
            if isinstance(text, str):
                texts.append(text)
    if texts:
        return "".join(texts)

    raise OpenAIClientError("ChatGPT 応答にテキストがありません")


def _is_valid_pdf_url_only(value: str) -> bool:
    """返答が PDF URL 1 文字列だけか検証する。"""
    if not _URL_ONLY_RE.fullmatch(value):
        return False
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False
    path = parsed.path.lower()
    if path.endswith(".pdf"):
        return True
    return _looks_like_pdf_download_url(parsed)


def _looks_like_pdf_download_url(parsed: object) -> bool:
    """CMS のダウンロード URL を許容する（PDF かどうかは取得段で検証）。"""
    path = str(getattr(parsed, "path", "")).lower()
    return any(marker in path for marker in ("/download", "/file", "/dl"))


def _uploaded_file_id(uploaded: object) -> str:
    file_id = _get_value(uploaded, "id")
    if not isinstance(file_id, str) or not file_id:
        raise OpenAIClientError("アップロードしたPDFの file_id を取得できません")
    return file_id


def _delete_uploaded_file(client: object, file_id: str) -> None:
    try:
        client.files.delete(file_id)
    except Exception:
        # 一時ファイルの削除失敗は変換結果を捨てる理由にはしない。
        return


def _get_value(target: object, name: str, default: object | None = None) -> object | None:
    if isinstance(target, dict):
        return target.get(name, default)
    return getattr(target, name, default)
