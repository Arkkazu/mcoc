"""
MCoC チャンピオン能力データ抽出スクリプト
ソース: AppData BCG バイナリ (.bin)
出力:  data/abilities/<champion_prefix>.json (チャンピオン別)
       data/abilities_all.json (全チャンピオン統合)
"""

import re
import struct
import json
import os
from collections import defaultdict
from pathlib import Path

BIN_PATH = Path("B64FC6A6D6243DB2A88B295572F5B5F145A66393.bin")
OUT_DIR  = Path("data/abilities")
OUT_ALL  = Path("data/abilities_all.json")

# ゲームモード・インフラ系プレフィックス（チャンピオン以外）
SKIP_PREFIXES = {
    "pve", "nec", "aol", "sb", "avx", "raid", "rel", "gmaster", "nmaster",
    "ava", "m", "aq", "ave", "dun", "kangsup", "aw", "col", "lab",
    "carserp", "glyk", "bhmt", "spunk", "kangimp",
    "tbe", "gmast", "karrie", "joov", "wccn", "atma", "pvp", "a1",
    "bg", "apfoo",
}

KEEP_SHORT_PREFIXES = {
    # Classic Abomination keeps one old all-attacks Fury entry under abm_*.
    "abm",
}


def read_varint(data: bytes, pos: int) -> tuple[int, int]:
    result, shift = 0, 0
    while pos < len(data):
        b = data[pos]; pos += 1
        result |= (b & 0x7F) << shift
        shift += 7
        if not (b & 0x80):
            break
    return result, pos


def parse_entries(raw: bytes) -> list[dict]:
    entries = []
    i, n = 0, len(raw)
    while i < n - 10:
        if raw[i] != 0x0A:
            i += 1
            continue
        i += 1
        outer_len, j = read_varint(raw, i)
        if outer_len < 5 or outer_len > 200000 or j + outer_len > n:
            continue
        msg_end = j + outer_len
        if raw[j] != 0x0A:
            continue
        j += 1
        id_len, j = read_varint(raw, j)
        if id_len < 3 or id_len > 100 or j + id_len > n:
            continue
        id_bytes = raw[j:j + id_len]
        if not all(0x20 <= b <= 0x7E for b in id_bytes):
            continue
        id_str = id_bytes.decode("ascii")
        if not re.match(r"^[a-zA-Z][a-zA-Z0-9_]+$", id_str):
            continue
        j += id_len

        fields: dict = {}
        fc = 0
        while j < msg_end and fc < 50:
            fc += 1
            if j >= msg_end:
                break
            tb = raw[j]; j += 1
            wt = tb & 7
            fn = tb >> 3
            if tb & 0x80:
                if j >= msg_end:
                    break
                tb2 = raw[j]; j += 1
                fn = ((tb & 0x7F) >> 3) | ((tb2 & 0x7F) << 4)
            if wt == 2:
                fl, j = read_varint(raw, j)
                if fl < 0 or fl > 50000 or j + fl > msg_end:
                    break
                if 1 <= fl <= 500:
                    fb = raw[j:j + fl]
                    if all(0x20 <= b <= 0x7E for b in fb):
                        fields[fn] = fb.decode("ascii")
                j += fl
            elif wt == 0:
                val, j = read_varint(raw, j)
                fields[fn] = val
            elif wt == 5:
                if j + 4 <= msg_end:
                    fields[fn] = struct.unpack_from("<f", raw, j)[0]
                    j += 4
            else:
                break

        if fields:
            entries.append({"id": id_str, **{f"f{k}": v for k, v in fields.items()}})
        i = msg_end
    return entries


def classify_entry(entry: dict) -> str:
    """エントリIDからカテゴリを推定する"""
    eid = entry["id"]
    if "_syn_" in eid:
        return "synergy"
    if "_sig_" in eid:
        return "signature"
    if "_sp1_" in eid or eid.endswith("_sp1"):
        return "special1"
    if "_sp2_" in eid or eid.endswith("_sp2"):
        return "special2"
    if "_sp3_" in eid or eid.endswith("_sp3"):
        return "special3"
    if "_hvy_" in eid or eid.endswith("_hvy"):
        return "heavy"
    if "_aa_" in eid:
        return "passive"
    if "_rmv" in eid or eid.endswith("_rmv"):
        return "remove"
    if "_ui" in eid or "_hud" in eid or "_icon" in eid or "_vfx" in eid:
        return "ui"
    return "other"


def main():
    print(f"バイナリ読み込み: {BIN_PATH}")
    raw = BIN_PATH.read_bytes()
    print(f"  サイズ: {len(raw):,} bytes")

    print("エントリ解析中...")
    entries = parse_entries(raw)
    print(f"  総エントリ数: {len(entries):,}")

    # プレフィックスでグループ化
    by_prefix: dict[str, list] = defaultdict(list)
    for e in entries:
        prefix = e["id"].split("_")[0]
        if prefix not in SKIP_PREFIXES:
            by_prefix[prefix].append(e)

    print(f"  チャンピオン候補プレフィックス数: {len(by_prefix)}")

    # 出力ディレクトリ作成
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # チャンピオン別 JSON 出力
    all_data = {}
    written = 0
    for prefix, elist in sorted(by_prefix.items()):
        # 少なすぎるエントリは原則ノイズ。ただし旧式キャラの補助prefixは保持する。
        if len(elist) < 3 and prefix not in KEEP_SHORT_PREFIXES:
            continue

        # カテゴリ別に整理
        categorized: dict[str, list] = defaultdict(list)
        for e in elist:
            cat = classify_entry(e)
            categorized[cat].append(e)

        champion_data = {
            "prefix": prefix,
            "total_entries": len(elist),
            "categories": {cat: entries for cat, entries in sorted(categorized.items())},
        }

        out_path = OUT_DIR / f"{prefix}.json"
        out_path.write_text(json.dumps(champion_data, ensure_ascii=False, indent=2))
        all_data[prefix] = champion_data
        written += 1

    # 統合ファイル出力
    OUT_ALL.write_text(json.dumps(
        {"total_champions": written, "champions": all_data},
        ensure_ascii=False, indent=2
    ))

    print(f"\n完了:")
    print(f"  チャンピオン別ファイル: {written}件 -> {OUT_DIR}/")
    print(f"  統合ファイル: {OUT_ALL}")

    # サマリー表示
    print(f"\n=== エントリ数上位20チャンピオン ===")
    for prefix, data in sorted(all_data.items(), key=lambda x: -x[1]["total_entries"])[:20]:
        cats = data["categories"]
        flags = []
        if "passive" in cats:   flags.append(f"passive:{len(cats['passive'])}")
        if "signature" in cats: flags.append(f"sig:{len(cats['signature'])}")
        if "synergy" in cats:   flags.append(f"syn:{len(cats['synergy'])}")
        if "special1" in cats:  flags.append(f"sp1:{len(cats['special1'])}")
        print(f"  {prefix:15s} {data['total_entries']:4d}件  {' '.join(flags)}")


if __name__ == "__main__":
    os.chdir(Path(__file__).parent)
    main()
