# MCOC Japanese Champion Data Tools

Marvel Contest of Champions のチャンピオンデータを収集・抽出し、日本語の検索可能なHTMLページを生成するローカルツール群です。

## 主なファイル

- `generate_jp_page.py` - ゲーム内抽出データとローカライズJSONから公開用の `index.html` を生成します。
- `extract_abilities.py` - 最新のゲームBCG `.bin` からチャンピオン別アビリティJSONを抽出します。
- `NOTES.md` - 調査経緯、データソース、生成方針の作業ノートです。

## セットアップ

現行のHTML生成スクリプトは標準ライブラリのみで動きます。仮想環境を使う場合は次の通りです。

```powershell
python -m venv venv
.\venv\Scripts\pip install -r requirements.txt
```

## HTML生成

```powershell
python -B extract_abilities.py
python -B generate_jp_page.py
```

出力先:

```text
index.html
```

本番サーバーでは次のエックスサーバー公開ディレクトリに配置します。

```text
/marvel-allstar-battle.tokyo/public_html
```

アップロード対象:

```text
index.html
privacy.html
disclaimer.html
robots.txt
sitemap.xml
data/portraits/
```

## 収益化の準備

AdSense 申請前に、公開サイトへ `privacy.html`、`disclaimer.html`、`robots.txt`、`sitemap.xml` を配置します。

AdSense 承認後、Google から発行される `pub-xxxxxxxxxxxxxxxx` を使って、ルート直下に `ads.txt` を追加してください。例:

```text
google.com, pub-xxxxxxxxxxxxxxxx, DIRECT, f08c47fec0942fa0
```

`pub-...` が未確定の段階では、誤った `ads.txt` を公開しないでください。

## GitHub Actions デプロイ

`main` ブランチにpushすると、`.github/workflows/deploy-xserver.yml` がエックスサーバーへ `index.html` と `data/portraits/` をアップロードします。

GitHub の `Settings` → `Secrets and variables` → `Actions` に次を登録してください。

```text
XSERVER_HOST         SSHホスト名
XSERVER_USER         SSHユーザー名
XSERVER_PORT         SSHポート。未設定なら10022
XSERVER_SSH_KEY      SSH秘密鍵
XSERVER_DEPLOY_PATH  /home/サーバーID/marvel-allstar-battle.tokyo/public_html
```

`XSERVER_DEPLOY_PATH` は誤配信防止のため、`marvel-allstar-battle.tokyo/public_html` を含むパスだけ許可しています。

## 注意

このリポジトリはローカルのゲームキャッシュから作成した抽出データを参照します。生のゲームクライアント資産、暗号化キャッシュ、巨大な中間ダンプ、ローカル抽出用JSONは `.gitignore` で除外しています。

公開に必要な `index.html` と `data/portraits/` は、GitHub Actions デプロイ用の成果物としてリポジトリに含めます。
