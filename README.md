# ゴミ収集日収集ツール





## 目的

JSON とゴミ収集日 PDF から Google カレンダーを更新するバッチ。



## 概要

1. ChatGPT による **ゴミ収集日 PDF** の URL 調査
2. URL から **ゴミ収集日 PDF** をダウンロード
3. ChatGPT により **ゴミ収集日 PDF** を **iCalJSON** （iCal取込用JSON）に変換
4. **iCalJSON** を保存
5. 全 **iCalJSON** を Google カレンダーへ反映

```mermaid
flowchart LR
  cron["cron"] --> batch

  subgraph batch["google-ical"]
    direction LR
    fetchGomi["fetch_gomi"] --> icalJsons["iCalJSON"]
    icalJsons --> syncCal["sync_calendar"]
    env[".env"] --> fetchGomi
    env --> syncCal
    syncCal --> gcal["Google カレンダー"]
  end

  gcal --> publicIcal["公開 iCal URL"]
  publicIcal --> quote0["電子ペーパー（quote0）"]
```

*カレンダーに登録したゴミ収集日を [電子ペーパー（quote0）](https://github.com/ryofujimotox/quote0) に表示すると便利。*



## 最低限の動作確認手順

- 詳細な手順は [docs/deploy.md](./docs/deploy.md) を参照
- Python **3.12** （[.python-version](./.python-version)）


### 1. 環境構築

```bash
git clone https://github.com/ryofujimotox/google-ical && cd google-ical
python -m pip install -r requirements.txt
cp -n .env.example .env
```

- `.env` を編集する。[AGENTS.md](./AGENTS.md) どおり。


### 2. Google 認証（初回のみ）

```bash
python -m google_ical.commands.auth
```


### 3. 手動実行

```bash
python -m google_ical.commands.fetch_gomi
python -m google_ical.commands.sync_calendar
```



## 技術スタック

- Python 3.12（[.python-version](./.python-version)）
- iCalJSON（手動定義・ゴミ収集日由来）
- Google Calendar API（書き込み）
- OpenAI API（ゴミ収集日 PDF 調査・JSON 化）
- pytest（単体テスト）



## 設計の要点

- **fetch_gomi → sync_calendar** の順で実行（月 1 回 cron）
- iCalJSON は **`ical_jsons/` 内の全 `*.json`** を合成して反映
- 内部 ID は **SHA-256**（ファイル名 + 予定内容）で冪等に作成・更新・削除
- 詳細な同期ルールは [AGENTS.md](./AGENTS.md) の「Google カレンダー連携」を参照



## フォルダ構成

```
AGENTS.md                  # 要件・振る舞い（仕様の正本）

docs/
  deploy.md                # Linux 配置・cron
  git.md                   # Git 運用
  issue-parallel-plan.md   # Issue 並行解決プラン（テンプレート）

google_ical/
  config.py                # コマンド別 check_*_config、固定値定数、app_config
  exceptions.py            # 共通例外
  cli.py                   # コマンド共通の終了処理
  pipeline_log.py          # 段階ログ
  commands/                # 実行可能コマンド（auth / fetch_gomi / sync_calendar）
  content/
    events/                # iCalJSON（models / schemas / loader / writer）
    gomi/                  # ゴミ収集日（normalize / pipeline）
    google/                # Google 連携（calendar / auth / sync）
      calendar.py          # Calendar API 薄いアダプタ
      auth.py              # OAuth トークン
      sync.py              # Google カレンダー同期
    openai_client.py       # ChatGPT（URL 調査・PDF→JSON）
    pdf.py                 # PDF HTTP 取得

config/
  json_sources/            # JSON 変換用ソース（fetch_gomi が保存する PDF 等）
  ical_jsons/              # iCalJSON テンプレート（gomi.json / sample.json）

tests/                     # 単体テスト（google_ical/ と同じ階層）
  content/

.env.example               # 環境変数名テンプレ

LICENSE                    # 本体（MIT）
```
