# MCoC 日本語チャンピオンページ — 作業ノート

---

## プロジェクト概要

Marvel Contest of Champions (MCoC) のチャンピオンデータを整理し、日本語解説HTMLページを自動生成するツール。

### 成果物

| ファイル | 説明 |
|---|---|
| `data/champions_jp.html` | ゲーム内抽出データのみで生成する日本語チャンピオン解説ページ（238件、約1.7MB） |
| `generate_jp_page.py` | HTMLページ生成スクリプト。日本語本文は `words_main.json` とゲームキャッシュ `words\out\v1\*.json` から読む |
| `extract_abilities.py` | AppData .bin からアビリティデータを抽出するスクリプト |
| `data/abilities_all.json` | 全チャンピオン統合アビリティデータ |
| `data/abilities/<prefix>.json` | チャンピオン別アビリティデータ（475ファイル） |
| `data/slug_to_prefix.json` | CSVスラッグ → バイナリプレフィックスマッピング |

### 削除済みの旧調査スクリプト/成果物

現行のHTML生成に不要なため、Spotlight/ニュース収集、メモリダンプ、AESキー探索のスクリプトと旧生成物は削除済み。

- `build_champion_database.py`
- `find_spotlights.py`
- `mcoc_news_fetcher.py`
- `dump_category.py`
- `dump_memory.py`
- `find_aes_key.py`
- `find_aes_key2.py`
- `extract_all.ps1`
- `extract_champions.ps1`
- `extract_values.ps1`
- `extract_champion_full.ps1`
- `data/champion_database.json`
- `data/champion_database.sqlite`
- `data/champions.json`
- `data/champions.csv`
- `data/localization_binary.json`
- `data/memory_strings.json`
- `data/news_cache.json`
- `data/slug_to_bio_jp.json`
- `data/slug_to_portrait.json`
- `data/translations_cache.json`

### 実行方法

```bash
python3 extract_abilities.py    # AppData .bin を解析してアビリティJSON生成
python3 generate_jp_page.py     # 日本語HTMLを生成
```

ブラウザで開く: `C:\python\mcoc\data\champions_jp.html`

### 更新履歴

#### 2026-06-13

- 最新BCG `AB9A00DA06B336BCE87DC509A0308313FE1C0F31.bin` からアビリティを再抽出。
- `data/abilities_all.json` は479プレフィックス、`data/abilities/` は479ファイルに更新。
- `words_main.json` を最新の `words/out/v1` 主JSONへ更新。
- 新規候補 `phyla` を確認し、`Phyla-Vell` / `フィラ＝ヴェル` として `data/game_roster_extra_champions.json` に補完。
- `data/portraits/portrait_phylavell.png` をゲーム本体 `ui_portraits_57.0` から追加。
- `data/champions_jp.html` は239件のチャンピオン一覧として再生成。

---

## ゲームデータ抽出（AppData .bin）

### ファイル

```
C:\Users\tane1\AppData\LocalLow\Kabam\Champions\bcg\out\v1\
  └── B64FC6A6D6243DB2A88B295572F5B5F145A66393.bin  （30MB protobuf）
```

### バイナリの内容

**含まれるもの:**
- チャンピオン名ローカライズ（field 9 = 日本語）→ `data/champion_names_jp.json`, `data/slug_to_jp.json`
- AWノード/サガ能力名: `saga_dodge`→回避, `saga_scythe`→明晰, `saga_xmagica`→X-マジック 等
- チャンピオンクラス/タグ名: コスミック, ミュータント, ヒーロー 等
- 戦闘スタイル: 攻撃型：バースト, 防御型：タンク 等

**含まれないもの:**
- 一般バフ/デバフ表示名（regen→再生, stun→スタン 等）

バフ表示名・能力説明本文は、現在は復号後にゲームが展開した `words\out\v1\*.json` と、そのローカルコピー `words_main.json` から取得する。

### プロトバフ構造

```
0x0A [varint: 外部メッセージ長]
  0x0A [varint: ID長] [ASCII ID文字列]
  [field_tag] [varint/float/string ...]
```

