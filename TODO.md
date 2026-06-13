# TODO




## 実装

- [x] Google OAuth フロー（`content/google/auth.py` の `run_oauth_flow`）
- [x] ChatGPT ゴミ収集日 PDF URL 調査（`content/openai_client.py`）
- [x] ChatGPT PDF→JSON 変換（`content/openai_client.py`）
- [x] Google カレンダー同期（作成・更新・削除・`extendedProperties`）
- [x] ゴミ収集日 PDF→予定 JSON の正規化テスト（`content/gomi/normalize.py`）
- [ ] 結合テスト（auth / fetch_gomi / sync_calendar の実 API）


## ドキュメント

- [x] AGENTS.md の未決定事項を移す（ChatGPT プロンプトは `openai_client.py` に実装済み）
- [x] GitHub リポジトリ作成・`origin` への初回 push
