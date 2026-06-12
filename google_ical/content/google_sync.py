"""Google カレンダーへの予定同期。

extendedProperties.private に google_ical_id / google_ical_source を保存し、
本リポ管理イベントのみ作成・更新・削除する（AGENTS.md）。
"""

from __future__ import annotations

from google_ical.config import AppConfig
from google_ical.content.events.models import MergedEvent


def sync_events_to_google_calendar(
    config: AppConfig,
    events: tuple[MergedEvent, ...],
) -> None:
    raise NotImplementedError("Google カレンダー同期は未実装です")
