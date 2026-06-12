"""プロジェクト共通の例外。"""

from __future__ import annotations


class GoogleIcalError(Exception):
    """本プロジェクトのドメイン例外の基底。"""


class ConfigError(GoogleIcalError, ValueError):
    """設定不備。"""


class EventsError(GoogleIcalError, ValueError):
    """予定 JSON の読込・検証失敗。"""


class GomiError(GoogleIcalError, RuntimeError):
    """ゴミ収集日パイプライン失敗。"""


class PdfDownloadError(GoogleIcalError, RuntimeError):
    """PDF 取得失敗。"""


class OpenAIClientError(GoogleIcalError, RuntimeError):
    """ChatGPT 呼び出しまたは応答解析失敗。"""


class GoogleAuthError(GoogleIcalError, RuntimeError):
    """Google 認証失敗。"""


class CalendarSyncError(GoogleIcalError, RuntimeError):
    """Google カレンダー同期失敗。"""
