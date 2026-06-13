"""ゴミ収集日PDFから終日予定を作るパイプライン。"""

from __future__ import annotations

import re
import tempfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

from google_ical.content.events.models import CalendarEvent, sort_events

MONTH_DAY_RE = re.compile(r"(?<![\d/-])(?P<month>\d{1,2})\s*[月/]\s*(?P<day>\d{1,2})\s*日?")
ISO_DATE_RE = re.compile(r"(?P<year>20\d{2})[-/](?P<month>\d{1,2})[-/](?P<day>\d{1,2})")


@dataclass(frozen=True)
class GomiRule:
    """PDFテキスト上のキーワードとカレンダー表示名。"""

    keyword: str
    title: str


DEFAULT_RULES: tuple[GomiRule, ...] = (
    GomiRule("可燃", "可燃ごみ"),
    GomiRule("燃やす", "可燃ごみ"),
    GomiRule("不燃", "不燃ごみ"),
    GomiRule("燃やさない", "不燃ごみ"),
    GomiRule("資源", "資源ごみ"),
    GomiRule("プラ", "プラスチック"),
    GomiRule("ペット", "ペットボトル"),
    GomiRule("びん", "びん"),
    GomiRule("ビン", "びん"),
    GomiRule("缶", "缶"),
    GomiRule("古紙", "古紙"),
    GomiRule("粗大", "粗大ごみ"),
)


def events_from_sources(
    sources: tuple[str, ...], *, year: int, rules: tuple[GomiRule, ...] = DEFAULT_RULES
) -> list[CalendarEvent]:
    """URL/ローカルPDFを全件解析してゴミ収集予定を返す。"""

    events: list[CalendarEvent] = []
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        for index, source in enumerate(sources):
            pdf_path = fetch_pdf(source, temp_path / f"gomi-{index}.pdf")
            events.extend(events_from_pdf(pdf_path, year=year, source=source, rules=rules))
    return sort_events(dedupe_events(events))


def fetch_pdf(source: str, destination: Path) -> Path:
    """URLなら取得し、パスならそのまま返す。"""

    parsed = urlparse(source)
    if parsed.scheme in {"http", "https"}:
        from urllib.request import urlopen

        with urlopen(source, timeout=30) as response:  # noqa: S310 - 運用者が.envで指定したURLを取得する
            content_type = response.headers.get("content-type", "")
            if "pdf" not in content_type.lower() and not source.lower().endswith(".pdf"):
                raise ValueError(f"PDFではないレスポンスです: url={source} content_type={content_type}")
            destination.write_bytes(response.read())
        return destination

    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(f"ゴミPDFが見つかりません: {source}")
    return path


def events_from_pdf(
    path: Path, *, year: int, source: str | None = None, rules: tuple[GomiRule, ...] = DEFAULT_RULES
) -> list[CalendarEvent]:
    """PDFの抽出テキストから日付と分別名を拾う。"""

    try:
        from pypdf import PdfReader
    except ModuleNotFoundError as exc:
        raise RuntimeError("PDF解析には pypdf のインストールが必要です") from exc

    reader = PdfReader(str(path))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    return events_from_text(text, year=year, source=source or str(path), rules=rules)


def events_from_text(
    text: str, *, year: int, source: str, rules: tuple[GomiRule, ...] = DEFAULT_RULES
) -> list[CalendarEvent]:
    """自治体PDFでよくある「日付 + 分別名」の行を予定に変換する。"""

    events: list[CalendarEvent] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        titles = tuple(dict.fromkeys(rule.title for rule in rules if rule.keyword in line))
        if not titles:
            continue
        for collected_on in _dates_in_line(line, default_year=year):
            for title in titles:
                uid = f"gomi:{collected_on.isoformat()}:{title}:{line_number}"
                events.append(
                    CalendarEvent(
                        source=source,
                        title=title,
                        start=collected_on,
                        description=f"ゴミ収集日PDFから生成: {line.strip()}",
                        uid=uid,
                    )
                )
    return sort_events(dedupe_events(events))


def dedupe_events(events: Iterable[CalendarEvent]) -> list[CalendarEvent]:
    seen: set[tuple[str, str, date]] = set()
    deduped: list[CalendarEvent] = []
    for event in events:
        if not isinstance(event.start, date):
            deduped.append(event)
            continue
        key = (event.source, event.title, event.start)
        if key not in seen:
            seen.add(key)
            deduped.append(event)
    return deduped


def _dates_in_line(line: str, *, default_year: int) -> list[date]:
    dates: list[date] = []
    for match in ISO_DATE_RE.finditer(line):
        dates.append(date(int(match.group("year")), int(match.group("month")), int(match.group("day"))))
    for match in MONTH_DAY_RE.finditer(line):
        candidate = date(default_year, int(match.group("month")), int(match.group("day")))
        if candidate not in dates:
            dates.append(candidate)
    return dates
