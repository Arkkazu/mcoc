#!/usr/bin/env python3
"""
MCoC プロセスメモリから日本語テキストを抽出するスクリプト
Windows上で管理者権限で実行すること。
"""
import ctypes
import ctypes.wintypes
import re
import json
import struct
from pathlib import Path

# ─── Windows API ───────────────────────────────────────────────
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
advapi32 = ctypes.WinDLL('advapi32', use_last_error=True)

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def enable_debug_privilege():
    """SeDebugPrivilege を有効化（管理者権限が必要）"""
    SE_DEBUG_NAME = "SeDebugPrivilege"
    TOKEN_ADJUST_PRIVILEGES = 0x0020
    TOKEN_QUERY = 0x0008
    SE_PRIVILEGE_ENABLED = 0x0002

    class LUID(ctypes.Structure):
        _fields_ = [("LowPart", ctypes.wintypes.DWORD),
                    ("HighPart", ctypes.c_long)]

    class LUID_AND_ATTRIBUTES(ctypes.Structure):
        _fields_ = [("Luid", LUID),
                    ("Attributes", ctypes.wintypes.DWORD)]

    class TOKEN_PRIVILEGES(ctypes.Structure):
        _fields_ = [("PrivilegeCount", ctypes.wintypes.DWORD),
                    ("Privileges", LUID_AND_ATTRIBUTES * 1)]

    h_token = ctypes.wintypes.HANDLE()
    advapi32.OpenProcessToken(
        kernel32.GetCurrentProcess(),
        TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY,
        ctypes.byref(h_token)
    )
    luid = LUID()
    advapi32.LookupPrivilegeValueW(None, SE_DEBUG_NAME, ctypes.byref(luid))
    tp = TOKEN_PRIVILEGES()
    tp.PrivilegeCount = 1
    tp.Privileges[0].Luid = luid
    tp.Privileges[0].Attributes = SE_PRIVILEGE_ENABLED
    advapi32.AdjustTokenPrivileges(h_token, False, ctypes.byref(tp), 0, None, None)
    kernel32.CloseHandle(h_token)
    err = ctypes.get_last_error()
    return err == 0

PROCESS_VM_READ            = 0x0010
PROCESS_QUERY_INFORMATION  = 0x0400
MEM_COMMIT                 = 0x1000
PAGE_NOACCESS              = 0x01
PAGE_GUARD                 = 0x100

class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BaseAddress",       ctypes.c_ulonglong),
        ("AllocationBase",    ctypes.c_ulonglong),
        ("AllocationProtect", ctypes.wintypes.DWORD),
        ("RegionSize",        ctypes.c_ulonglong),
        ("State",             ctypes.wintypes.DWORD),
        ("Protect",           ctypes.wintypes.DWORD),
        ("Type",              ctypes.wintypes.DWORD),
    ]

def find_process(names):
    """プロセス名からPIDを探す"""
    import subprocess
    result = subprocess.run(
        ['tasklist', '/FO', 'CSV', '/NH'],
        capture_output=True, text=True, encoding='utf-8', errors='ignore'
    )
    procs = {}
    for line in result.stdout.strip().splitlines():
        parts = line.strip('"').split('","')
        if len(parts) >= 2:
            pname = parts[0].lower()
            try:
                pid = int(parts[1])
                procs[pname] = pid
            except ValueError:
                pass

    for name in names:
        if name.lower() in procs:
            return procs[name.lower()], name
    # 部分一致
    for pname, pid in procs.items():
        for name in names:
            if name.lower().split('.')[0] in pname:
                return pid, pname
    return None, None

def open_process(pid):
    handle = kernel32.OpenProcess(
        PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, pid
    )
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    return handle

def read_memory(handle, address, size):
    buf = ctypes.create_string_buffer(size)
    bytes_read = ctypes.c_ulonglong(0)
    ok = kernel32.ReadProcessMemory(handle, ctypes.c_ulonglong(address), buf, size, ctypes.byref(bytes_read))
    if ok:
        return bytes(buf[:bytes_read.value])
    return None

def enum_regions(handle):
    mbi = MEMORY_BASIC_INFORMATION()
    addr = 0
    regions = []
    while True:
        ret = kernel32.VirtualQueryEx(
            handle, ctypes.c_ulonglong(addr),
            ctypes.byref(mbi), ctypes.sizeof(mbi)
        )
        if not ret:
            break
        if (mbi.State == MEM_COMMIT and
            not (mbi.Protect & PAGE_NOACCESS) and
            not (mbi.Protect & PAGE_GUARD)):
            regions.append((mbi.BaseAddress, mbi.RegionSize))
        addr = mbi.BaseAddress + mbi.RegionSize
        if addr >= 0x7FFFFFFFFFFF:
            break
    return regions