主要フィールド: `f2`=アビリティタイプ, `f14`=効果値, `f55`=対象(self/opponent)

---

## UIローカライズファイル調査結果（2026-05-26）

### 目的
バフ/アビリティタイプ名のゲーム本来の日本語訳を取得しようとした。

### 調査したファイル

| ファイル | 結果 |
|---|---|
| `Champions_Data/Resources/Data/ui/ui.assetbundle` (61MB) | UIアニメーション/コンポーネントのみ。ローカライズなし |
| `Champions_Data/resources.assets` (28MB) | 一部平文、ローカライズ部分は暗号化 |

### resources.assets の構造

**平文（読み取り可能）:**
- `AttributeDefs` — 属性定義JSON（armor, fury, bleed 等の内部名）
- `KeywordConfig` — ツールチップID定義

**暗号化（読み取り不可）:**
- `bcg_en`, `bcg_stat_en` — ゲーム本体テキスト
- `initial_ja`, `tutorials_ja`, `kabamaccounts_ja`, `tips_ja` — 日本語ローカライズ

暗号化の特徴:
- 全ファイル共通マジックバイト: `4c d2 9e 8f 9f 1e b5 9d`（8バイト）
- エントロピー: 7.997 bits/byte（AES相当）
- zlib / LZ4 / brotli / lzma では解凍不可

### 結論

`GameAssembly.dll`（Unity IL2CPP）内の復号鍵なしには不可。  
→ `ABILITY_TYPE_JP` 辞書の手動メンテで対応する。

### 追記（2026-05-28）

この節は、暗号化された `.bytes` / Unity resources を直接読む方法を調査していた時点の記録。  
現行の `generate_jp_page.py` は、ゲームが復号後にローカルへ展開した次の平文JSONを日本語本文ソースとして使う。

```text
C:\Users\tane1\AppData\LocalLow\Kabam\Champions\words\out\v1\*.json
```

加えて、同形式のローカルコピーとして次も先に読む。

```text
C:\python\mcoc\words_main.json
```

そのため、現行の `champions_jp.html` の能力説明・必殺技説明・シナジー説明は、`resources.assets` や暗号化 `.bytes` を直接読んで生成していない。

### 現在の ABILITY_TYPE_JP 状況

| 項目 | 件数 |
|---|---|
| `ABILITY_TYPE_JP`（翻訳辞書） | 206件 |
| `SKIP_F2`（内部タイプ非表示） | 134件 |
| 頻度10回以上で未対応 | 0件 |

---

## ローカライズデータ取得調査（2026-05-26）

### 目的
`ABILITY_TYPE_JP` 辞書の日本語訳をゲーム本来の表示名で補完したい。

---

### スクショによる翻訳辞書修正

マジックのアビリティ画面スクショ8枚から以下を修正・追加：

| f2 | 修正前 | 修正後 | 種別 |
|---|---|---|---|
| `fury` | フューリー | **激怒** | 誤訳修正 |
| `neutralize` | ニュートライズ | **中和** | 誤訳修正 |
| `degen` / `degeneration` | 変性 | **体力低下** | 誤訳修正 |
| `unblockable` | アンブロッカブル | **防御不能** | 誤訳修正 |
| `falter` | 動揺 | **ひるみ** | 誤訳修正 |
| `limbo` | （未登録） | **リンボ** | 新規追加 |
| `buff_accel_all` | （未登録） | **バフ加速** | 新規追加 |
| `buff_decel_all` | （未登録） | **バフ減速** | 新規追加 |

---

### メモリダンプ試行（失敗）

**目的:** 起動中ゲームのメモリから復号済みテキストを抽出  
**結果:** `ReadProcessMemory` が `err=5`（アクセス拒否）で全領域失敗  
**原因:** ゲームのアンチチート保護がメモリ読み取りをブロック  
**スクリプト:** `dump_memory.py`

---

### Fiddler によるネットワーク傍受

**目的:** ゲームがダウンロードするローカライズファイルを平文で取得  
**結果:**
- `kabam-marvel.shared.mcoc-cdn.net` から2件のZIPをキャプチャ
  - `/protobuf/production/bcg/1/hash.zip` → BCGゲームデータ（31MB）
  - `/protobuf/production/gacha/1/hash.zip` → ガチャデータ
