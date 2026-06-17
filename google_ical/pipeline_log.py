"""バッチパイプラインの段階ログ（成功=stdout / 失敗=stderr）。"""

from __future__ import annotations

import sys


def log_info(message: str) -> None:
    """通常ログを stdout へ出力する。"""
    print(message, flush=True)


def log_error(message: str) -> None:
    """エラーログを stderr へ出力する。"""
    print(message, file=sys.stderr, flush=True)


def log_stage_start(stage: str, *, detail: str = "") -> None:
    """段階開始ログを出す。
    例: log_stage_start("PDF ダウンロード", detail=url) → "PDF ダウンロード 開始: ..."
    """
    suffix = f": {detail}" if detail else ""
    log_info(f"{stage} 開始{suffix}")


def log_stage_success(stage: str, *, detail: str = "") -> None:
    """段階成功ログを出す。
    例: log_stage_success("JSON 保存", detail="data/ical_jsons/gomi.json") → "JSON 保存 成功: ..."
    """
    suffix = f": {detail}" if detail else ""
    log_info(f"{stage} 成功{suffix}")
