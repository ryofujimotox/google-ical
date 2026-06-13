"""ゴミ収集日設定 JSON の読込。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

from google_ical.constants import DEFAULT_GOMI_OUTPUT
from google_ical.exceptions import GomiError


class _GomiSectionSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    region: str
    output_file: str = DEFAULT_GOMI_OUTPUT
    pdf_url_override: str | None = None

    @field_validator("region")
    @classmethod
    def validate_region_not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("region は空文字列にできません")
        return stripped

    @field_validator("pdf_url_override")
    @classmethod
    def validate_pdf_url_override_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("pdf_url_override は空文字列にできません")
        return stripped


class _GomiConfigSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    gomi: _GomiSectionSchema


@dataclass(frozen=True)
class GomiConfig:
    """fetch_gomi が使うゴミ収集日設定。"""

    region: str
    output_file: str
    pdf_url_override: str | None


def resolve_gomi_output_path(events_json_dir: Path, output_file: str) -> Path:
    """EVENTS_JSON_DIR 内の出力パスを解決する。ディレクトリ外への脱出を拒否する。"""
    candidate = Path(output_file)
    if candidate.is_absolute() or candidate.name != output_file or ".." in candidate.parts:
        raise GomiError(
            f"output_file は EVENTS_JSON_DIR 内のファイル名のみ指定できます: {output_file!r}",
        )
    if not output_file.endswith(".json"):
        raise GomiError(
            f"output_file は .json ファイル名を指定してください: {output_file!r}",
        )
    events_root = events_json_dir.resolve()
    resolved = (events_root / candidate).resolve()
    if resolved.parent != events_root:
        raise GomiError(
            f"output_file は EVENTS_JSON_DIR 内のファイル名のみ指定できます: {output_file!r}",
        )
    return resolved


def load_gomi_config(path: Path) -> GomiConfig:
    if not path.is_file():
        raise GomiError(f"ゴミ収集日設定ファイルがありません: {path}")

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        parsed = _GomiConfigSchema.model_validate(raw)
    except json.JSONDecodeError as exc:
        raise GomiError(f"ゴミ収集日設定 JSON の解析に失敗しました: {path}") from exc
    except ValidationError as exc:
        raise GomiError(f"ゴミ収集日設定 JSON の形式が不正です: {path}") from exc

    return GomiConfig(
        region=parsed.gomi.region,
        output_file=parsed.gomi.output_file,
        pdf_url_override=parsed.gomi.pdf_url_override,
    )