- `words/snapshots/ja/Extra/*.bytes` のダウンロードは**確認できなかった**

`words` フォルダを削除後ゲーム再起動で `.bytes` ファイルが再生成されたが、  
新旧ファイルは**バイト単位で完全一致**（サーバー側で暗号化済みを配信と判明）。

---

### `.bytes` ファイルの暗号化解析

**ファイル:** `bcg_stat_ja.bytes`（4,495,256 bytes）  
**構造:**
```
[0:8]   マジック/バージョン: 4c fd f9 ca cb 5f b7 85
[8:24]  IV候補: 68 a0 21 6f d9 18 9a 8f 1c ff b6 16 07 af c1 3c
[24:]   暗号文: 4,495,232 bytes（16の倍数 ✅ → AES-CBC確定）
```

**エントロピー:** 8.000 bits/byte（AES相当）  
**resources.assets との共通点:** 両方とも `0x4c` 始まり + 8バイトヘッダー + AES-CBC構造  

#### キー探索試行（いずれも失敗）

| 手法 | 内容 | 結果 |
|---|---|---|
| `find_aes_key.py` | `global-metadata.dat` / `GameAssembly.dll` のASCII文字列（16/24/32文字）を試行 | 失敗 |
| `find_aes_key2.py` | DLL全体を16バイトウィンドウでスキャン（約1億候補）、IV embedded / null IVの2パターン | 失敗 |

**結論:** キーはASCII文字列でなく**RAWバイト配列**で格納されている可能性が高い。

---

### ゲームファイルの場所

| ファイル | パス |
|---|---|
| 実行ファイル | `C:\Games\Marvel Contest of Champions\default\game\Champions.exe` |
| GameAssembly.dll | `C:\Games\Marvel Contest of Champions\default\game\GameAssembly.dll`（108MB）|
| global-metadata.dat | `...Champions_Data\il2cpp_data\Metadata\global-metadata.dat`（30MB）|
| ローカライズキャッシュ | `C:\Users\tane1\AppData\LocalLow\Kabam\Champions\words\snapshots\ja\Extra\*.bytes` |

---

### IL2CppDumper / Cpp2IL 試行

| ツール | 結果 |
|---|---|
| Il2CppDumper v6.7.46 | メタデータv39非対応でエラー |
| Cpp2IL 2022.0.7 | 未試行（v39非対応の可能性あり） |

**次の手段候補:**
1. Cpp2ILを試す
2. Ghidraで `GameAssembly.dll` を直接解析してAESキーを探す
3. スクショ＋OCR自動化に切り替える

---

## generate_jp_page.py の動作

現行版は「ゲーム内抽出データのみ」でHTMLを生成する。Spotlight / Wiki / Google翻訳 / `champions.csv` の説明文は、能力説明の主ソースとして使わない。

1. `data/abilities_all.json` と `data/slug_to_prefix.json` を読み込む
   - `extract_abilities.py` が BCG `.bin` から抽出した内部アビリティID、効果種別、数値、参照キーを使う
2. `load_localization()` で日本語ローカライズを統合する
   - 先に `C:\python\mcoc\words_main.json`
   - 次に `C:\Users\tane1\AppData\LocalLow\Kabam\Champions\words\out\v1\*.json`
3. `champion_classes.txt`、`data/champion_names_jp.json`、`data/game_roster_extra_champions.json` などから、ゲーム内に存在するチャンピオン一覧を作る
4. BCG `.bin` から UI表示順、シナジーID、現在有効なアビリティIDを補助的に確認する
5. `ID_UI_STAT_FORMAT_*`、`ID_STAT_ATTRIBUTE_*`、`ID_SPECIAL_ATTACK_*`、`ID_UI_HERO_SYNERGY_*` などの日本語本文を `words` JSON から引き、`data/champions_jp.html` を出力する

### 出力ファイル書き込み注意

Windows NTFS マウントでは `write_text()` がファイルを切り詰めない。  
必ず削除してから書き込む:

