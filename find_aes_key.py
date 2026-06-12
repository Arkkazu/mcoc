#!/usr/bin/env python3
"""
GameAssembly.dll / global-metadata.dat から AES キーを探して
bcg_stat_ja.bytes の復号を試みるスクリプト。
Windows上で実行すること。
"""
import struct, re, itertools
from pathlib import Path

try:
    from Crypto.Cipher import AES
except ImportError:
    import subprocess, sys
    subprocess.run([sys.executable, "-m", "pip", "install", "pycryptodome"], check=True)
    from Crypto.Cipher import AES

BASE         = Path(r"C:\Games\Marvel Contest of Champions\default\game")
METADATA     = BASE / "Champions_Data" / "il2cpp_data" / "Metadata" / "global-metadata.dat"
GAMEASSEMBLY = BASE / "GameAssembly.dll"
ENCRYPTED    = Path(r"C:\python\mcoc\bcg_stat_ja.bytes")
OUTPUT_DIR   = Path(r"C:\python\mcoc\data")

# ─── 暗号化ファイルの構造 ────────────────────────────────────
# [0:8]   magic (8 bytes)
# [8:24]  IV    (16 bytes) ← 候補1
# [24:]   ciphertext       ← 候補1
# または
# [8:]    ciphertext (IV=all zeros) ← 候補2
enc_data = ENCRYPTED.read_bytes()
magic       = enc_data[0:8]
iv_embedded = enc_data[8:24]
cipher1     = enc_data[24:]   # IV embedded
cipher2     = enc_data[8:]    # IV = null

print(f"暗号化ファイル: {len(enc_data):,} bytes")
print(f"magic:       {magic.hex()}")
print(f"IV候補:      {iv_embedded.hex()}")
print(f"暗号文1長さ: {len(cipher1)} ({len(cipher1)%16==0})")
print(f"暗号文2長さ: {len(cipher2)} ({len(cipher2)%16==0})")

def try_decrypt(key_bytes, label=""):
    """AES-CBCで復号を試みる。有効なUTF-8テキストが得られたら返す"""
    results = []
    # 候補1: IV = embedded
    if len(cipher1) % 16 == 0 and len(key_bytes) in (16, 24, 32):
        try:
            cipher = AES.new(key_bytes, AES.MODE_CBC, iv=iv_embedded)
            plain = cipher.decrypt(cipher1)
            # パディング除去 (PKCS7)
            pad = plain[-1]
            if 1 <= pad <= 16:
                plain_unpad = plain[:-pad]
            else:
                plain_unpad = plain
            # 有効テキスト判定
            score = check_plaintext(plain_unpad)
            if score > 0:
                results.append((score, "embedded_iv", key_bytes, plain_unpad[:200]))
        except Exception:
            pass

    # 候補2: IV = null (all zeros)
    null_iv = b'\x00' * 16
    if len(cipher2) % 16 == 0 and len(key_bytes) in (16, 24, 32):
        try:
            cipher = AES.new(key_bytes, AES.MODE_CBC, iv=null_iv)
            plain = cipher.decrypt(cipher2)
            pad = plain[-1]
            if 1 <= pad <= 16:
                plain_unpad = plain[:-pad]
            else:
                plain_unpad = plain
            score = check_plaintext(plain_unpad)
            if score > 0:
                results.append((score, "null_iv", key_bytes, plain_unpad[:200]))
        except Exception:
            pass

    return results

def check_plaintext(data):
    """復号結果が有意なテキストかどうかスコア付け（厳格版）"""
    if not data or len(data) < 100:
        return 0

    sample = data[:500]

    # UTF-8として有効かチェック
    try:
        text = sample.decode('utf-8')
    except UnicodeDecodeError:
        return 0  # UTF-8として無効 → 確実に不正解

    # 印字可能文字率（500バイト中）
    printable = sum(1 for c in text if c.isprintable() or c in '\n\r\t')
    ratio = printable / len(text)

    if ratio < 0.85:
        return 0  # 85%未満は不正解

    score = int(ratio * 10)

    # JSON構造チェック
    if data[:1] == b'{' and b'"' in sample[:50] and b':' in sample[:50]:
        score += 10
    elif data[:1] == b'[' and b'"' in sample[:50]:
        score += 8

    # 日本語テキストが含まれる
    jp = len(re.findall(rb'[\xe3\xe4\xe5\xe6\xe7\xe8\xe9][\x80-\xbf]{2}', sample))
    if jp > 5:
        score += jp

    return score

