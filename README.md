# ゴミ収集日収集ツール





## 目的

**iCalJSON** で Google カレンダーを更新する。

近所の **ゴミ収集日 PDF** を自動取得して **iCalJSON** にし、反映する機能も含む。

![fetch_gomi: コマンド実行 → PDF 自動取得 → JSON 自動変換](./docs/images/fetch_gomi.png)

![sync_calendar: 事前準備 → コマンド実行 → カレンダーに反映](./docs/images/sync_calendar.png)



## 概要

1. ChatGPT で近所の **ゴミ収集日 PDF** をダウンロード
2. ChatGPT で **ゴミ収集日 PDF** を **iCalJSON**（iCal取込用JSON）に変換
3. 全 **iCalJSON** を Google カレンダーへ反映

```mermaid
flowchart LR
  cron["cron"] --> gomiPdf
  cron --> gcal

  subgraph fetch_gomi["fetch_gomi"]
    direction LR
    gomiPdf["ゴミ収集日PDFを取得"]
    gomiPdf --> icalJsons["iCalJSONに変換"]
  end

  subgraph sync_calendar["sync_calendar"]
    gcal["Googleカレンダーに反映"]
  end

  icalJsons --> gcal

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
- iCalJSON は **`data/ical_jsons/` 内の全 `*.json`** を合成して反映
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

data/
  sources/                 # 変換元ソース（fetch_gomi が保存する PDF 等）
  ical_jsons/              # iCalJSON テンプレート（gomi.json / sample.json）
  auth/
    token.json             # OAuth トークン（Git に含めない）

tests/                     # 単体テスト（google_ical/ と同じ階層）
  content/

.env.example               # 環境変数名テンプレ

LICENSE                    # 本体（MIT）
```