```python
if OUTPUT_PATH.exists():
    OUTPUT_PATH.unlink()
OUTPUT_PATH.write_bytes(content.encode("utf-8"))
```

---

## champions_jp.html の機能

- ダークテーマ（背景色 `#0f1117`）
- スティッキーヘッダー＋テキスト検索
- クラス別フィルターバー
- レスポンシブカードグリッド（350px min）
- 各カードに: ゲーム内名、クラス、能力、ステータス表（ゲーム内データがある場合）、シナジー、ポートレート
- 外部依存なし

---

## デプロイ（Xserver VPS）

旧 `build_champion_database.py` 前提のクロール運用は廃止。現行は生成済みの `data/champions_jp.html` と必要な静的アセットを配置する。

| 項目 | 内容 |
|---|---|
| サーバー | Xserver VPS（Ubuntu / 2GB RAM） |
| IP | 85.131.248.47 |
| デプロイ先 | `/root/mcoc/` |
| SSH鍵 | `~/.ssh/xvps`（ed25519） |

### ファイル転送

```powershell
scp -i ~/.ssh/xvps C:\python\mcoc\data\champions_jp.html root@85.131.248.47:~/mcoc/
scp -i ~/.ssh/xvps -r C:\python\mcoc\data\portraits root@85.131.248.47:~/mcoc/
```

### VPS初期セットアップ（初回のみ）

```bash
mkdir -p ~/mcoc/portraits
```

### 日常操作

```bash
# 配置確認
ssh -i ~/.ssh/xvps root@85.131.248.47 "ls -lh ~/mcoc/champions_jp.html"
```

---

## 現在の日本語説明ソース（ゲーム内）

更新日: 2026-05-28

`champions_jp.html` に入るゲーム内日本語の能力説明・必殺技説明・シナジー説明は、`generate_jp_page.py` の `load_localization()` が読むローカライズJSONから取得する。  
本文の主ソースは次の2系統。

```text
C:\python\mcoc\words_main.json
C:\Users\tane1\AppData\LocalLow\Kabam\Champions\words\out\v1\*.json
```

読み込み順は `words_main.json` が先、ゲームキャッシュ `words\out\v1\*.json` が後。  
同じキーがある場合は、後から読んだゲームキャッシュ側の値で上書きされる。

現時点で確認した `words` 系ファイルは次の通り。

| 文字列数 | ファイル | 主な内容 |
|---:|---|---|
| 26,868 | `C:\python\mcoc\words_main.json` | `bcg_stat,client` のローカルコピー。能力説明、能力見出し、必殺技、シナジー説明の補助ソース |
| 26,872 | `C:\Users\tane1\AppData\LocalLow\Kabam\Champions\words\out\v1\7A173BC3C999CF5C90FC6A63D2009BAACC0D40C1.json` | 現行の主ソース。`ID_UI_STAT_FORMAT_*`、`ID_STAT_ATTRIBUTE_*`、`ID_SPECIAL_ATTACK_*`、`ID_UI_HERO_SYNERGY_*`、`ID_PS_*` など |
| 2,522 | `C:\Users\tane1\AppData\LocalLow\Kabam\Champions\words\out\v1\9CBF1A5F1DA3E55FEF1526D7C718F2B9C360431D.json` | `bcg,client`。キャラクターバイオ、必殺技、シナジー、BCG系表示名の一部 |
| 662 | `C:\Users\tane1\AppData\LocalLow\Kabam\Champions\words\out\v1\BC9DAC7AB4B8ADDD5E3311BED975246441BA8E58.json` | `quests,client`。クエスト系テキスト。通常のチャンピオン能力本文にはほぼ使わない |
| 9 | `C:\Users\tane1\AppData\LocalLow\Kabam\Champions\words\out\v1\5A1736D52172C87E94F68DB5D43BADF4C4365460.json` | `tower,client`。タワー系テキスト。通常のチャンピオン能力本文にはほぼ使わない |

主に参照するローカライズキー:

- `ID_UI_STAT_FORMAT_*`
- `ID_STAT_ATTRIBUTE_*`
- `ID_UI_STAT_ATTRIBUTE_*`
- `ID_SPECIAL_ATTACK_*`
- `ID_SPECIAL_ATTACK_DESCRIPTION_*`
- `ID_UI_HERO_SYNERGY_TITLE_*`
- `ID_UI_HERO_SYNERGY_DESC_*`
- `ID_UI_HERO_SYNERGY_DESCRIPTION_*`
- `ID_CHARACTER_BIOS_*`
- `ID_PS_*`

次のファイルは日本語本文の直接ソースではない。

- `data/abilities_all.json`: BCG `.bin` から抽出した内部アビリティID、効果種別、数値、参照キー。日本語本文そのものは入っていない
- `C:\Users\tane1\AppData\LocalLow\Kabam\Champions\bcg\out\v1\*.bin`: UI表示順、シナジー定義、内部IDとローカライズキーの対応確認に使う。日本語本文は `words` JSON から引く
- `data/champions.csv`: 旧スクレイピング/参照用。現行HTMLの能力説明の主ソースではない
- `data/translations_cache.json`: 旧Google翻訳キャッシュ。現行HTMLの能力説明には使わない
- Spotlight / Wiki 由来テキスト: 現行HTMLへ入れない方針

過去の `game_champion_ability_texts_jp.md` / `game_extracted_localized_texts.json` は調査・中間出力。現在の `champions_jp.html` 生成では、上記 `words` JSON と BCG `.bin` の対応情報を `generate_jp_page.py` が直接参照する。

---

## MCOCゲーム内チャンピオン画像の抽出メモ

作成日: 2026-05-27

チャンピオンごとのポートレート画像は、ゲーム本体のインストール先にPNGとして存在する。

主な取得元は次の `ui_portraits*` 配下。

```text
C:\Games\Marvel Contest of Champions\default\game\Champions_Data\Resources\Data\ui_portraits*\portraits\
```

確認時点では、`ui_portraits` 系ディレクトリ全体で画像が590件あった。

代表例:

```text
C:\Games\Marvel Contest of Champions\default\game\Champions_Data\Resources\Data\ui_portraits\portraits\portrait_abomination.png
C:\Games\Marvel Contest of Champions\default\game\Champions_Data\Resources\Data\ui_portraits\portraits\portrait_blade.png
C:\Games\Marvel Contest of Champions\default\game\Champions_Data\Resources\Data\ui_portraits\portraits\portrait_magik.png
C:\Games\Marvel Contest of Champions\default\game\Champions_Data\Resources\Data\ui_portraits_56.0\portraits\portrait_blade_stellar.png
C:\Games\Marvel Contest of Champions\default\game\Champions_Data\Resources\Data\ui_portraits_56.0\portraits\portrait_rubythursday.png
C:\Games\Marvel Contest of Champions\default\game\Champions_Data\Resources\Data\ui_portraits_56.1\portraits\portrait_wave.png
```

チャンピオン名つきのアイコン/ポートレートを取りたい場合は、この `ui_portraits*\portraits` を使うのが最も扱いやすい。

一方、ローカルキャッシュにも画像は大量にある。

```text
C:\Users\tane1\AppData\LocalLow\Kabam\Champions\asset_cache\files
```

確認時点の内訳:

| 拡張子 | 件数 |
|---|---:|
| `.png` | 1,432 |
| `.jpg` | 973 |
| `.json` | 748 |
| `.jpeg` | 7 |

ただし `asset_cache\files` の画像はハッシュ名になっており、チャンピオン名との対応付けが面倒。チャンピオン別画像として使うなら、まずゲーム本体側の `ui_portraits*\portraits` を優先する。

補足: 全身モデル、3Dモデル、テクスチャなどまで抽出したい場合は、各チャンピオンのODR AssetBundleをUnityアセットとして読む必要がある。

例:

```text
C:\Games\Marvel Contest of Champions\default\game\Champions_Data\Resources\Data\blade_current_odr\blade_current.assetbundle
C:\Games\Marvel Contest of Champions\default\game\Champions_Data\Resources\Data\rubythursday_current_odr\rubythursday_current.assetbundle
```

この場合はPNGコピーだけでは済まず、AssetBundle解析用ツールまたはライブラリを使う別工程になる。