# ─── global-metadata.dat から文字列を抽出 ───────────────────
print("\n=== global-metadata.dat から候補キー文字列を抽出 ===")

meta = METADATA.read_bytes()
print(f"metadata サイズ: {len(meta):,} bytes")
print(f"metadata magic: {meta[:4].hex()}")

# Unity IL2CPP metadata ヘッダーのパース
# magic: 0xFAB11BAF (little-endian)
UNITY_META_MAGIC = 0xFAB11BAF
if struct.unpack_from('<I', meta, 0)[0] == UNITY_META_MAGIC:
    print("Unity IL2CPP metadata 形式を確認")
    version = struct.unpack_from('<I', meta, 4)[0]
    print(f"バージョン: {version}")
    # string literalのオフセット (バージョンによって異なる)
    # v29以降: offset 0x48あたり
    str_offset = struct.unpack_from('<I', meta, 0x48)[0]
    str_count  = struct.unpack_from('<I', meta, 0x4C)[0]
    print(f"文字列セクション offset={str_offset:#x}, size={str_count}")
    str_data = meta[str_offset:str_offset+str_count]
else:
    print("標準形式でない。全体から文字列を抽出します")
    str_data = meta

# ASCII 文字列パターンで候補を抽出
key_candidates = set()
pattern = re.compile(rb'[ -~]{10,64}')
for m in pattern.finditer(str_data):
    s = m.group()
    if len(s) in (16, 24, 32):
        key_candidates.add(s)
    # Base64デコードして16/24/32バイトになるものも試す
    if len(s) in (24, 32, 44, 48):
        import base64
        try:
            decoded = base64.b64decode(s)
            if len(decoded) in (16, 24, 32):
                key_candidates.add(decoded)
        except Exception:
            pass

print(f"候補キー数: {len(key_candidates)}")

# ─── 各候補で復号試行 ────────────────────────────────────────
print("\n=== 復号試行 ===")
found = []
for i, key in enumerate(key_candidates):
    results = try_decrypt(key)
    if results:
        for score, mode, k, preview in results:
            found.append((score, mode, k, preview))
            print(f"✅ スコア={score} モード={mode} キー={k!r}")
            print(f"   先頭: {preview[:80]}")

    if i % 1000 == 0 and i > 0:
        print(f"  {i}/{len(key_candidates)} 試行済み...", end='\r')

if not found:
    print("文字列候補では見つかりませんでした。GameAssembly.dll をスキャンします...")

    # GameAssembly.dll からも抽出
    print(f"\nGameAssembly.dll を読み込み中 ({GAMEASSEMBLY.stat().st_size/1024/1024:.0f}MB)...")
    dll = GAMEASSEMBLY.read_bytes()
    dll_candidates = set()
    for m in pattern.finditer(dll):
        s = m.group()
        if len(s) in (16, 24, 32):
            dll_candidates.add(s)

    # metadataとの差分だけ試す
    new_candidates = dll_candidates - key_candidates
    print(f"DLL追加候補: {len(new_candidates)}")

    for i, key in enumerate(new_candidates):
        results = try_decrypt(key)
        if results:
            for score, mode, k, preview in results:
                found.append((score, mode, k, preview))
                print(f"✅ スコア={score} モード={mode} キー={k!r}")
                print(f"   先頭: {preview[:80]}")
        if i % 5000 == 0 and i > 0:
            print(f"  {i}/{len(new_candidates)} 試行済み...", end='\r')

if found:
    best = max(found, key=lambda x: x[0])
    score, mode, key, preview = best
    print(f"\n=== 最良の結果 ===")
    print(f"キー: {key!r} ({len(key)}バイト)")
    print(f"モード: {mode}")
    print(f"先頭テキスト: {preview[:200]}")

    # フル復号して保存
    if mode == "embedded_iv":
        cipher = AES.new(key, AES.MODE_CBC, iv=iv_embedded)
        plain = cipher.decrypt(cipher1)
    else:
        cipher = AES.new(key, AES.MODE_CBC, iv=b'\x00'*16)
        plain = cipher.decrypt(cipher2)

    out = OUTPUT_DIR / "bcg_stat_ja_decrypted.bin"
    out.write_bytes(plain)
    print(f"復号ファイルを保存: {out}")
else:
    print("\n文字列キーでは復号できませんでした。")
    print("次の手段: IL2CppDumperでバイト配列キーを探す必要があります。")
