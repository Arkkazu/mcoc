# MCOC Japanese Champion Data Tools

Marvel Contest of Champions のチャンピオンデータを収集・抽出し、日本語の検索可能なHTMLページを生成するローカルツール群です。

## 主なファイル

- `generate_jp_page.py` - ゲーム内抽出データとローカライズJSONから `data/champions_jp.html` を生成します。
- `extract_abilities.py` - BCG `.bin` からチャンピオン別アビリティJSONを抽出します。
- `find_spotlights.py` - 公式Champion Spotlight記事URLを収集します。
- `build_champion_database.py` - Spotlight記事をクロールしてJSON/SQLite形式の参照DBを作ります。
- `mcoc_news_fetcher.py` - 公式ニュース一覧から新着記事を確認します。
- `NOTES.md` - 調査経緯、データソース、生成方針の作業ノートです。

## セットアップ

```powershell
python -m venv venv
.\venv\Scripts\pip install -r requirements.txt
```

## HTML生成

```powershell
.\venv\Scripts\python generate_jp_page.py
```

出力先:

```text
data/champions_jp.html
```

## 注意

このリポジトリはローカルのゲームキャッシュやUnity AssetBundleを参照する調査コードを含みます。生のゲームクライアント資産、暗号化キャッシュ、抽出画像、巨大な中間ダンプ、生成HTMLは `.gitignore` で除外しています。
