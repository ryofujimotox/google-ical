# Git 運用




## 🌿 ブランチ方針

| 項目 | 決め方 |
|------|------|
| GitHub Default branch | **`dev`**（[Settings](https://github.com/ryofujimotox/google-ical/settings)） |
| PR 先（base） | **`dev`** |
| `main` | リリース用。日常 PR は向けない。反映は **dev → main** |
| Reviewer | **@codex review** |

- コミットメッセージ：**何の変更か一目で分かること**（下記「コミットメッセージのルール」）
- レビュー依頼（初回）：PR コメントに **@codex review**
- 再レビュー依頼（指摘対応後）：PR コメントに **@codex review** を再度付ける
- Issue 自動クローズ：PR **説明**に `Fixes #N` を書き **dev へマージ**する
- 原則、1 Issue につきブランチ 1 本・PR 1 つ。小さな Issue（例: 文言修正のみ）は複数を 1 PR にまとめてよい
- 複数 Issue を並行で進めるとき: [issue-parallel-plan.md](issue-parallel-plan.md) のテンプレートを `plan.md` にコピーして整理する



### プレフィックスの使い分け

| プレフィックス | 用途 |
|----------------|------|
| `docs/` | 仕様・手順・README など |
| `feature/` | バッチ実装・機能追加・テストなどコード変更全般 |
| `fix/` | バグ修正 |
| `refactor/` | 依存・設定・構成整理（バッチの成果物・振る舞いは変えない） |

**ブランチ名のプレフィックス**（`docs/` 等）と**コミットの Type**（`Docs` / `Chore` 等）は別。


## 😀 コミットメッセージのルール

形式（すべてこの形）:

```text
{emoji} {Type}: {日本語の要約}
```

- 要約内の**英字・数字と日本語の間に半角スペースを入れない**（例: `Python実行の土台`。`Python 実行` のように挟まない）

| Type | emoji | 用途（例） |
|------|-------|------------|
| Docs | 📚 | `📚 Docs: デプロイ手順を追加` |
| Chore | 🔧 | `🔧 Chore: Python実行の土台を追加` |
| Feat | ✨ | `✨ Feat: 予定JSON読込を追加` |
| Fix | 🐛 | `🐛 Fix: 内部ID生成の不具合` |
| Update | 🎨 | `🎨 Update: ゴミ収集日JSONの書き出し形式を調整` |
| Refactor | ♻️ | `♻️ Refactor: Google同期をモジュール分割` |
| Perf | 🐎 | `🐎 Perf: PDF取得を並列化` |
| Test | 🚨 | `🚨 Test: 予定JSON合成を追加` |
| Chore | 🗑️ | `🗑️ Chore: 未使用の設定キーを削除` |
| Chore | 💩 | `💩 Chore: 旧環境変数を非推奨化` |
| Chore | 🔖 | `🔖 Chore: v0.1.0 をタグ付け` |
| Wip | 🚧 | `🚧 Wip: Google同期は未接続` |
| — | 🎉 | `🎉 Initial commit`（`main` の初回のみ。Type 省略） |

**この表以外の絵文字は使わない。**


### レビュー指摘対応のコミット

PR レビュー（Codex 含む）への対応コミットは、**件名に PR 番号**、**本文にリンク付きの詳細**を書く。

- 件名: `{emoji} {Type}: {要約}（PR #N）`
- 本文: どの指摘への対応かを、レビュー・コメントへの **完全 URL** とともに書く
- review ID（例: `4490815424`）は PR 番号ではない。`#4490815424` のような省略リンクは使わない
- リンク形式: `https://github.com/{owner}/{repo}/pull/N#pullrequestreview-{id}` または `#discussion_r{id}`

例:

```text
🐛 Fix: PDF URL検証でランディングページURLを拒否（PR #3）

P2「Enforce the .pdf path requirement」対応。
/garbage-calendar 等の非PDFランディングページURLを段1で拒否する。

- レビュー: https://github.com/ryofujimotox/google-ical/pull/3#pullrequestreview-4490815424
- コメント: https://github.com/ryofujimotox/google-ical/pull/3#discussion_r3407350727
```


