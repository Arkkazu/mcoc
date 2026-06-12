#!/usr/bin/env python3
"""
GameAssembly.dll の全16バイトウィンドウをAESキー候補として試すブルートフォース。
最初のブロックだけ復号してUTF-8有効かチェックすることで高速化。
"""
import struct
from pathlib import Path
from Crypto.Cipher import AES

GAMEASSEMBLY = Path(r"C:\Games\Marvel Contest of Champions\default\game\GameAssembly.dll")
ENCRYPTED    = Path(r"C:\python\mcoc\bcg_stat_ja.bytes")
OUTPUT_DIR   = Path(r"C:\python\mcoc\data")

enc = ENCRYPTED.read_bytes()

# 試すIV/暗号文パターン
PATTERNS = [
    ("embedded_iv_8",  enc[8:24],      enc[24:],    "magic8+IV16+cipher"),
    ("null_iv_8",      b'\x00'*16,     enc[8:],     "magic8+cipher(IV=0)"),
    ("null_iv_0",      b'\x00'*16,     enc,         "全体暗号文(IV=0)"),
    ("embedded_iv_0",  enc[0:16],      enc[16:],    "IV16+cipher"),
]

for pname, iv, ciphertext, desc in PATTERNS:
    if len(ciphertext) % 16 != 0:
        print(f"スキップ {pname}: 暗号文が16の倍数でない ({len(ciphertext)})")
        PATTERNS = [(n,v,c,d) for n,v,c,d in PATTERNS if n != pname]

print(f"試すパターン: {[p[0] for p in PATTERNS]}")

# メインパターン（最初のものをデフォルト使用）
iv          = PATTERNS[0][1]
ciphertext  = PATTERNS[0][2]
first_block = ciphertext[:16]

print(f"IV:           {iv.hex()}")
print(f"最初のブロック: {first_block.hex()}")
print(f"DLL読み込み中...")

dll = GAMEASSEMBLY.read_bytes()
dll_size = len(dll)
print(f"DLLサイズ: {dll_size:,} bytes")
print(f"候補数: {dll_size - 15:,}")
print("スキャン開始...")

VALID_STARTS = set(range(0x20, 0x7F)) | {0x0A, 0x0D, 0x09, 0xEF, 0xE3, 0xE4, 0xE5}

found = []
report_interval = 1_000_000

for pat_name, pat_iv, pat_cipher, pat_desc in PATTERNS:
    first_b = pat_cipher[:16]
    print(f"\nパターン [{pat_name}] {pat_desc}")
    print(f"  IV={pat_iv.hex()}, first_block={first_b.hex()}")

    for i in range(dll_size - 15):
        key = dll[i:i+16]

        if len(set(key)) < 4:
            continue

        try:
            cipher = AES.new(key, AES.MODE_ECB)
            dec_block = cipher.decrypt(first_b)
            plain16 = bytes(a ^ b for a, b in zip(dec_block, pat_iv))

            if plain16[0] not in VALID_STARTS:
                continue

            readable = sum(1 for b in plain16
                           if 0x20 <= b <= 0x7E or b in (0x09,0x0A,0x0D)
                           or 0x80 <= b <= 0xBF or b >= 0xE3)
            if readable < 12:
                continue

            cipher2 = AES.new(key, AES.MODE_CBC, iv=pat_iv)
            plain128 = cipher2.decrypt(pat_cipher[:128])
            try:
                text = plain128.decode('utf-8')
                printable = sum(1 for c in text if c.isprintable() or c in '\n\r\t')
                if printable / len(text) < 0.85:
                    continue
            except UnicodeDecodeError:
                continue

            print(f"\n✅ キー候補! pattern={pat_name} offset={i:#x}")
            print(f"   キー: {key.hex()} = {key!r}")
            print(f"   先頭: {plain128[:80]!r}")
            found.append((pat_name, pat_iv, pat_cipher, i, key, plain128))

        except Exception:
            continue

        if i % report_interval == 0 and i > 0:
            pct = i / dll_size * 100
            print(f"  {pct:.1f}%", end='\r')

print(f"\nスキャン完了。{len(found)}件の候補")

if found:
    pat_name, pat_iv, pat_cipher, offset, key, _ = found[0]
    print(f"\nフル復号中... pattern={pat_name} キー offset={offset:#x}")
    cipher = AES.new(key, AES.MODE_CBC, iv=pat_iv)
    plain = cipher.decrypt(pat_cipher)

    out = OUTPUT_DIR / "bcg_stat_ja_decrypted.bin"
    out.write_bytes(plain)
    print(f"保存: {out}")
    print(f"先頭256バイト: {plain[:256]!r}")
