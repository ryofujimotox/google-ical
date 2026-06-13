# デプロイ

## 前提

| 項目 | 内容 |
|------|------|
| OS | Linux |
| 配置 | `/home/scripts/google-ical/` |
| 実行 | 毎日 0:05 JST に cron で `.venv/bin/python -m google_ical.commands.sync_calendar` |
| 秘密情報 | `.env` とサービスアカウント JSON |
| Python | 3.12（`.python-version`） |

## セットアップ

```bash
git clone https://github.com/ryofujimotox/google-ical /home/scripts/google-ical
cd /home/scripts/google-ical
python3.12 -m venv .venv
.venv/bin/python --version
.venv/bin/pip install -U pip
.venv/bin/pip install -r requirements.txt
```

## 環境変数

```bash
cd /home/scripts/google-ical
cp -n .env.example .env
chmod 600 .env
```

`AGENTS.md` の「設定（環境変数）」どおり `.env` を設定する。

## Google Calendar 側の準備

1. Google Cloud で Calendar API を有効化する
2. サービスアカウントを作成して JSON キーを保存する
3. 更新先カレンダーをサービスアカウントのメールアドレスへ共有し、「予定の変更権限」を付ける
4. JSON キーのパスを `GOOGLE_SERVICE_ACCOUNT_FILE` に設定する

## 動作確認

```bash
cd /home/scripts/google-ical
.venv/bin/python -m google_ical
.venv/bin/python -m google_ical.commands.sync_calendar --dry-run
.venv/bin/python -m google_ical.commands.sync_calendar
```

## cron 登録

```bash
sudo mkdir -p /var/log/google-ical
sudo chown "$(whoami)" /var/log/google-ical
crontab -e
```

```cron
5 0 * * * cd /home/scripts/google-ical && .venv/bin/python -m google_ical.commands.sync_calendar >>/var/log/google-ical/sync_calendar.log 2>&1
```

失敗時は `/var/log/google-ical/sync_calendar.log` の末尾に出る日本語メッセージを確認する。

## 更新

```bash
cd /home/scripts/google-ical
git pull
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m google_ical.commands.sync_calendar --dry-run
```
