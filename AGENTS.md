# AGENTS.md

直感的に理解できてすぐ実行できるようなコメント・ソースとする。

## 概要

- cron で単発実行するバッチ（時刻・起動コマンドは [docs/deploy.md](docs/deploy.md)）
- **固定予定 JSON** と **ゴミ収集日 PDF** から予定を作り、**Google Calendar API** でカレンダーを更新する
- Google Calendar 上では `extendedProperties.private` に同期IDを入れ、このバッチが作った予定だけを更新・削除する

## 技術・構成の前提

- 言語は Python 3.12。Web フレームワークは使わない
- 本番エントリポイントは `python -m google_ical.commands.sync_calendar`
- `python -m google_ical` は `.env` 読み込み確認のみ
- `.venv` を使い実行する

## 設定（環境変数）

`.env.example` をコピーして `.env` を作る。`.env` は Git に含めない。

| 変数 | 入れる値 |
|------|----------|
| `GOOGLE_SERVICE_ACCOUNT_FILE` | Google サービスアカウント JSON パス |
| `GOOGLE_CALENDAR_ID` | 更新先 Google カレンダー ID |
| `EVENT_JSON_PATHS` | 固定予定 JSON。複数はカンマ区切り |
| `GOMI_PDF_SOURCES` | ゴミ収集 PDF の URL またはパス。複数はカンマ区切り |
| `GOMI_YEAR` | PDF 内の日付へ補う年。空なら今日の年 |
| `SYNC_DAYS` | 今日から何日先まで同期するか |
| `SYNC_NAMESPACE` | 同期IDの名前空間 |

## 振る舞い（必ず守る）

- 入力読込 → ゴミPDF解析 → Google Calendar 既存予定取得 → upsert/delete の順で実行する
- 途中で失敗したら非0で終了し、原因が追える日本語メッセージを stderr に出す
- 同じ入力なら同じ同期IDになるよう、出力は決定的にする
- Google Calendar 上でこのバッチが管理していない予定は触らない
- 常駐プロセスや GUI は前提にしない（cron 等の単発実行）

## JSON 形式

トップレベルは配列、または `{ "events": [...] }`。

```json
{
  "events": [
    {
      "title": "通院",
      "start": "2026-06-20T10:00:00+09:00",
      "end": "2026-06-20T11:00:00+09:00",
      "description": "任意",
      "location": "任意",
      "uid": "stable-id",
      "color_id": "5",
      "reminders": [30]
    },
    { "title": "記念日", "start": "2026-06-21" }
  ]
}
```

- `start` / `end` は ISO8601 の日付または日時
- 終日予定の `end` は Google Calendar 仕様に合わせて排他的日付。省略時は翌日
- `uid` があれば同期IDの材料に使う。無ければ source/title/start/end から作る

## テスト

- テストランナーは `pytest`
- テストは責務単位で分ける（設定、JSON 読込、Google リソース変換、ゴミPDFテキスト解析）
- Google Calendar 送信は単体テスト対象外。API 呼び出し前のリソース変換までをテストする

## コメントの書き方

- 日本語で短く、意図がすぐ分かるようにする
- 仕様の羅列は本書や docs に置き、ソース内コメントに重複させない
- 依存追加・運用変更は README/docs に影響を短く説明する