# ─── 日本語UTF-8パターン ─────────────────────────────────────
# 3バイト以上の日本語文字列（ひらがな・カタカナ・漢字）
JP_PATTERN = re.compile(
    rb'(?:[\xe3\xe4\xe5\xe6\xe7\xe8\xe9][\x80-\xbf]{2}){2,}'
)

# 既知の日本語バフ名（検証用）
KNOWN_STRINGS = [
    "リンボ", "激怒", "中和", "体力低下", "ひるみ",
    "防御不能", "再生", "無敵", "回避", "スタン",
    "出血", "毒", "燃焼", "凍結", "感電",
]

def scan_process(pid):
    print(f"プロセス PID={pid} に接続中...")
    if not is_admin():
        print("⚠️  管理者権限なし。一部のメモリ領域が読めない可能性があります。")
    ok = enable_debug_privilege()
    print(f"SeDebugPrivilege: {'✅ 有効' if ok else '❌ 取得失敗（管理者で実行してください）'}")
    handle = open_process(pid)
    regions = enum_regions(handle)
    print(f"メモリ領域数: {len(regions)}")

    found_strings = set()
    total_scanned = 0
    fail_count = 0
    first_errors = []

    for i, (base, size) in enumerate(regions):
        if size > 200 * 1024 * 1024:  # 200MB超はスキップ
            continue
        data = read_memory(handle, base, size)
        if not data:
            fail_count += 1
            if len(first_errors) < 3:
                err = ctypes.get_last_error()
                first_errors.append(f"offset={base:#x} size={size:#x} err={err}")
            continue
        total_scanned += len(data)

        for m in JP_PATTERN.finditer(data):
            chunk = m.group()
            try:
                s = chunk.decode('utf-8')
                if len(s) >= 3:  # 3文字以上
                    found_strings.add(s)
            except UnicodeDecodeError:
                pass

        if i % 50 == 0:
            scanned_mb = total_scanned / 1024 / 1024
            print(f"  {i}/{len(regions)} 領域スキャン済み ({scanned_mb:.0f}MB), "
                  f"文字列: {len(found_strings)}件", end='\r')

    kernel32.CloseHandle(handle)
    print(f"\nスキャン完了: {total_scanned/1024/1024:.1f}MB スキャン, "
          f"{fail_count}領域 読み取り失敗, {len(found_strings)}件の日本語文字列")
    if first_errors:
        print("読み取り失敗の例:")
        for e in first_errors:
            print(f"  {e}")
    return found_strings

def main():
    # MCoC プロセス名候補
    candidates = [
        "Champions.exe", "champions.exe",
        "MCOC.exe", "mcoc.exe",
        "Marvel Contest of Champions.exe",
    ]

    pid, name = find_process(candidates)
    if pid is None:
        print("MCoC プロセスが見つかりません。")
        print("実行中のプロセス一覧:")
        import subprocess
        result = subprocess.run(['tasklist', '/FO', 'CSV', '/NH'], capture_output=True, text=True, encoding='utf-8', errors='ignore')
        for line in result.stdout.strip().splitlines()[:30]:
            print(" ", line)
        print("\nプロセス名を入力してください（例: Champions.exe）:")
        name = input().strip()
        for line in result.stdout.strip().splitlines():
            parts = line.strip('"').split('","')
            if len(parts) >= 2 and parts[0].lower() == name.lower():
                pid = int(parts[1])
                break
        if pid is None:
            print("プロセスが見つかりませんでした。")
            return

    print(f"プロセス: {name} (PID={pid})")
    strings = scan_process(pid)

    # 既知文字列のチェック
    print("\n=== 既知バフ名の検出チェック ===")
    for known in KNOWN_STRINGS:
        found = any(known in s for s in strings)
        print(f"  {'✅' if found else '❌'} {known}")

    # 結果保存
    output = Path(__file__).parent / "data" / "memory_strings.json"
    # 長さでフィルタ（3〜200文字）
    filtered = sorted([s for s in strings if 3 <= len(s) <= 200])
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(filtered, f, ensure_ascii=False, indent=2)
    print(f"\n結果を保存: {output} ({len(filtered)}件)")

if __name__ == '__main__':
    main()
