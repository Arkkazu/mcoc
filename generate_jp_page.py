#!/usr/bin/env python3
"""
MCOC チャンピオン日本語解説ページ生成スクリプト

ゲーム内抽出データ（BCG由来のクラス/アビリティ/ローカライズ）を使い、
単一の検索・フィルター機能付き HTML ページを生成する。

使用方法:
  python3 generate_jp_page.py
"""

import json
from pathlib import Path

# ─── パス設定 ───────────────────────────────────────────────
BASE = Path(__file__).parent
OUTPUT_PATH     = BASE / "data" / "champions_jp.html"
ABILITIES_PATH  = BASE / "data" / "abilities_all.json"
SLUG_MAP_PATH   = BASE / "data" / "slug_to_prefix.json"
NAME_JP_PATH    = BASE / "data" / "slug_to_jp.json"
WORDS_PATH      = BASE / "words_main.json"
CHAMP_NAMES_PATH = BASE / "data" / "champion_names_jp.json"
EXTRA_CHAMPIONS_PATH = BASE / "data" / "game_roster_extra_champions.json"
CHAMPION_CLASSES_PATH = BASE / "champion_classes.txt"
CHAMPIONS_SUMMARY_PATH = BASE / "champions_summary.txt"
GAME_WORDS_OUT = Path(r"C:\Users\tane1\AppData\LocalLow\Kabam\Champions\words\out\v1")
GAME_BCG_OUT = Path(r"C:\Users\tane1\AppData\LocalLow\Kabam\Champions\bcg\out\v1")

# ─── 定数 ────────────────────────────────────────────────────
CLASS_JP = {
    "Science": "サイエンス",
    "Mutant":  "ミュータント",
    "Skill":   "スキル",
    "Cosmic":  "コスミック",
    "Tech":    "テック",
    "Mystic":  "ミスティック",
}

CLASS_COLORS = {
    "Science": "#52aa17",
    "Mutant":  "#f8c11b",
    "Skill":   "#eb1212",
    "Cosmic":  "#009ac6",
    "Tech":    "#0459d8",
    "Mystic":  "#bc22c6",
}

ATTR_JP = {
    "SURVIVABILITY":    "生存性",
    "DAMAGE":           "ダメージ",
    "EASE OF USE":      "使いやすさ",
    "UTILITY":          "ユーティリティ",
    "DEFENDER STRENGTH": "防衛力",
}

# ゲーム内アビリティタイプ → 日本語
ABILITY_TYPE_JP = {
    # ─ 攻撃系バフ / 変性
    "damage":           "ダメージ",
    "true_damage":      "真撃ダメージ",
    "fury":             "激怒",
    "cruelty":          "残虐",
    "prowess":          "勇気",
    "precision":        "精度",
    "amplify":          "増幅",
    "energize":         "エネルギー付与",
    "crit_rate":        "クリティカル率",
    "crit_rating":      "クリティカル率",
    "crit_damage":      "クリティカルダメージ",
    "crit_dmg":         "クリティカルダメージ",
    "crit_damage_mod":  "クリティカルダメージ増幅",
    "guaranteed_crit":  "確定クリティカル",
    "crit_chance_mod":  "クリティカル率増幅",
    "block_penetration":"ブロック貫通",
    "true_strike":      "直撃",
    "true_accuracy":    "真精度",
    "add_combo":        "コンボ追加",
    "combo_shield":     "コンボシールド",
    "unstoppable":      "無敵",
    "unblockable":      "防御不能",
    "incinerating":     "焼却",
    "disintegrate":     "崩壊",
    "overload":         "オーバーロード",
    "plasma":           "プラズマ",
    "marked":           "マーキング",
    # ─ 回復・防御バフ
    "regen":            "再生",
    "regeneration":     "再生",
    "regen_rate":       "再生率",
    "passive_regen":    "受動再生",
    "mana_regen":       "パワー再生",
    "armor_up":         "アーマーアップ",
    "armor":            "アーマー",
    "protection":       "守護",
    "bulwark":          "砦",
    "indestructible":   "破壊不能",
    "indestructible_cd":"破壊不能（クールダウン）",
    "block_proficiency":"ブロック効果",
    "block_proficiency_mod": "ブロック効果増幅",
    "perfect_block_chance":  "パーフェクトブロック",
    "resist_physical":  "物理耐性",
    "resist_magic":     "魔法耐性",
    "damage_reduction_percent": "ダメージ軽減",
    "steadfast":        "堅強",
    "vigilance":        "警戒",
    "auto_block":       "オートブロック",
    "passive_evade":    "受動回避",
    "endurance":        "耐久力",
    # ─ パワー関係
    "mana_gain":        "パワーゲイン",
    "power_gain":       "パワーゲイン",
    "mana_gain_rate":   "パワー取得率",
    "mana_rate":        "パワー回復率",
    "mana_loss":        "パワー損失",
    "mana_steal":       "パワー奪取",
    "mana_burn":        "パワーバーン",
    "mana_burn_dmg":    "パワーバーンダメージ",
    "power_drain":      "パワードレイン",
    "power_lock":       "パワーロック",
    "power_sting":      "パワースティング",
    "power_steal":      "パワースティール",
    "power_burn":       "パワーバーン",
    "power_dissolve":   "パワーディゾルブ",
    "power_reroute":    "パワーリルート",
    "power_timebomb":   "パワー起爆",
    "power_efficiency": "パワー効率",
    "special_lock":     "必殺技ロック",
    "special_cost_ratio":"スペシャルコスト削減",
    "arcane_font":      "アルケインフォント",
    # ─ デバフ（ダメージ系）
    "bleed":            "流血",
    "passive_bleed":    "受動流血",
    "poison":           "毒",
    "incinerate":       "焼却",
    "coldsnap":         "コールドスナップ",
    "shock":            "ショック",
    "radiation":        "放射線",
    "magnetism":        "磁力",
    "degen":            "体力低下",
    "degeneration":     "体力低下",
    "rupture":          "断裂",
    "neuroshock":       "ニューロショック",
    "acid_burn":        "アシッドバーン",
    "plasma_burn":      "プラズマ灼傷",
    "concussion":       "脳震盪",
    # ─ デバフ（状態異常）
    "stun":             "気絶",
    "battered":         "被弾脆弱",
    "battered_dmg":     "被弾脆弱（ダメージ）",
    "weakness":         "弱体化",
    "slow":             "スロー",
    "disorient":        "困惑",
    "petrify":          "化石化",
    "heal_block":       "ヒールブロック",
    "exhaustion":       "極度の疲労",
    "rooted":           "固定",
    "suppress":         "抑制",
    "wither":           "衰え",
    "debilitate":       "消耗",
    "stagger":          "よろめき",
    "stagger_delay":    "よろめき遅延",
    "miss":             "ミス",
    "ability_suppress": "能力抑制",
    "taunt":            "挑発",
    "intimidate":       "威圧",
    "vuln_physical":    "物理的弱点",
    "vuln_energy":      "エネルギー弱点",
    "armor_break":      "アーマー破壊",
    "armor_shattered":  "アーマー粉砕",
    "armor_pen_mod":    "アーマー貫通",
    "purge":            "バフ除去",
    # ─ 能力無効・コントロール
    "nullify":          "無効化",
    "fateseal":         "運命刻印",
    "placebo":          "プラセボ",
    "neutralize":       "中和",
    "purify":           "浄化",
    "cleanse":          "クレンジング",
    "reflect":          "反射",
    # ─ 回避・カウンター
    "evade":            "回避",
    "auto_evade":       "自動回避",
    "miss_chance":      "回避率",
    # ─ 耐性・免疫
    "debuff_immune":        "デバフ耐性",
    "bleed_immune":         "流血耐性",
    "poison_immune":        "毒耐性",
    "incinerate_immune":    "焼却耐性",
    "coldsnap_immune":      "コールドスナップ耐性",
    "shock_immune":         "ショック耐性",
    "stun_immune":          "気絶耐性",
    "unblockable_immune":   "防御不能耐性",
    "unstoppable_immune":   "無敵耐性",
    "buff_immunity":        "バフ耐性",
    "radiation_immune":     "放射線耐性",
    "magnetism_immune":     "磁力耐性",
    # ─ 特殊
    "refresh_id":           "バフ更新",
    "refresh":              "更新",
    "rally_rate":           "アドレナリン",
    "rally_gain":           "アドレナリン",
    "ability_accuracy":     "スキル精度",
    "effect_accuracy":      "スキル精度",
    "effect_accuracy_id_flat": "スキル精度",
    "effect_accuracy_flat": "スキル精度",
    "effect_accuracy_id":   "スキル精度",
    "heavy_timeout":        "ヘビー延長",
    "adjust_ticktime_id":   "タイマー調整",
    "absolute_strength":    "絶対的な力",
    "power_bar_boost":      "パワーバー強化",
    # ─ チャンピオン固有能力
    "fire_aura":        "炎のオーラ",
    "fire_aura_activate": "炎のオーラ発動",
    "deathtouch":       "即死の一撃",
    "glancing":         "攻撃そらし",
    "fragility":        "虚弱",
    "invulnerable":     "無敵",
    "limbo":            "リンボ",
    "crush":            "押し潰し",
    "pursuit":          "追撃",
    "aspect_of_evolution": "進化の側面",
    "evolution_armor":  "進化アーマー",
    "pixie_spell":      "ピクシー魔法",
    # ─ 耐性・免疫（追加）
    "crit_resist":          "クリティカル耐性",
    "crit_resist_mod":      "クリティカル耐性増幅",
    "crit_pen_mod":         "クリティカル貫通",
    "buff_accel_all":      "バフ加速",
    "buff_decel_all":      "バフ減速",
    "energy_protection":    "エネルギー防護",
    # ─ バフ（追加）
    "copy_buffs":           "バフコピー",
    "damage_increase_percent": "ダメージ増加",
    "grit":                 "根性",
    "fervor":               "炎熱",
    "aptitude":             "適性",
    "reinforce":            "増強",
    "intensify":            "激烈化",
    "resist_up":            "抵抗力アップ",
    "add_combo_multiplier": "コンボ乗数",
    "immortal":             "不死",
    "immortality":          "不死",
    "invincible":           "無敵",
    "untouchable":          "アンタッチャブル",
    "invisibility":         "透明化",
    "unstoppable_charge":   "無敵チャージ",
    "heavy_proficiency":    "重厚感",
    "spectre":              "怪異",
    "uncanny":              "アンキャニー超常現象",
    "block_regen":          "防御再生",
    "power_manipulation":   "パワー操作",
    # ─ デバフ（追加）
    "tranquilize":          "鎮静化",
    "falter":               "ひるみ",
    "cowardice":            "臆病",
    "daunted":              "ひるみ",
    "trauma":               "トラウマ",
    "enervate":             "弱体化",
    "infuriate":            "激昂",
    "fear":                 "恐怖",
    "corrosion":            "腐食",
    "frostbite":            "フロストバイト",
    "decelerate":           "減速",
    "atrophy":              "退行",
    "sabotage":             "妨害",
    "pulverize":            "粉砕",
    "smoulder":             "燻り",
    "sleep":                "睡眠",
    "injury":               "負傷",
    "bleed_vuln":           "流血弱点",
    "bleed_vulnerability":  "流血弱点",
    "ensnare":              "トラップ",
    "sunder":               "切り離し",
    "delirium":             "錯乱状態",
    "debuff_siphon":        "デバフ吸収",
    "invalidate":           "無効化",
    "special_concussion":   "特殊脳震盪",
    "resist_down":          "耐性低下",
    "rage":                 "憤怒",
    "fatigue":              "疲労",
    "exhaustion_buff":      "極度の疲労",
    # ─ 能力
    "pierce":               "貫通",
    "impact":               "衝撃",
    "tracking":             "追跡",
    "true_sense":           "トゥルーセンス",
    "judgment":             "ジャッジメント",
    "inexorable":           "冷徹",
    "vicious":              "狂暴",
    "destroy":              "破壊",
    "dark_tide":            "ダークタイド",
    "purge_id":             "バフ消去",
    "cooldown":             "クールダウン",
}

BUFF_TYPES = {
    "fury", "cruelty", "prowess", "precision", "amplify", "energize",
    "guaranteed_crit", "true_strike", "true_accuracy", "true_damage",
    "combo_shield", "unstoppable", "unblockable", "overload", "plasma",
    "disintegrate", "marked", "regen", "regeneration", "regen_rate",
    "armor_up", "armor", "protection", "bulwark", "indestructible",
    "steadfast", "vigilance", "auto_block", "passive_evade", "endurance",
    "power_gain", "mana_gain", "power_efficiency", "cleanse", "purify",
    "evade", "immortal", "immortality", "invincible", "invulnerable",
    "untouchable", "invisibility", "grit", "fervor", "aptitude",
    "reinforce", "intensify", "heavy_proficiency", "block_regen",
    "true_sense", "refresh", "glancing", "unstoppable_charge",
    "add_combo", "adrenaline", "rally_rate", "rally_gain",
    "absolute_strength", "power_bar_boost", "copy_buffs",
    "damage_increase_percent", "resist_up", "add_combo_multiplier",
    "aspect_of_evolution", "crit_chance_mod", "crit_damage_mod",
}

DEBUFF_TYPES = {
    "bleed", "passive_bleed", "poison", "incinerate", "incinerating",
    "coldsnap", "shock", "radiation", "degen", "degeneration",
    "rupture", "neuroshock", "acid_burn", "plasma_burn", "concussion",
    "stun", "battered", "battered_dmg", "weakness", "slow", "disorient",
    "petrify", "heal_block", "exhaustion", "wither", "debilitate",
    "stagger", "stagger_delay", "taunt", "intimidate",
    "vuln_physical", "vuln_energy", "armor_break", "armor_shattered",
    "fateseal", "neutralize", "power_lock", "power_sting", "power_drain",
    "power_steal", "power_burn", "power_dissolve", "power_timebomb",
    "special_lock", "falter", "daunted", "cowardice", "trauma",
    "enervate", "infuriate", "fear", "corrosion", "frostbite",
    "decelerate", "atrophy", "sabotage", "pulverize", "sleep",
    "injury", "bleed_vuln", "bleed_vulnerability", "ensnare",
    "sunder", "delirium", "invalidate", "rage", "fatigue",
    "tracking", "miss", "suppress", "rooted",
}

BUFF_LABELS_JP = {ABILITY_TYPE_JP[t] for t in BUFF_TYPES if t in ABILITY_TYPE_JP}
DEBUFF_LABELS_JP = {ABILITY_TYPE_JP[t] for t in DEBUFF_TYPES if t in ABILITY_TYPE_JP}


MANUAL_BINARY_TO_PREFIX = {
    # BCGのアビリティ束名と表示用binary idが一致しない古い/特殊キャラ。
    "wolverine_weaponx": "wpnx",
}

AUTO_BINARY_TO_PREFIX = {
    # champions_summary.txt上では本名/短縮名で出るプレイアブル。
    "absorbingman": "carl",
    "blackwidow_timely": "cvbw",
    "brothervoodoo": "drvood",
    "captainbritain_legacy": "capb",
    "champion": "thechamp",
    "cyclops_90s_legacy": "cyc90",
    "doc_ock": "doc",
    "drstrange_legacy": "drstrange",
    "emmafrost_legacy": "emma",
    "ghostrider_cosmic": "cgr",
    "ghostrider_legacy": "ghr",
    "groot_king": "kgu",
    "groot_king_deathless": "kgroot",
    "guillotine_2099": "glt29",
    "guillotine_nameless": "gltn",
    "howardfrontend": "htdu",
    "icephoenix": "icmphx",
    "ironman_movie": "imi",
    "ironman_silvercenturion": "immrk",
    "jjj_spiderslayer": "jjj",
    "magneto_marvelnow": "mgnx",
    "mistersinister": "mrsin",
    "negasonicteenagewarhead": "ntw",
    "nightcarnage": "ncarn",
    "phoenix_dark": "phx",
    "phoenix_legacy": "phx",
    "scarletwitch_current": "scitch",
    "spiderman_movie": "spmcu",
    "spiderman_pavitr": "pvitr",
    "spiderwitch": "spwtch",
    "ultron_prime": "ultu",
    "venompool": "vplu",
    "venomtheduck": "vtd",
    "vision_deathless": "vsn",
    "vision_timely": "visaark",
    "vulture_movie": "vlt",
}

SUPPLEMENTAL_ABILITY_PREFIXES = {
    # Classic Abomination stores its old all-attacks Fury as a one-entry abm_* bundle.
    "abmntn": ("abm",),
}

NON_PLAYABLE_BINARY_PREFIXES = (
    "ex_",
    "npc_",
    "raid_",
    "pvp_",
    "adaptoid_",
    "antivenomoid_",
    "doombot_",
    "dploid_",
    "hnchpl_",
    "lab_",
    "sentinelbot_",
    "sym_",
    "symbioid_",
    "ultron_drone_",
)

NON_PLAYABLE_BINARY_IDS = {
    "chair",
    "cerastes",
    "grandmaster",
    "grandmaster_event",
    "herbie",
    "infinityclaw",
    "isosphere",
    "lockheed",
    "lockjaw",
    "sym_cos_beam",
    "sym_cos_thanos",
    "sym_mut_electric",
    "sym_mut_ground",
    "venomtheduckfrontend",
    "wolverine_xforce",
    "x23_legacy",
}

ALLOW_DUPLICATE_PREFIX_BINARY_IDS = {
    "captainbritain_legacy",
    "drstrange_legacy",
    "emmafrost_legacy",
    "phoenix_dark",
    "phoenix_legacy",
    "vision_deathless",
}


def is_playable_binary_id(binary_id: str) -> bool:
    if binary_id in NON_PLAYABLE_BINARY_IDS:
        return False
    return not any(binary_id.startswith(prefix) for prefix in NON_PLAYABLE_BINARY_PREFIXES)


# ─── ローカライズデータ ───────────────────────────────────────
import re as _re

def load_localization() -> dict:
    """ローカルコピーとゲームキャッシュ words/out/v1 を統合して k→v 辞書を返す"""
    kv: dict = {}
    source_count = 0

    def merge_payload(path: Path) -> None:
        nonlocal source_count
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            return
        strings = data.get("strings", []) if isinstance(data, dict) else []
        added = 0
        for s in strings:
            key = s.get("k")
            value = s.get("v")
            if key and value:
                kv[key] = value
                added += 1
        if added:
            source_count += 1

    if WORDS_PATH.exists():
        merge_payload(WORDS_PATH)
    if GAME_WORDS_OUT.exists():
        for path in sorted(GAME_WORDS_OUT.glob("*.json")):
            merge_payload(path)

    print(f"ローカライズデータ: {len(kv)} エントリ / {source_count} ファイル")
    return kv

def strip_loc_tags(text: str) -> str:
    """カラータグ・リンクタグを除去してプレーンテキストにする"""
    text = _re.sub(r'\[k=[\w/]+\]([^\[]*)\[/k\]', r'\1', text)
    text = _re.sub(r'\[[-a-zA-Z0-9#]+\]|\[/[-a-zA-Z0-9]*\]', '', text)
    return text.strip()


_SYNERGY_GENERIC_JP = {
    "enemies":    "敵同士",
    "teammates":  "チームメイト",
    "rivals":     "ライバル",
    "friends":    "フレンド",
    "strangers":  "ストレンジャー",
}
_STAR_JP = {"1":"1★","2":"2★","3":"3★","4":"4★","5":"5★","6":"6★","7":"7★"}


_WITH_UNIQUE_PAT = _re.compile(r'^(.+?)\s+with\s+.+\s*\(Unique\)\s*$', _re.IGNORECASE)


def translate_synergy_line(line: str) -> str:
    """CSV英語シナジー行をパターン変換で日本語化する"""
    # "Title with Partner(s) (Unique)" → "Title　ユニーク"
    m_wu = _WITH_UNIQUE_PAT.match(line)
    if m_wu:
        return m_wu.group(1).strip() + '　ユニーク'

    name_part = _re.split(r'\s+[-–]\s+|\s+\(', line)[0].strip()
    rest = line[len(name_part):]

    # 汎用シナジー名変換
    for en, jp in _SYNERGY_GENERIC_JP.items():
        if name_part.lower().startswith(en):
            suffix = name_part[len(en):]          # " Lv. 3" など
            name_part = jp + suffix
            break

    # "(N-Star+)" → "（N★以上）"
    rest = _re.sub(
        r'\((\d+)-Star\+\)',
        lambda m: f'（{_STAR_JP.get(m.group(1), m.group(1))}以上）',
        rest
    )
    # "– Unique" / "- Unique" → "　ユニーク"
    rest = _re.sub(r'\s*[-–]\s*Unique', '　ユニーク', rest)

    return (name_part + rest).strip()


_SYNERGY_PARTNER_PAT = _re.compile(r'\[64acff\]([^：\[]+)：\[-\]')
_SYNERGY_GENERIC_LABELS = {'シナジーヒーロー', 'すべてのヒーロー', 'すべてのhヒーロー', 'すべてのチームメンバー'}
_SYNERGY_DESC_MARKERS = ('_DESC', '_DESCRIPTION', '_LONG')
_SYNERGY_DESC_VARIANTS = ('_V5', '_V4', '_V3', '_V2', '_NEW', '_GLOSS', '_N', '')


def clean_synergy_desc(text: str) -> str:
    text = strip_loc_tags(text)
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = _re.sub(r'\{[\d]+\}', '〔数値〕', text)
    return text.strip()


def extract_synergy_partner_labels(raw: str) -> list[str]:
    labels: list[str] = []
    seen: set[str] = set()
    text = strip_loc_tags(raw).replace('\r\n', '\n').replace('\r', '\n')
    for line in _re.split(r'\n+', text):
        line = line.strip(" /　")
        m = _re.match(r'^([^：:\n]{1,90})[：:]', line)
        if not m:
            continue
        label = m.group(1).strip()
        if not label or label in _SYNERGY_GENERIC_LABELS or label.startswith('#'):
            continue
        if label not in seen:
            labels.append(label)
            seen.add(label)
    return labels


def _looks_like_synergy_title(value: str) -> bool:
    title = strip_loc_tags(value).strip()
    if not title or len(title) >= 70:
        return False
    return not any(mark in title for mark in ('：', ':', '。', '{', '\n', '\r'))


def _is_synergy_desc_key(key: str) -> bool:
    key_up = key.upper()
    return any(marker in key_up for marker in _SYNERGY_DESC_MARKERS)


def _variant_score(key: str) -> tuple[int, int, str]:
    key_up = key.upper()
    score = 0
    for token, value in (
        ('_V5', 50), ('_V4', 40), ('_V3', 30), ('_V2', 20),
        ('NEW', 16), ('_N', 12), ('GLOSS', 6), ('B', 2), ('A', 1),
    ):
        if token in key_up:
            score = max(score, value)
    return score, len(key), key


def _best_synergy_desc_key(title_key: str, kv: dict, synergy_keys: list[str]) -> str:
    candidates: set[str] = set()

    def add_stem(stem: str) -> None:
        for suffix in _SYNERGY_DESC_VARIANTS:
            key = stem + suffix
            if key in kv:
                candidates.add(key)
        for key in synergy_keys:
            if key.startswith(stem) and _is_synergy_desc_key(key):
                candidates.add(key)

    if title_key.startswith('ID_STAT_SYNERGY_'):
        add_stem(title_key + '_LONG')

    if title_key.startswith('ID_UI_HERO_SYNERGY_'):
        tail = title_key[len('ID_UI_HERO_SYNERGY_'):]
        if title_key.endswith('_TITLE'):
            base = title_key[:-len('_TITLE')]
            add_stem(base + '_DESC')
            add_stem(base + '_DESCRIPTION')
            add_stem(base + '_LONG')
        if '_TITLE_' in title_key:
            add_stem(title_key.replace('_TITLE_', '_DESC_'))
            add_stem(title_key.replace('_TITLE_', '_DESCRIPTION_'))
            add_stem(title_key.replace('_TITLE_', '_LONG_'))

        add_stem(title_key + '_DESC')
        add_stem(title_key + '_DESCRIPTION')
        add_stem(title_key + '_LONG')
        add_stem('ID_UI_HERO_SYNERGY_DESC_' + tail)
        add_stem('ID_UI_HERO_SYNERGY_DESCRIPTION_' + tail)
        add_stem('ID_UI_HERO_SYNERGY_LONG_' + tail)
        if '_' in tail:
            head, rest = tail.split('_', 1)
            add_stem(f'ID_UI_HERO_SYNERGY_{head}_DESC_{rest}')
            add_stem(f'ID_UI_HERO_SYNERGY_{head}_DESCRIPTION_{rest}')
            add_stem(f'ID_UI_HERO_SYNERGY_{head}_LONG_{rest}')

    if not candidates:
        return ''
    return max(candidates, key=_variant_score)


def collect_localized_synergy_entries(kv: dict) -> list[dict]:
    """ローカライズ内のシナジー表記を、タイトル・説明・対象名として抽出する"""
    synergy_keys = [k for k in kv if 'SYNERGY' in k]
    entries: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for key in sorted(synergy_keys):
        if _is_synergy_desc_key(key) or not _looks_like_synergy_title(kv[key]):
            continue
        desc_key = _best_synergy_desc_key(key, kv, synergy_keys)
        raw_desc = kv.get(desc_key, '') if desc_key else ''
        desc = clean_synergy_desc(raw_desc) if raw_desc else ''
        if not desc:
            continue
        title = strip_loc_tags(kv[key])
        ident = (title, desc)
        if ident in seen:
            continue
        seen.add(ident)
        entries.append({
            'key': key,
            'title': title,
            'desc': desc,
            'partners': extract_synergy_partner_labels(raw_desc),
        })
    return entries


def get_champion_synergies_jp(loc_prefix: str, kv: dict) -> list[tuple[str, str, list[str]]]:
    """ローカライズデータからチャンピオン固有シナジーを (タイトル, 説明文, パートナー名リスト) のリストで返す"""
    result: list[tuple[str, str, list[str]]] = []
    seen_titles: set[str] = set()
    if not loc_prefix:
        return result

    def extract_partners(raw: str) -> list[str]:
        labels = [
            m.group(1).strip()
            for m in _SYNERGY_PARTNER_PAT.finditer(raw)
            if m.group(1).strip() not in _SYNERGY_GENERIC_LABELS
        ]
        return labels or extract_synergy_partner_labels(raw)

    # パターン1: ID_UI_HERO_SYNERGY_{PREFIX}_{NAME} + {NAME}_DESC
    p1_keys = sorted(
        k for k in kv
        if _re.match(rf'^ID_UI_HERO_SYNERGY_{_re.escape(loc_prefix)}_', k)
        and '_DESC' not in k and '_V2' not in k and 'TITLE' not in k
    )
    for k in p1_keys:
        title = strip_loc_tags(kv[k])
        if not title or len(title) >= 60 or title in seen_titles:
            continue
        seen_titles.add(title)
        desc_k = k + '_DESC'
        raw_desc = kv.get(desc_k, '')
        desc = clean_synergy_desc(raw_desc)
        partners = extract_partners(raw_desc)
        result.append((title, desc, partners))

    # パターン2: ID_UI_HERO_SYNERGY_TITLE_{PREFIX}_{N} + DESC_{PREFIX}_{N}
    if not result:
        title_keys = sorted(
            k for k in kv
            if _re.match(rf'^ID_UI_HERO_SYNERGY_TITLE_{_re.escape(loc_prefix)}_', k)
        )
        for tk in title_keys:
            title = strip_loc_tags(kv[tk])
            base_title = _re.sub(r'\s+Lv\.?\s*[\dIVX]+$', '', title).strip()
            if not base_title or len(base_title) >= 60 or base_title in seen_titles:
                continue
            seen_titles.add(base_title)
            m = _re.search(r'_(\d+)', tk)
            num = m.group(1) if m else ''
            desc_k = f'ID_UI_HERO_SYNERGY_DESC_{loc_prefix}_{num}' if num else ''
            raw_desc = kv.get(desc_k, '')
            desc = clean_synergy_desc(raw_desc)
            partners = extract_partners(raw_desc)
            result.append((base_title, desc, partners))

    # パターン3: ID_UI_HERO_SYNERGY_{OTHER}_{PREFIX}_TITLE と、本文が同じbaseまたはbase_DESC
    title_keys = sorted(
        k for k in kv
        if k.startswith('ID_UI_HERO_SYNERGY_')
        and k.endswith('_TITLE')
        and f'_{loc_prefix}' in k
    )
    for tk in title_keys:
        title = strip_loc_tags(kv[tk])
        base_title = _re.sub(r'\s+Lv\.?\s*[\dIVX]+$', '', title).strip()
        if not base_title or len(base_title) >= 60 or base_title in seen_titles:
            continue
        base = tk[:-len('_TITLE')]
        raw_desc = (
            kv.get(base + '_DESC_V3', '') or kv.get(base + '_DESC_V2', '') or
            kv.get(base + '_DESC_NEW', '') or kv.get(base + '_DESC', '') or
            kv.get(base + '_LONG_V3', '') or kv.get(base + '_LONG_V2', '') or
            kv.get(base + '_LONG', '') or kv.get(base + '_V2', '') or kv.get(base, '')
        )
        desc = clean_synergy_desc(raw_desc)
        partners = extract_partners(raw_desc)
        result.append((base_title, desc, partners))
        seen_titles.add(base_title)

    return result


_HERO_RARITY_SUFFIXES = ("cm", "un", "rar", "ep", "leg", "t6", "t7")
_HERO_RARITY_RANK = {suffix: idx for idx, suffix in enumerate(_HERO_RARITY_SUFFIXES)}
_SYNERGY_TITLE_LEVEL_RE = _re.compile(r'_(?:I|II|III|IV|V|VI|VII|VIII|IX|X)$')
_BCG_SYNERGY_CACHE: tuple[dict, dict] | None = None
_BCG_UI_STAT_CACHE: dict[str, list[tuple[int, str]]] | None = None
_BCG_ACTIVE_ABILITY_CACHE: tuple[dict[str, set[str]], dict[str, set[str]]] | None = None


def _latest_game_bcg_path() -> Path | None:
    if not GAME_BCG_OUT.exists():
        return None
    bins = sorted(
        GAME_BCG_OUT.glob("*.bin"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return bins[0] if bins else None


def _variant_base_id(variant_id: str) -> str:
    for suffix in _HERO_RARITY_SUFFIXES:
        tail = "_" + suffix
        if variant_id.endswith(tail):
            return variant_id[:-len(tail)]
    return variant_id


def _variant_suffix(variant_id: str) -> str:
    for suffix in _HERO_RARITY_SUFFIXES:
        if variant_id.endswith("_" + suffix):
            return suffix
    return ""


def _synergy_signature(defn: dict) -> tuple[str, str, tuple[str, ...]]:
    bases: list[str] = []
    seen: set[str] = set()
    for variant_id in defn.get("variants", []):
        base = _variant_base_id(variant_id)
        if base not in seen:
            bases.append(base)
            seen.add(base)
    title_stem = _SYNERGY_TITLE_LEVEL_RE.sub("", defn.get("title_key", ""))
    return title_stem, defn.get("desc_key", ""), tuple(bases)


def load_bcg_synergy_index() -> tuple[dict, dict]:
    """BCG内のシナジー定義と、各チャンピオンに紐づくシナジーIDを返す。"""
    global _BCG_SYNERGY_CACHE
    if _BCG_SYNERGY_CACHE is not None:
        return _BCG_SYNERGY_CACHE

    bcg_path = _latest_game_bcg_path()
    if not bcg_path:
        _BCG_SYNERGY_CACHE = ({}, {})
        return _BCG_SYNERGY_CACHE

    try:
        raw = bcg_path.read_bytes()
    except OSError:
        _BCG_SYNERGY_CACHE = ({}, {})
        return _BCG_SYNERGY_CACHE

    synergy_record_re = _re.compile(
        rb'([a-z][a-z0-9_]{2,})\x12.{0,6}?(ID_UI_HERO_SYNERGY_[A-Z0-9_]+)',
        _re.S,
    )
    synergy_key_re = _re.compile(rb'ID_UI_HERO_SYNERGY_[A-Z0-9_]+')
    variant_re = _re.compile(
        rb'(?<![a-z0-9_])([a-z][a-z0-9_]*_(?:cm|un|rar|ep|leg|t6|t7))(?![a-z0-9_])'
    )
    token_re = _re.compile(rb'[A-Za-z0-9_]{3,}')

    matches = list(synergy_record_re.finditer(raw))
    synergy_defs: dict[str, dict] = {}
    for idx, match in enumerate(matches):
        sid = match.group(1).decode("ascii", "ignore")
        title_key = match.group(2).decode("ascii", "ignore")
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else min(len(raw), start + 3000)
        chunk = raw[start:end]

        keys = [m.group().decode("ascii", "ignore") for m in synergy_key_re.finditer(chunk)]
        desc_key = next(
            (
                key for key in keys[1:]
                if any(marker in key for marker in _SYNERGY_DESC_MARKERS)
            ),
            "",
        )
        if not desc_key:
            continue

        variants: list[str] = []
        seen_variants: set[str] = set()
        for variant_match in variant_re.finditer(chunk):
            variant_id = variant_match.group(1).decode("ascii", "ignore")
            if variant_id in seen_variants:
                continue
            variants.append(variant_id)
            seen_variants.add(variant_id)
        if variants:
            synergy_defs[sid] = {
                "id": sid,
                "title_key": title_key,
                "desc_key": desc_key,
                "variants": variants,
                "pos": start,
            }

    known_synergy_ids = set(synergy_defs)
    hero_record_re = _re.compile(
        rb'(?<![A-Za-z0-9_])([a-z][a-z0-9_]*_(?:cm|un|rar|ep|leg|t6|t7))\x12[\x01-\x40]([a-z][a-z0-9_]*)h'
    )
    raw_rows_by_binary: dict[str, list[tuple[int, int, int, str]]] = {}
    for hero_match in hero_record_re.finditer(raw):
        variant_id = hero_match.group(1).decode("ascii", "ignore")
        binary_id = hero_match.group(2).decode("ascii", "ignore")
        if _variant_base_id(variant_id) != binary_id:
            continue

        chunk = raw[hero_match.start():hero_match.start() + 500]
        cut = len(chunk)
        for marker in (b'\xda\x01', b'\xe0\x01'):
            marker_pos = chunk.find(marker)
            if marker_pos > 0:
                cut = min(cut, marker_pos)
        chunk = chunk[:cut]

        suffix = _variant_suffix(variant_id)
        rank = _HERO_RARITY_RANK.get(suffix, -1)
        local_order = 0
        for token_match in token_re.finditer(chunk):
            sid = token_match.group().decode("ascii", "ignore")
            if sid not in known_synergy_ids:
                continue
            raw_rows_by_binary.setdefault(binary_id, []).append(
                (rank, hero_match.start(), local_order, sid)
            )
            local_order += 1

    synergies_by_binary: dict[str, list[str]] = {}
    for binary_id, rows in raw_rows_by_binary.items():
        chosen_by_sig: dict[tuple[str, str, tuple[str, ...]], tuple[int, int, int, str]] = {}
        for rank, pos, local_order, sid in rows:
            signature = _synergy_signature(synergy_defs[sid])
            current = chosen_by_sig.get(signature)
            if current is None or (rank, pos, local_order) > current[:3]:
                chosen_by_sig[signature] = (rank, pos, local_order, sid)
        selected = sorted(chosen_by_sig.values(), key=lambda item: (item[1], item[2], item[3]))
        synergies_by_binary[binary_id] = [sid for _, _, _, sid in selected]

    print(
        f"ゲーム内シナジー: 定義 {len(synergy_defs)} 件 / 紐づき {len(synergies_by_binary)} 件"
    )
    _BCG_SYNERGY_CACHE = (synergy_defs, synergies_by_binary)
    return _BCG_SYNERGY_CACHE


def load_bcg_ui_stat_index() -> dict[str, list[tuple[int, str]]]:
    """BCGのUI効果ID → ローカライズキー参照を返す。"""
    global _BCG_UI_STAT_CACHE
    if _BCG_UI_STAT_CACHE is not None:
        return _BCG_UI_STAT_CACHE

    bcg_path = _latest_game_bcg_path()
    if not bcg_path:
        _BCG_UI_STAT_CACHE = {}
        return _BCG_UI_STAT_CACHE

    try:
        raw = bcg_path.read_bytes()
    except OSError:
        _BCG_UI_STAT_CACHE = {}
        return _BCG_UI_STAT_CACHE

    start_re = _re.compile(
        rb'(?<![A-Za-z0-9_])([a-z][a-z0-9_]{2,})(?=[\x12\x1a"\*\x32\x3a\x42\x62][\x01-\x7f]ID_)'
    )
    loc_field_tags = {0x12, 0x1a, 0x22, 0x2a, 0x32, 0x3a, 0x42, 0x62}
    result: dict[str, list[tuple[int, str]]] = {}

    for match in start_re.finditer(raw):
        ui_id = match.group(1).decode("ascii", "ignore")
        idx = match.end()
        fields: list[tuple[int, str]] = []
        while idx + 2 < len(raw) and idx < match.end() + 260:
            tag = raw[idx]
            if tag not in loc_field_tags:
                break
            length = raw[idx + 1]
            if length <= 0 or length > 100 or idx + 2 + length > len(raw):
                break
            value = raw[idx + 2:idx + 2 + length]
            if not value.startswith(b"ID_"):
                break
            fields.append((tag, value.decode("ascii", "ignore")))
            idx += 2 + length
        if fields:
            result.setdefault(ui_id, fields)

    _BCG_UI_STAT_CACHE = result
    return _BCG_UI_STAT_CACHE


def load_bcg_active_ability_ids(abilities: dict) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """BCGのランク別レコードから、現在有効なアビリティIDを binary/prefix 別に返す。"""
    global _BCG_ACTIVE_ABILITY_CACHE
    if _BCG_ACTIVE_ABILITY_CACHE is not None:
        return _BCG_ACTIVE_ABILITY_CACHE

    bcg_path = _latest_game_bcg_path()
    if not bcg_path:
        _BCG_ACTIVE_ABILITY_CACHE = ({}, {})
        return _BCG_ACTIVE_ABILITY_CACHE

    ids_by_prefix: dict[str, set[str]] = {}
    id_to_prefixes: dict[str, set[str]] = {}
    for prefix, info in abilities.items():
        prefix_ids: set[str] = set()
        for entries in info.get("categories", {}).values():
            for entry in entries:
                entry_id = entry.get("id", "")
                if not entry_id:
                    continue
                prefix_ids.add(entry_id)
                id_to_prefixes.setdefault(entry_id, set()).add(prefix)
        ids_by_prefix[prefix] = prefix_ids

    known_ids = set(id_to_prefixes)
    if not known_ids:
        _BCG_ACTIVE_ABILITY_CACHE = ({}, {})
        return _BCG_ACTIVE_ABILITY_CACHE

    try:
        raw = bcg_path.read_bytes()
    except OSError:
        _BCG_ACTIVE_ABILITY_CACHE = ({}, {})
        return _BCG_ACTIVE_ABILITY_CACHE

    variant_re = _re.compile(
        rb'(?<![A-Za-z0-9_])([a-z][a-z0-9_]*_(?:cm|un|rar|ep|leg|t6|t7))(?![A-Za-z0-9_])'
    )
    token_re = _re.compile(rb'[A-Za-z0-9_]{3,}')
    rows_by_binary: dict[str, list[tuple[int, int, int, list[str]]]] = {}
    rows_by_prefix: dict[str, list[tuple[int, int, int, list[str]]]] = {}

    for match in variant_re.finditer(raw):
        # Active loadout rows live late in the BCG. Earlier occurrences are roster/synergy records.
        if match.start() < 20_000_000:
            continue
        variant_id = match.group(1).decode("ascii", "ignore")
        binary_id = _variant_base_id(variant_id)
        rank = _HERO_RARITY_RANK.get(_variant_suffix(variant_id), -1)
        chunk = raw[match.start():match.start() + 3500]

        found: list[str] = []
        seen: set[str] = set()
        for token_match in token_re.finditer(chunk):
            entry_id = token_match.group().decode("ascii", "ignore")
            if entry_id not in known_ids or entry_id in seen:
                continue
            found.append(entry_id)
            seen.add(entry_id)
        if len(found) < 2:
            continue

        rows_by_binary.setdefault(binary_id, []).append((rank, len(found), match.start(), found))

        prefix_hits: dict[str, int] = {}
        for entry_id in found:
            for prefix in id_to_prefixes.get(entry_id, ()):
                prefix_hits[prefix] = prefix_hits.get(prefix, 0) + 1
        for prefix, count in prefix_hits.items():
            if count >= 2:
                rows_by_prefix.setdefault(prefix, []).append((rank, count, match.start(), found))

    def select_rows(rows_by_key: dict[str, list[tuple[int, int, int, list[str]]]]) -> dict[str, set[str]]:
        selected_by_key: dict[str, set[str]] = {}
        for key, rows in rows_by_key.items():
            max_rank = max(row[0] for row in rows)
            rank_rows = [row for row in rows if row[0] == max_rank]
            max_count = max(row[1] for row in rank_rows)
            chosen = [row for row in rank_rows if row[1] == max_count]
            ids: set[str] = set()
            for _, _, _, found in chosen:
                ids.update(found)
            if ids:
                selected_by_key[key] = ids
        return selected_by_key

    by_binary = select_rows(rows_by_binary)
    by_prefix = select_rows(rows_by_prefix)
    print(f"ゲーム内有効アビリティ: binary {len(by_binary)} 件 / prefix {len(by_prefix)} 件")
    _BCG_ACTIVE_ABILITY_CACHE = (by_binary, by_prefix)
    return _BCG_ACTIVE_ABILITY_CACHE


def build_loc_prefix_map(slug_map: dict, kv: dict) -> dict:
    """slug → ローカライズキーのプレフィックス マッピングを構築"""
    fmt_prefixes: set[str] = set()
    for k in kv:
        m = _re.match(r'ID_UI_STAT_FORMAT_([A-Z0-9]+)_', k)
        if m:
            fmt_prefixes.add(m.group(1))

    result: dict = {}
    for slug, prefix in slug_map.items():
        p_up = prefix.upper()
        if p_up in fmt_prefixes:
            result[slug] = p_up
            continue
        candidates = [p for p in fmt_prefixes if p.startswith(p_up[:4])]
        if candidates:
            best = max(candidates, key=lambda x: len(_re.match(r'^' + _re.escape(x[:min(len(x), len(p_up))]), p_up + 'X').group() if _re.match(r'^' + _re.escape(x[:min(len(x), len(p_up))]), p_up + 'X') else ''))
            result[slug] = best
    return result


SECTION_NAME_JP: dict[str, str] = {
    # 常時発動系
    "ALWAYS":           "常時発動",
    "ALWYS":            "常時発動",
    "AA_LONG":          "常時発動（詳細）",
    # 回避・ブロック
    "AUTOBLOCK":        "オートブロック",
    "EVADE":            "回避",
    "DASHBACK":         "ダッシュバック",
    "TACEVD":           "戦術的回避",
    "PASSIVE_EVADE":    "受動回避",
    # ダメージ・攻撃
    "DEGEN":            "体力低下",
    "FURYSTYLE":        "激怒スタイル",
    "PROWESS":          "勇気",
    "KILLERINSTINCT":   "殺戮本能",
    "RUTHLESS":         "無慈悲",
    "WARMONGER":        "戦争狂",
    "DIALED_IN":        "ダイヤルイン",
    "DASHATTACK":       "ダッシュ攻撃",
    "PASS_CRIT":        "パッシブ・クリティカル",
    "SP1_BLEED":        "必殺技1 - 流血",
    "SP1_SLOW":         "必殺技1 - スロー",
    "SP2_DAMAGE":       "必殺技2 - ダメージ",
    "SP2_SHOCK":        "必殺技2 - ショック",
    "SP2_LIGHTTEMP":    "必殺技2 - 光の一撃",
    "SP2_NRG_DMG":      "必殺技2 - エネルギーダメージ",
    "SPECIALS12":       "必殺技1＆2",
    "SPECIAL1":         "必殺技1",
    "SPECIAL2":         "必殺技2",
    "SPECIAL3":         "必殺技3",
    "HVY":              "強攻撃",
    # 特定スキル
    "CONF":             "自信",
    "SUPER_CONF":       "絶対的自信",
    "ULTRA_CONF":       "究極の自信",
    "FOT":              "妙技",
    "BLACKORDER":       "ブラックオーダー",
    "GLAIVEDELAY":      "グレイヴ遅延",
    "ILLUSIONS":        "幻影",
    "NIGHTMARE":        "幻想的な悪夢",
    "IMMORTAL_SIG":     "不死のシグネチャー",
    "DEATH":            "デスタッチ",
    "EVOLUTION":        "進化",
    "EVOEXO":           "進化：外骨格",
    "EVOFIELD":         "進化：フィールド",
    "PRIMEVAL":         "太古のまゆ",
    "QUICKSAND":        "流砂",
    "ROCK":             "岩の構造",
    "ROCK_1":           "岩の構造1",
    "ROCK_PAUSE_LONG":  "岩の一時停止",
    "DMGREDUCTION":     "ダメージ軽減",
    "STABLE":           "安定状態",
    "UNSTABLE":         "不安定状態",
    "COMBODET":         "コンボ増加",
    "STUN_INT":         "気絶干渉",
    "STRUCK":           "被弾時",
    "WHNSTRCK":         "被弾時",
    "WHNBLCKTTCK":      "タイムリーブロック時",
    "STRONT_PHYS":      "強力な物理攻撃",
    "RESUPS":           "リソース強化",
    "SROOT":            "強化された根性",
    "COSR_IMM":         "コズミック耐性",
    "ARMORUP_IMMUNITY": "アーマーアップ耐性",
    "DBFFS":            "デバフ&バフ",
    "AMAA":             "反物質反応体",
    "AMC":              "反物質チャージ",
    "EAMP":             "エネルギー付与",
    "EDETON":           "エネルギー爆発",
    "CP":               "狡猾さ",
    "DI":               "不可視",
    "BM":               "アドレナリン",
    "NEURALARROWS":     "ニューラル・アロー",
    "INEVERMISS_AA":    "必中（常時発動）",
    "SIG_BUFFPOT":      "シグネチャー・バフ効力",
    "SIG_DAMAGE":       "シグネチャー・ダメージ",
    "SIGNATURE_LONG":   "シグネチャー（詳細）",
    "INFINITYCLASS_LONG": "無限クラス",
    "PLANOBS":          "軌道観測",
    "PLNCHRG":          "惑星チャージ",
    "HARDWAREUP":       "ハードウェア強化",
    "IMMU":             "耐性",
    "SYN":              "シナジー",
    "MYSTC":            "ミスティック",
    "ST":               "スタン",
    "PV":               "パッシブ",
    "ME":               "変異強化",
    "GH":               "ガンマホーミング",
    "HG":               "ヘビーガード",
    "SPA":              "スパイダーアーモー",
    "SPE":              "スペシャル強化",
    "GMD":              "γ線ダメージ",
    "PMPT":             "プロンプト",
    "COS":              "コズミック",
    "MIEK":             "観衆の興奮",
    "ANALYSIS":         "分析チャージ",
    "FRAC":             "フラクチャード",
    "ADORATION":        "大衆の崇拝",
    "PASSIVE_REGEN":    "受動再生",
    "AMODE":            "サイオニック・モード",
    "CHNL":             "チャネリング",
    "VFX":              "特殊効果",
    "AGGR":             "積極的な交渉",
    "WARMONGER":        "戦争狂の威圧",
    "AGAIN":            "再び立ち上がれ",
    "HEAVY_MEDLEY":     "ヘビー・メドレー",
    "VNMBLSTS":         "ヴェノム・ブラスト",
    "INCIN225":         "焼却（最大225）",
    "KLNTRDB":          "クリンターデバフ",
    "PROWESS_POWER_EXTRA": "勇気（追加パワー）",
    "INEVERMISS_AA":    "必中（常時発動）",
    "INFINITYCLASS_LONG": "無限クラス",
}

_CLS_JP = {"COS": "コズミック", "MUT": "ミュータント", "SCI": "サイエンス",
           "SKL": "スキル", "TECH": "テック", "MYS": "ミスティック"}

# Hardware / Hunter sections (SentinelBot pattern: {CLASS}_{TYPE})
for _cls, _cls_jp in _CLS_JP.items():
    SECTION_NAME_JP[f"{_cls}_HARDWARE"] = f"{_cls_jp}ハードウェア"
    SECTION_NAME_JP[f"{_cls}_HUNTER"]   = f"{_cls_jp}ハンター"
    SECTION_NAME_JP[f"{_cls}_SP1"]      = f"{_cls_jp}必殺技1"
    SECTION_NAME_JP[f"{_cls}_SP2"]      = f"{_cls_jp}必殺技2"


def get_champion_sections(loc_prefix: str, kv: dict,
                          legacy_prefixes: list[str] | None = None) -> list[tuple[str, list[str]]]:
    """チャンピオンの能力説明セクションを (表示名, [説明文...]) のリストで返す"""
    legacy_prefixes = legacy_prefixes or []
    fmt_keys: dict[str, list[tuple[int, str]]] = {}

    def clean_value(value: str) -> str:
        value = _re.sub(r'\{\d+\}', '〔数値〕', strip_loc_tags(value)).strip()
        value = _re.sub(r'\s+', ' ', value)
        return value

    def item_order(suffix: str) -> int:
        if suffix.isdigit():
            return int(suffix)
        if len(suffix) == 1 and suffix.isalpha():
            return 100 + ord(suffix)
        return 500

    def add_grouped(rest: str, value: str) -> None:
        if not rest or rest.startswith(('EGG_', 'EASTER_', 'HUD_', 'DEBUG_')):
            return
        parts = rest.split('_')
        if not parts:
            return
        if parts[-1] in {'TITLE', 'TITLE_LOWER', 'SHORT', 'HUD', 'ICON', 'CALLOUT'}:
            return
        if len(parts) >= 2:
            sec = '_'.join(parts[:-1])
            suffix = parts[-1]
        else:
            sec = parts[0]
            suffix = '1'
        if sec in {'EGG', 'EASTER', 'DEBUG'} or sec.startswith(('EGG_', 'EASTER_', 'DEBUG_')):
            return
        cleaned = clean_value(value)
        if len(cleaned) > 5:
            fmt_keys.setdefault(sec, []).append((item_order(suffix), cleaned))

    search_prefixes = list(dict.fromkeys([p for p in [loc_prefix] + legacy_prefixes if p]))
    for search_prefix in search_prefixes:
        for k, v in kv.items():
            for head in (
                f'ID_UI_STAT_FORMAT_{search_prefix}_',
                f'ID_STAT_ATTRIBUTE_{search_prefix}_',
                f'ID_UI_STAT_ATTRIBUTE_{search_prefix}_',
            ):
                if k.startswith(head):
                    add_grouped(k[len(head):], v)
                    break

    def _lookup_sec_name(loc_prefix: str, sec: str) -> str | None:
        """ローカライズデータからセクション表示名を検索する"""
        candidates = [
            f'ID_UI_STAT_ATTRIBUTE_{loc_prefix}_{sec}',
            f'ID_UI_STAT_ATTRIBUTE_{loc_prefix}_{sec}_TITLE',
            f'ID_STAT_ATTRIBUTE_{loc_prefix}_{sec}_TITLE',
            f'ID_UI_STAT_ATTRIBUTE_TRIGGER_SUBTITLE_ON{loc_prefix}{sec}',
            f'ID_UI_STAT_ATTRIBUTE_TRIGGER_SUBTITLE_{loc_prefix}_{sec}',
            f'ID_UI_STAT_FORMAT_{loc_prefix}_{sec}_TITLE',
            f'ID_UI_STAT_FORMAT_{loc_prefix}_TITLE_{sec}',
            f'ID_UI_STAT_FORMAT_{loc_prefix}_{sec}_HUD',
            f'ID_UI_STAT_ATTRIBUTE_TRIGGER_SUBTITLE_{sec}',
        ]
        for k in candidates:
            if k in kv:
                return strip_loc_tags(kv[k])
        return None

    def get_display_name(sec: str) -> str:
        if sec == 'SIG':
            for sk in (f'ID_UI_{loc_prefix}_SIG_TITLE', f'ID_UI_STAT_FORMAT_{loc_prefix}_SIG_TITLE', f'ID_UI_STAT_ATTRIBUTE_{loc_prefix}_SIG_TITLE'):
                if sk in kv:
                    return f'シグネチャー - {strip_loc_tags(kv[sk])}'
            return 'シグネチャー'
        if sec == 'AA':
            return '常時発動'
        if sec == 'PASSIVE':
            return 'パッシブ'
        sp_idx = {'SP1': 0, 'SP_1': 0, 'SP2': 1, 'SP_2': 1, 'SP3': 2, 'SP_3': 2}
        if sec in sp_idx:
            idx = sp_idx[sec]
            sp_name = ""
            for prefix in search_prefixes:
                sp_key = f'ID_SPECIAL_ATTACK_{prefix}_{idx}'
                if sp_key in kv:
                    sp_name = strip_loc_tags(kv[sp_key])
                    break
            label = ('必殺技1', '必殺技2', '必殺技3')[idx]
            return f'{label}{" - " + sp_name if sp_name else ""}'
        if sec == 'HEAVY':
            return '強攻撃'
        loc_name = _lookup_sec_name(loc_prefix, sec)
        if loc_name:
            return loc_name
        if sec in SECTION_NAME_JP:
            return SECTION_NAME_JP[sec]
        if sec in {'KIN', 'REF', 'RMAT', 'SCRAP', 'SS', 'CRITS', 'FRNZY', 'REGEN', 'CALM', 'PREC'}:
            return '能力補足'
        return sec.replace('_', ' ').title()

    ORDER = {'SIG': 0, 'AA': 1, 'PASSIVE': 2, 'HEAVY': 80,
             'SP1': 91, 'SP_1': 91, 'SP2': 92, 'SP_2': 92, 'SP3': 93, 'SP_3': 93}
    result: list[tuple[str, list[str]]] = []
    for sec, items in sorted(fmt_keys.items(), key=lambda x: (ORDER.get(x[0], 50), x[0])):
        texts = [t for _, t in sorted(items)]
        texts = list(dict.fromkeys(texts))
        if texts:
            result.append((get_display_name(sec), texts))

    seen_titles = {title for title, _ in result}

    def add_legacy_signature(prefix: str) -> None:
        bases: list[str] = []
        exact = f'ID_UI_STAT_SIGNATURE_{prefix}_TITLE'
        if exact in kv:
            bases.append(f'ID_UI_STAT_SIGNATURE_{prefix}')
        marker = f'ID_UI_STAT_SIGNATURE_{prefix}_'
        for k in kv:
            if not k.startswith(marker) or not k.endswith('_TITLE') or k.endswith('_TITLE_LOWER'):
                continue
            base = k[:-len('_TITLE')]
            if base not in bases:
                bases.append(base)
        for base in bases:
            title = strip_loc_tags(kv.get(base + '_TITLE', 'シグネチャー'))
            display = f'シグネチャー - {title}'
            if display in seen_titles:
                continue
            texts = []
            for suffix in ('DESC', 'DESC_NEW', 'DESC_NEW2', 'DESC_B', 'SIMPLE'):
                key = f'{base}_{suffix}'
                if key in kv:
                    val = clean_value(kv[key])
                    if val and val not in texts:
                        texts.append(val)
            if texts:
                result.append((display, texts))
                seen_titles.add(display)

    def add_special_attacks(prefix: str) -> None:
        for idx, label in enumerate(('必殺技1', '必殺技2', '必殺技3')):
            name = strip_loc_tags(kv.get(f'ID_SPECIAL_ATTACK_{prefix}_{idx}', ''))
            desc = clean_value(kv.get(f'ID_SPECIAL_ATTACK_DESCRIPTION_{prefix}_{idx}', '')) if f'ID_SPECIAL_ATTACK_DESCRIPTION_{prefix}_{idx}' in kv else ''
            if not name and not desc:
                continue
            display = f'{label}{" - " + name if name else ""}'
            if display in seen_titles:
                continue
            result.append((display, [desc] if desc else [name]))
            seen_titles.add(display)

    for prefix in ([loc_prefix] if loc_prefix else []) + legacy_prefixes:
        if prefix:
            add_legacy_signature(prefix)
            add_special_attacks(prefix)

    return result


# ─── ゲームデータ読み込み ────────────────────────────────────
def load_abilities() -> tuple[dict, dict]:
    """abilities_all.json と slug_to_prefix.json を読み込む"""
    abilities: dict = {}
    slug_map: dict = {}
    if ABILITIES_PATH.exists():
        with open(ABILITIES_PATH, encoding="utf-8") as f:
            data = json.load(f)
            abilities = data.get("champions", {})
    if SLUG_MAP_PATH.exists():
        with open(SLUG_MAP_PATH, encoding="utf-8") as f:
            slug_map = json.load(f)
    print(f"ゲームアビリティデータ: {len(abilities)} プレフィックス / マッピング: {len(slug_map)} 件")
    return abilities, slug_map


SKIP_F2 = {
    "remove", "sequence", "dummy_ui", "dummy_hud", "dummy_timer", "dummy_egg",
    "dummy_icon", "dummy_callout", "dummy_trigger", "dummy_fxtrigger", "dummy_say",
    "dummy_info", "dummy_fx", "dummy_vfx", "dummy_cooldown", "dummy_range_hud",
    "dummy_easteregg", "set_var", "add_var", "set_appearance", "pause_id", "pause",
    "state_disable", "state_enable", "mod_id_percent", "mod_percent", "mod_id_flat",
    "duration_id_flat", "duration_id_percent", "duration_percent", "duration_flat",
    "chance_mod", "hp_min", "switch", "purge", "none", "hud_call", "info_page",
    "init_per_var", "init_cross_fight", "add_tel_var", "trigger_volume", "vfx",
    "lock_mod_id", "lock_mod", "lock_attribute", "clear_callout_id", "add_stack_limit",
    "get_buff_value_id", "ai_atk", "ai_sp1_bias", "ai_sp2_bias", "ai_sp3_bias",
    "ai_think", "ai_heavy_chance", "ai_profile_value", "ai_lvl3_enable", "ai_mana_cons",
    "block_stun", "hit_stun", "move_stun", "set_time_scale", "invert_controls_swipe",
    "jub_sp_frwrk", "refresh_id", "adjust_ticktime_id", "heavy_timeout",
    # ─ ダミー・UI系（追加）
    "dummy_appearance", "dummy_icon_1", "dummy_icon_2", "dummy_icon_obj",
    "dummy_ui_1", "dummy_ui_2", "dummy_hud_cnef", "dummy_hud_inv",
    "dummy_timer_cd", "dummy_timer_sig", "dummy_gr_icon", "dummy_text",
    "dummy_delay", "dummy_flag", "dummy_check", "dummy_camera_rdy",
    "ui_dummy", "mysto_dummy", "maw_dummy_ui",
    "hud_callout", "callout", "clear_callout", "immune_callout",
    "blct_card_hud", "culforce_hud", "mojo_prompt", "jjj_prompt",
    # ─ 内部処理系（追加）
    "get_buff_value", "set_trigger_volume_icon", "set_immune_id",
    "set_tag", "set_tel_var", "clear_var", "define_type_group",
    "mana_set", "hp_set", "fx_trig_list", "fx_trig_next", "fx_delay",
    "generic_remove", "share_stack_id", "toggle_ai", "adjust_ticktime",
    "none_timer", "reduce_cross_fight", "combo_telemetry", "trigger_seq_event",
    "hit_dmg_alt", "play_custom_matinee", "damage_type", "cooldown_timer",
    "scale", "disable_run",
    # ─ チャンピオン固有内部
    "shthra_dummy_egg", "shthra_dummy_wasp", "nico_pf", "pixie_cd",
    "nova_incin", "nova_force", "cgr_judgment", "hulkim_gamma",
    "spell_purple", "spell_orange", "spell_green",
    "ded_count", "ded_count_dn", "anti_ab",
    "cooldown_timer", "dummy_pi", "cleanse_delay",
}


def get_ability_effects(entries: list[dict], skip_types: set[str] | None = None) -> list[str]:
    """エントリ一覧から重複なしの日本語アビリティタイプを返す"""
    effective_skip = SKIP_F2 if skip_types is None else skip_types
    seen: list[str] = []
    seen_set: set[str] = set()
    for e in entries:
        raw = e.get("f2", "")
        if not raw or raw in effective_skip:
            continue
        jp = ABILITY_TYPE_JP.get(raw, raw)
        if jp not in seen_set:
            seen.append(jp)
            seen_set.add(jp)
    return seen


def _fmt_game_value(v, as_percent: bool = False) -> str:
    """ゲーム内数値を表示用に整える"""
    if v in (None, ""):
        return ""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return str(v)
    if as_percent:
        return f"{f * 100:g}%"
    return f"{f:g}"


def _entry_by_id(cats: dict, entry_id: str) -> dict:
    for entries in cats.values():
        for e in entries:
            if e.get("id") == entry_id:
                return e
    return {}


def _merged_ability_categories(abilities: dict, prefix: str) -> dict:
    cats = {
        cat: list(entries)
        for cat, entries in abilities.get(prefix, {}).get("categories", {}).items()
    }
    for extra_prefix in SUPPLEMENTAL_ABILITY_PREFIXES.get(prefix, ()):
        for cat, entries in abilities.get(extra_prefix, {}).get("categories", {}).items():
            cats.setdefault(cat, []).extend(entries)
    return cats


def _supplemental_ability_ids(abilities: dict, prefix: str) -> set[str]:
    ids: set[str] = set()
    for extra_prefix in SUPPLEMENTAL_ABILITY_PREFIXES.get(prefix, ()):
        for entries in abilities.get(extra_prefix, {}).get("categories", {}).values():
            for entry in entries:
                entry_id = entry.get("id", "")
                if entry_id:
                    ids.add(entry_id)
    return ids


def _prefer_rank_variant_entries(entries: list[dict]) -> list[dict]:
    """同一能力の通常版と5★カーブ版が同時にある場合は5★版を優先する。"""
    entry_ids = {entry.get("id", "") for entry in entries}
    result: list[dict] = []
    for entry in entries:
        entry_id = entry.get("id", "")
        if entry_id and f"{entry_id}_5s" in entry_ids:
            continue
        result.append(entry)
    return result


def _prefer_rank_variant_categories(cats: dict[str, list[dict]]) -> dict[str, list[dict]]:
    entry_ids = {
        entry.get("id", "")
        for entries in cats.values()
        for entry in entries
        if entry.get("id", "")
    }
    result: dict[str, list[dict]] = {}
    for cat, entries in cats.items():
        filtered = [
            entry for entry in entries
            if not (entry.get("id", "") and f'{entry.get("id", "")}_5s' in entry_ids)
        ]
        if filtered:
            result[cat] = filtered
    return result


def _core_game_categories(cats: dict[str, list[dict]], binary_id: str = "") -> dict[str, list[dict]]:
    """全prefixフォールバック時に、シナジー/小ネタ系の表示行を混ぜないよう絞る。"""
    result: dict[str, list[dict]] = {}
    for cat, entries in cats.items():
        filtered: list[dict] = []
        for entry in entries:
            entry_id = entry.get("id", "")
            owner = entry.get("f26", "")
            if "_syn_" in entry_id or "_sb_" in entry_id or "_egg_" in entry_id:
                continue
            if owner and binary_id and owner != binary_id:
                continue
            filtered.append(entry)
        if filtered:
            result[cat] = filtered
    return result


def _section_text_count(sections: list[tuple[str, list[str]]]) -> int:
    return sum(len(texts) for _, texts in sections)


def _has_non_special_section(sections: list[tuple[str, list[str]]]) -> bool:
    return any(not title.startswith("必殺技") for title, texts in sections if texts)


def _immune_badges_from_entry(entry: dict) -> list[str]:
    """BCGでpurify扱いの免疫エントリを、表示用の耐性名へ直す。"""
    ui_id = entry.get("f12", "")
    trigger = str(entry.get("f4", "")).lower()
    looks_immune = (
        "immune" in ui_id or
        "immunity" in ui_id or
        "imn" in ui_id or
        (entry.get("f2") == "purify" and trigger in {"onstart", "onbuffimmune"})
    )
    if not looks_immune:
        return []
    meta = f'{entry.get("f3", "")};{entry.get("f11", "")}'
    m = _re.search(r"(?:^|[;\s])type=([a-z0-9_,]+)", meta)
    if not m:
        return []
    badges: list[str] = []
    for raw in m.group(1).split(","):
        jp = ABILITY_TYPE_JP.get(f"{raw}_immune", "")
        if jp and jp not in badges:
            badges.append(jp)
    return badges


def _clean_game_text(value: str, entry: dict | None = None) -> str:
    value = strip_loc_tags(value).strip()
    if entry:
        if "{0}%" in value:
            value = value.replace("{0}%", _fmt_game_value(entry.get("f13"), True))
        if "{1}%" in value:
            value = value.replace("{1}%", _fmt_game_value(entry.get("f14"), True))
        try:
            duration = float(entry.get("f15", ""))
        except (TypeError, ValueError):
            duration = -1
        if duration >= 0:
            value = value.replace("{2}秒", f'{_fmt_game_value(duration)}秒')
    value = _re.sub(r'\{\d+\}', '〔数値〕', value)
    value = _re.sub(r'\s+', ' ', value)
    return value


def _entry_display_text(entry: dict, ui_index: dict[str, list[tuple[int, str]]],
                        kv: dict, prefer_simple: bool = False) -> tuple[str, list[str]]:
    """アビリティエントリのf12参照から、ゲーム内表示名と説明文を返す。"""
    ui_id = entry.get("f12", "")
    if not ui_id:
        return "", []
    fields = ui_index.get(ui_id, [])
    if not fields:
        return "", []

    title = ""
    title_tags = (0x12, 0x1a, 0x62)
    desc_tags = (0x22, 0x2a) if prefer_simple else (0x22,)

    for tag, key in fields:
        if tag not in title_tags or key not in kv:
            continue
        candidate = _clean_game_text(kv[key], entry)
        if candidate and len(candidate) < 70 and not any(mark in candidate for mark in ("。", "：", ":")):
            title = candidate
            break

    texts: list[str] = []
    for tag, key in fields:
        if tag not in desc_tags or key not in kv:
            continue
        text = _clean_game_text(kv[key], entry)
        if text and len(text) > 5 and text not in texts:
            texts.append(text)

    if not texts and not prefer_simple:
        for tag, key in fields:
            if tag != 0x2a or key not in kv:
                continue
            text = _clean_game_text(kv[key], entry)
            if text and len(text) > 5 and text not in texts:
                texts.append(text)

    return title, texts


def _signature_section_title(ui_id: str, ui_index: dict[str, list[tuple[int, str]]], kv: dict) -> str:
    candidates = [ui_id]
    base = ui_id
    while "_" in base:
        base = base.rsplit("_", 1)[0]
        candidates.append(base)

    for candidate in candidates:
        for tag, key in ui_index.get(candidate, []):
            if tag != 0x12 or key not in kv:
                continue
            title = _clean_game_text(kv[key])
            if title:
                return f"シグネチャー - {title}"
    return "シグネチャー"


def _special_attack_section_title(loc_prefixes: list[str], kv: dict, idx: int) -> str:
    label = ("必殺技1", "必殺技2", "必殺技3")[idx]
    for prefix in loc_prefixes:
        if not prefix:
            continue
        name = strip_loc_tags(kv.get(f"ID_SPECIAL_ATTACK_{prefix}_{idx}", ""))
        if name:
            return f"{label} - {name}"
    return label


def _special_attack_description(loc_prefixes: list[str], kv: dict, idx: int) -> str:
    for prefix in loc_prefixes:
        if not prefix:
            continue
        key = f"ID_SPECIAL_ATTACK_DESCRIPTION_{prefix}_{idx}"
        if key in kv:
            return _clean_game_text(kv[key])
    return ""


def _entry_special_indices(entry: dict) -> list[int]:
    """カテゴリ外にある必殺技連動エントリを、必殺技1/2/3へ振り分ける。"""
    haystack = " ".join(str(entry.get(k, "")) for k in ("f4", "f5", "f11")).lower()
    return [idx - 1 for idx in (1, 2, 3) if f"special{idx}" in haystack]


def _trigger_section_title(entry: dict) -> str:
    """結果エフェクト名ではなく、発動条件をタイトルにすべきエントリを判定する。"""
    trigger = " ".join(str(entry.get(k, "")) for k in ("f4", "f5")).lower()
    if "ontypeactivate" not in trigger:
        return ""
    meta = f'{entry.get("f3", "")};{entry.get("f11", "")}'
    m = _re.search(r"(?:^|[;\s])type=([a-z0-9_]+)", meta)
    if not m:
        return ""
    trigger_type = m.group(1)
    result_type = entry.get("f2", "")
    if not trigger_type or trigger_type == result_type:
        return ""
    jp = ABILITY_TYPE_JP.get(trigger_type, "")
    return f"{jp}時" if jp else ""


def _event_trigger_tokens(entry: dict) -> list[str]:
    """BCGエントリの発動イベント名を、表示に使う優先順で返す。"""
    first = str(entry.get("f4", "") or "")
    second = str(entry.get("f5", "") or "")
    first_lower = first.lower()
    generic_first = (
        first_lower in {"none", "onstart", "onabilityactivate", "ontypeactivate"} or
        first_lower.endswith(".ontypeactivate")
    )
    raw_tokens = [second, first] if second and generic_first else [first, second]
    result: list[str] = []
    for raw in raw_tokens:
        token = _re.sub(r"[^A-Za-z0-9]+", "", raw).upper()
        if token and token != "NONE" and token not in result:
            result.append(token)
    return result


def _localized_event_section_title(entry: dict, kv: dict) -> str:
    """ゲーム内ローカライズ済みの発動条件見出しを返す。"""
    for token in _event_trigger_tokens(entry):
        key = f"ID_UI_STAT_ATTRIBUTE_TRIGGER_SUBTITLE_{token}"
        if key in kv:
            title = strip_loc_tags(kv[key])
            if title:
                return title
    return ""


def _event_section_title(entry: dict, kv: dict) -> str:
    """ゲームUIで発動条件名として出る旧式エントリのタイトルを返す。"""
    loc_title = _localized_event_section_title(entry, kv)
    if loc_title:
        return loc_title

    trigger = " ".join(str(entry.get(k, "")) for k in ("f4", "f5")).lower()
    if "onlighthit" in trigger:
        return "弱攻撃"
    if "onmediumhit" in trigger:
        return "中攻撃"
    if "onheavyhit" in trigger:
        return "強攻撃"
    if "oncrit" in trigger:
        return "クリティカルヒット"
    if "onspecialhit" in trigger or "onspecialactivate" in trigger:
        return "必殺技"
    if "onhit" in trigger:
        return "全攻撃"
    if "onstruck" in trigger or "onattackreceived" in trigger:
        return "攻撃を受けたとき"
    if "onblock" in trigger:
        return "防御中"
    return ""


def _always_active_section_title(entry: dict) -> str:
    """ゲーム内の「常時発動」欄に相当する受動監視エントリを判定する。"""
    ui_id = entry.get("f12", "")
    if not ui_id or ui_id.startswith("sig_"):
        return ""
    trigger = str(entry.get("f4", "")).lower()
    meta = f'{entry.get("f3", "")};{entry.get("f11", "")}'.lower()
    if trigger == "onstart" and "modtype=" in meta and "passive" in meta:
        return "常時発動"
    return ""


def _all_attacks_section_title(entry: dict) -> str:
    """旧式UIで「全攻撃」枠に表示されるアビリティを判定する。"""
    if entry.get("id") == "abm_fry_i":
        return "全攻撃"
    return ""


def build_active_game_ability_sections(cats: dict, active_ids: set[str],
                                       kv: dict, loc_prefixes: list[str]) -> list[tuple[str, list[str]]]:
    """有効アビリティIDとUI参照から、ゲーム内能力説明を構築する。"""
    ui_index = load_bcg_ui_stat_index()
    active_cats: dict[str, list[dict]] = {}
    for cat, entries in cats.items():
        filtered = [e for e in entries if not active_ids or e.get("id") in active_ids]
        if filtered:
            active_cats[cat] = _prefer_rank_variant_entries(filtered)
    active_cats = _prefer_rank_variant_categories(active_cats)

    sections: list[tuple[str, list[str]]] = []
    seen_sections: set[tuple[str, str]] = set()

    def add_section(title: str, texts: list[str]) -> None:
        clean_texts = [t for t in texts if t]
        clean_texts = list(dict.fromkeys(clean_texts))
        if not title or not clean_texts:
            return
        for idx, (existing_title, existing_texts) in enumerate(sections):
            if existing_title != title:
                continue
            merged = existing_texts[:]
            for text in clean_texts:
                if text not in merged:
                    merged.append(text)
            sections[idx] = (existing_title, merged)
            return
        ident = (title, "\n".join(clean_texts))
        if ident in seen_sections:
            return
        sections.append((title, clean_texts))
        seen_sections.add(ident)

    # Signature entries may be in signature/ui/other depending on champion age.
    signature_texts_by_title: dict[str, list[str]] = {}
    for entries in active_cats.values():
        for entry in entries:
            ui_id = entry.get("f12", "")
            if not ui_id.startswith("sig_"):
                continue
            _, texts = _entry_display_text(entry, ui_index, kv)
            if not texts:
                continue
            display_title = _signature_section_title(ui_id, ui_index, kv)
            bucket = signature_texts_by_title.setdefault(display_title, [])
            for text in texts:
                if text not in bucket:
                    bucket.append(text)
    for title, texts in signature_texts_by_title.items():
        add_section(title, texts)

    normal_order = ("passive", "other", "heavy")
    normal_titles = {"passive": "パッシブ", "other": "", "heavy": "強攻撃"}
    for cat in normal_order:
        entries = active_cats.get(cat, [])
        if not entries:
            continue
        for entry in entries:
            if _entry_special_indices(entry):
                continue
            ui_id = entry.get("f12", "")
            if not ui_id or ui_id.startswith("sig_") or ui_id.endswith(("_hud", "_icon")):
                continue
            title, texts = _entry_display_text(entry, ui_index, kv)
            if not texts:
                continue
            section_title = _all_attacks_section_title(entry) or _always_active_section_title(entry) or _event_section_title(entry, kv) or _trigger_section_title(entry) or title or normal_titles.get(cat) or "能力補足"
            if cat in {"passive", "heavy"} and title and title not in section_title:
                texts = [f"{title}: {text}" for text in texts]
            add_section(section_title, texts)

    for cat, idx in (("special1", 0), ("special2", 1), ("special3", 2)):
        entries: list[dict] = []
        seen_entry_ids: set[str] = set()

        def add_special_entry(entry: dict) -> None:
            entry_id = entry.get("id", "")
            if entry_id and entry_id in seen_entry_ids:
                return
            if entry_id:
                seen_entry_ids.add(entry_id)
            entries.append(entry)

        for entry in active_cats.get(cat, []):
            add_special_entry(entry)
        for source_cat, source_entries in active_cats.items():
            if source_cat in {cat, "signature"}:
                continue
            for entry in source_entries:
                if idx in _entry_special_indices(entry):
                    add_special_entry(entry)

        title = _special_attack_section_title(loc_prefixes, kv, idx)
        texts: list[str] = []
        desc = _special_attack_description(loc_prefixes, kv, idx)
        if desc:
            texts.append(desc)
        for entry in entries:
            ui_id = entry.get("f12", "")
            if not ui_id or ui_id.startswith("sig_") or ui_id.endswith(("_hud", "_icon")):
                continue
            effect_title, effect_texts = _entry_display_text(entry, ui_index, kv)
            for text in effect_texts:
                line = f"{effect_title}: {text}" if effect_title else text
                if line not in texts:
                    texts.append(line)
        add_section(title, texts)

    return sections


def build_wolverine_game_ability_sections(cats: dict) -> list[tuple[str, list[str]]]:
    """Classic WolverineのBCGデータを、ゲーム内表記に近い説明へ整える"""
    bld = _entry_by_id(cats, "wlvrn_bld")
    regen_struck = _entry_by_id(cats, "wlvrn_rgn")
    regen_hit = _entry_by_id(cats, "wlvrn_rgn2")
    sp3_bleed = _entry_by_id(cats, "wlvrn_bld_s3")
    sig_regen = _entry_by_id(cats, "wlvrn_sigrgn")
    sig_regen_5s = _entry_by_id(cats, "wlvrn_sigrgn_5s")

    sections: list[tuple[str, list[str]]] = []
    if bld:
        sections.append(
            (
                "クリティカルヒット",
                [
                    f'クリティカルヒット時、{_fmt_game_value(bld.get("f13"), True)}の確率で'
                    f'{_fmt_game_value(bld.get("f15"))}秒間の流血を付与する。',
                    f'流血ダメージは攻撃力を参照し、係数は{_fmt_game_value(bld.get("f14"), True)}。',
                ],
            )
        )

    if regen_struck or regen_hit:
        hit_chance = _fmt_game_value(regen_hit.get("f13"), True) if regen_hit else ""
        struck_chance = _fmt_game_value(regen_struck.get("f13"), True) if regen_struck else ""
        duration = _fmt_game_value((regen_hit or regen_struck).get("f15"))
        potency = _fmt_game_value((regen_hit or regen_struck).get("f14"), True)
        sections.append(
            (
                "ヒーリングファクター",
                [
                    f'攻撃を当てた時は{hit_chance}、攻撃を受けた時は{struck_chance}の確率で再生を得る。',
                    f'再生は{duration}秒間持続し、最大体力と現在のパワー量を参照する。係数は{potency}。',
                ],
            )
        )

    if sp3_bleed:
        sections.append(
            (
                "必殺技3",
                [
                    f'ヒット時、{_fmt_game_value(sp3_bleed.get("f13"), True)}の確率で'
                    f'{_fmt_game_value(sp3_bleed.get("f15"))}秒間の流血を付与する。',
                    f'この流血は攻撃力を参照し、係数は{_fmt_game_value(sp3_bleed.get("f14"), True)}。',
                ],
            )
        )

    if sig_regen:
        sig_potency = _fmt_game_value(sig_regen.get("f14"), True)
        sig_potency_5s = _fmt_game_value(sig_regen_5s.get("f14"), True) if sig_regen_5s else sig_potency
        sections.append(
            (
                "シグネチャー補足",
                [
                    "覚醒後は攻撃を当てた時、または攻撃を受けた時に、追加の再生が発動する。",
                    f'発動率は{_fmt_game_value(sig_regen.get("f13"), True)}、持続時間は{_fmt_game_value(sig_regen.get("f15"))}秒。'
                    f'回復係数は通常{sig_potency}、5★用カーブでは{sig_potency_5s}。',
                ],
            )
        )

    return sections


def build_agent_venom_game_ability_sections(cats: dict) -> list[tuple[str, list[str]]]:
    """Agent VenomのBCGデータを、抜けの少ないゲーム内数値つき説明へ整える"""
    tenacity = _entry_by_id(cats, "agv_ten")
    stealth = _entry_by_id(cats, "agv_ea_ev")
    bleed = _entry_by_id(cats, "agv_bld_i")
    barrage = _entry_by_id(cats, "agv_bar")
    incinerate = _entry_by_id(cats, "agv_inc_i")
    incinerate_ui = _entry_by_id(cats, "agv_inc_ui_i")
    sp3_bleed_chance = _entry_by_id(cats, "agv_sp3_bldea")
    sig = _entry_by_id(cats, "agv_sig_ui")
    sig_fury = _entry_by_id(cats, "agv_sig_fury")
    sig_crit = _entry_by_id(cats, "agv_sig_crdm")

    sections: list[tuple[str, list[str]]] = []
    if sig:
        atk_potency = _fmt_game_value((sig_fury or sig).get("f14"), True)
        crit_potency = _fmt_game_value((sig_crit or sig).get("f14"), True)
        sections.append(
            (
                "シグネチャー - クリンターの憤怒",
                [
                    f'戦闘開始時、およびフラッシュが体力最大値の{_fmt_game_value(sig.get("f13"), True)}を失った時、'
                    f'クリンターの憤怒を発動する。',
                    f'発動中は攻撃力が{atk_potency}、クリティカルダメージ・レーティングが{crit_potency}上昇する。',
                    f'この効果はフラッシュが{_fmt_game_value(sig.get("f15"))}回攻撃を受けると失われる。',
                ],
            )
        )

    if tenacity:
        sections.append(
            (
                "執念",
                [
                    f'デバフを受けた時、{_fmt_game_value(tenacity.get("f13"), True)}の確率で'
                    f'浄化する。',
                ],
            )
        )

    if stealth:
        sections.append(
            (
                "シンビオートステルス",
                [
                    f'相手の回避スキル精度を{_fmt_game_value(abs(float(stealth.get("f14", 0))), True)}低下させる。',
                ],
            )
        )

    if bleed:
        sections.append(
            (
                "必殺技",
                [
                    f'必殺技の最後のヒット時、{_fmt_game_value(bleed.get("f13"), True)}の確率で'
                    f'{_fmt_game_value(bleed.get("f15"))}秒間の流血を付与する。',
                    f'この流血は攻撃力を参照し、係数は{_fmt_game_value(bleed.get("f14"), True)}。',
                ],
            )
        )

    if barrage:
        sections.append(
            (
                "必殺技1",
                [
                    f'この攻撃中、相手の回避率を{_fmt_game_value(abs(float(barrage.get("f14", 0))), True)}低下させる。',
                    f'効果時間は{_fmt_game_value(barrage.get("f15"))}秒。',
                ],
            )
        )

    if incinerate:
        incinerate_texts = [
            f'ヒット時、{_fmt_game_value(incinerate.get("f13"), True)}の確率で'
            f'{_fmt_game_value(incinerate.get("f15"))}秒間の焼却を付与する。',
            f'この焼却は攻撃力を参照し、係数は{_fmt_game_value(incinerate.get("f14"), True)}。',
        ]
        if incinerate_ui:
            incinerate_texts.append(
                f'焼却中はパーフェクトブロック・チャンスを無効化し、防御能力を'
                f'{_fmt_game_value(incinerate_ui.get("f13"), True)}低下させる。'
            )
        sections.append(
            (
                "必殺技2",
                incinerate_texts,
            )
        )

    if sp3_bleed_chance:
        sections.append(
            (
                "必殺技3",
                [
                    f'あらゆる流血効果の発動率が{_fmt_game_value(sp3_bleed_chance.get("f14"), True)}上昇する。',
                ],
            )
        )

    return sections


def build_abomination_game_ability_sections(cats: dict) -> list[tuple[str, list[str]]]:
    """Classic Abominationの旧式prefixを含むゲーム内能力を、UIの表示順に整える。"""
    ui_index = load_bcg_ui_stat_index()
    kv = load_localization()

    def texts_for(entry_id: str) -> list[str]:
        entry = _entry_by_id(cats, entry_id)
        if not entry:
            return []
        _, texts = _entry_display_text(entry, ui_index, kv)
        return texts

    sections: list[tuple[str, list[str]]] = []
    sig = _entry_by_id(cats, "abmntn_irradiate_5s") or _entry_by_id(cats, "abmntn_irradiate")
    if sig:
        sections.append(
            (
                _signature_section_title(sig.get("f12", ""), ui_index, kv),
                [
                    f'アボミネーションのガンマ線の体から繰り出される攻撃で、敵に'
                    f'〔数値〕%の確率で毒を付与し、体力回復を30%減少させ、'
                    f'直接ダメージを〔数値〕、{_fmt_game_value(sig.get("f15"))}秒間与える。'
                ],
            )
        )

    poison = _entry_by_id(cats, "abmntn_pois_i")
    if poison:
        sections.append(
            (
                "常時発動",
                [
                    f'アボミネーションが流血するたびに、流れ出た血が敵に'
                    f'{_fmt_game_value(poison.get("f13"), True)}の確率で毒を与え、'
                    f'直接ダメージを〔数値〕、{_fmt_game_value(poison.get("f15"))}秒間付与する。'
                ],
            )
        )

    fury = _entry_by_id(cats, "abm_fry_i")
    if fury:
        sections.append(
            (
                "全攻撃",
                [
                    f'{_fmt_game_value(fury.get("f13"), True)}の確率で激怒バフを'
                    f'{_fmt_game_value(fury.get("f15"))}秒間獲得し、攻撃力が+〔数値〕上昇する。'
                ],
            )
        )

    immune_texts = texts_for("abmntn_imn_psn")
    if immune_texts:
        sections.append(("常時発動", immune_texts))

    return sections


def build_antman_game_ability_sections(cats: dict) -> list[tuple[str, list[str]]]:
    """Classic Ant-Manの現行antuデータを、ゲーム内UIの能力欄に近い構成へ整える。"""
    ui_index = load_bcg_ui_stat_index()
    kv = load_localization()

    def texts_for(entry_id: str) -> list[str]:
        entry = _entry_by_id(cats, entry_id)
        if not entry:
            return []
        _, texts = _entry_display_text(entry, ui_index, kv)
        if entry_id in {"antu_imn_buff_ui", "antu_sp1_pymp"}:
            texts = [text.replace("〔数値〕", _fmt_game_value(entry.get("f14")), 1) for text in texts]
            texts = [text.replace("ピム粒子を1生成", "ピム粒子を1個生成").replace("ピム粒子を3得る", "ピム粒子を3個得る") for text in texts]
        return texts

    def loc_text(key: str, entry_id: str = "") -> str:
        value = kv.get(key, "")
        if not value:
            return ""
        entry = _entry_by_id(cats, entry_id) if entry_id else None
        return _clean_game_text(value, entry or None)

    def add_section(sections: list[tuple[str, list[str]]], title: str, texts: list[str]) -> None:
        clean_texts = list(dict.fromkeys([t for t in texts if t]))
        if clean_texts:
            sections.append((title, clean_texts))

    sections: list[tuple[str, list[str]]] = []

    sig_title = loc_text("ID_UI_ATTRINUTE_ANTU_SIG_TITLE") or "シグネチャー"
    add_section(
        sections,
        f"シグネチャー - {sig_title}",
        texts_for("antu_sig_fat_5") + texts_for("antu_sig_pymp_pause_5"),
    )

    add_section(
        sections,
        "常時発動",
        texts_for("antu_imn_dot") + texts_for("antu_imn_buff_ui"),
    )

    pym_title = loc_text("ID_UI_STAT_ATTRIBUTE_TRIGGER_SUBTITLE_PYMPARTICLE") or "ピム粒子"
    add_section(
        sections,
        pym_title,
        [
            loc_text("ID_PYMP_D", "antu_pymp"),
            *texts_for("antu_rfrsh_int"),
            *texts_for("antu_pwr_stng_ui"),
            *texts_for("antu_pwr_stng_bns"),
        ],
    )

    add_section(
        sections,
        "必殺技発動時",
        texts_for("antu_sp_unsteady") + texts_for("antu_unst_miss") + texts_for("antu_sp_unsteady_cd"),
    )

    add_section(
        sections,
        "必殺技1",
        texts_for("antu_sp1_pymp") + texts_for("antu_sp1_fatigue"),
    )

    add_section(
        sections,
        "必殺技2",
        texts_for("antu_sp2_dmg") + texts_for("antu_sp2_psn"),
    )

    add_section(
        sections,
        "必殺技3",
        texts_for("antu_sp3_ptrfy"),
    )

    return sections


def build_game_ability_sections_html(sections: list[tuple[str, list[str]]]) -> str:
    """能力説明を単一の「能力」アコーディオン内に平坦表示する"""
    if not sections:
        return ""

    groups: list[str] = []
    for title, texts in sections:
        text_li = "".join(f'<li>{t}</li>' for t in texts if t)
        if not text_li:
            continue
        groups.append(
            f'<div class="gd-ability-group">'
            f'<div class="gd-ability-title">{title}</div>'
            f'<ul class="gd-texts">{text_li}</ul>'
            f'</div>'
        )

    if not groups:
        return ""
    return (
        '<div class="gd-descs">'
        '<details class="gd-detail gd-ability-detail">'
        '<summary>能力</summary>'
        f'<div class="gd-ability-groups">{"".join(groups)}</div>'
        '</details>'
        '</div>'
    )


def build_game_data_html(slug: str, abilities: dict, slug_map: dict,
                          loc_prefix_map: dict | None = None,
                          kv: dict | None = None,
                          legacy_loc_prefixes: list[str] | None = None,
                          binary_id: str = "") -> str:
    """チャンピオンのゲーム内アビリティデータセクションHTML（mcoc.gg形式）"""
    prefix = slug_map.get(slug)
    loc_prefix = loc_prefix_map.get(slug, "") if loc_prefix_map else ""
    loc_prefixes = [p for p in [loc_prefix] + (legacy_loc_prefixes or []) if p]
    if not prefix or prefix not in abilities:
        sections = get_champion_sections(loc_prefix, kv, legacy_loc_prefixes) if kv else []
        sections_html = build_game_ability_sections_html(sections)
        if not sections_html:
            return ""
        return f"""<div class="gd-sec">
  {sections_html}
</div>"""

    cats = _merged_ability_categories(abilities, prefix)
    active_by_binary, active_by_prefix = load_bcg_active_ability_ids(abilities)
    active_ids = set(active_by_binary.get(binary_id, set()) or active_by_prefix.get(prefix, set()))
    active_ids.update(_supplemental_ability_ids(abilities, prefix))
    active_cats = {
        cat: _prefer_rank_variant_entries([entry for entry in entries if not active_ids or entry.get("id") in active_ids])
        for cat, entries in cats.items()
    }
    active_cats = _prefer_rank_variant_categories(active_cats)

    # ローカライズ説明セクション。BCGの有効ID検出がプリファイトなどに寄って
    # 本体能力を落とす場合だけ、同じゲーム内prefixの全表示行へフォールバックする。
    sections: list[tuple[str, list[str]]] = []
    section_cats = active_cats
    manual_section_builder = {
        "game-roster-abomination": build_abomination_game_ability_sections,
        "game-roster-ant-man": build_antman_game_ability_sections,
        "game-roster-wolverine": build_wolverine_game_ability_sections,
        "game-roster-agent-venom": build_agent_venom_game_ability_sections,
    }.get(slug)
    if manual_section_builder:
        sections = manual_section_builder(cats)
        manual_badge_ids = {
            "game-roster-ant-man": {
                "antu_sig_fat_5",
                "antu_sig_pymp_pause_5",
                "antu_imn_dot",
                "antu_imn_buff_ui",
                "antu_pymp",
                "antu_rfrsh_int",
                "antu_pwr_stng",
                "antu_pwr_stng_ui",
                "antu_pwr_stng_bns",
                "antu_sp_unsteady",
                "antu_sp_glance",
                "antu_unst_miss",
                "antu_sp_unsteady_cd",
                "antu_sp1_pymp",
                "antu_sp1_unblck",
                "antu_sp1_fatigue",
                "antu_sp2_dmg",
                "antu_sp2_psn",
                "antu_sp3_ptrfy",
            },
        }.get(slug)
        if manual_badge_ids:
            section_cats = {
                cat: [entry for entry in entries if entry.get("id") in manual_badge_ids]
                for cat, entries in cats.items()
            }
    elif kv and loc_prefix_map:
        sections = build_active_game_ability_sections(active_cats, active_ids, kv, loc_prefixes)
        if (
            not sections or
            (active_ids and (len(active_ids) < 4 or not _has_non_special_section(sections)))
        ):
            fallback_cats = _prefer_rank_variant_categories(_core_game_categories(cats, binary_id))
            fallback_sections = build_active_game_ability_sections(fallback_cats, set(), kv, loc_prefixes)
            if _section_text_count(fallback_sections) > _section_text_count(sections):
                section_cats = fallback_cats
                sections = fallback_sections
        if not sections and (loc_prefix or legacy_loc_prefixes):
            sections = get_champion_sections(loc_prefix, kv, legacy_loc_prefixes)

    # 全カテゴリの entries を優先順で結合
    all_entries: list[dict] = []
    for cat in ("signature", "passive", "other", "heavy", "special1", "special2", "special3"):
        all_entries.extend(section_cats.get(cat, []))

    # 重複なしでf2タイプを収集（buff/debuff/immune に分類）
    seen_set: set[str] = set()
    buff_badges:   list[str] = []
    debuff_badges: list[str] = []
    immune_badges: list[str] = []
    other_badges:  list[str] = []
    ui_index = load_bcg_ui_stat_index()

    for e in all_entries:
        immune_jps = _immune_badges_from_entry(e)
        if immune_jps:
            for immune_jp in immune_jps:
                if immune_jp not in seen_set:
                    seen_set.add(immune_jp)
                    immune_badges.append(immune_jp)
            continue
        if not e.get("f12"):
            continue
        raw = e.get("f2", "")
        if not raw or raw in SKIP_F2:
            continue
        jp = ABILITY_TYPE_JP.get(raw, None)
        display_title = ""
        if kv:
            display_title, _ = _entry_display_text(e, ui_index, kv)
        if display_title in BUFF_LABELS_JP or display_title in DEBUFF_LABELS_JP:
            jp = display_title
        if jp is None:
            continue
        if jp in seen_set:
            continue
        seen_set.add(jp)
        if raw.endswith("_immune") or raw.endswith("_immunity"):
            immune_badges.append(jp)
        elif jp in BUFF_LABELS_JP or raw in BUFF_TYPES:
            buff_badges.append(jp)
        elif jp in DEBUFF_LABELS_JP or raw in DEBUFF_TYPES:
            debuff_badges.append(jp)
        else:
            other_badges.append(jp)

    def badges(items: list[str], css: str) -> str:
        return "".join(f'<span class="abi-badge {css}">{jp}</span>' for jp in items)

    all_badges_html = (
        badges(buff_badges,   "abi-buff") +
        badges(debuff_badges, "abi-debuff") +
        badges(other_badges,  "abi-neutral")
    )

    # 免疫・耐性セクション
    immune_html = ""
    if immune_badges:
        imm = badges(immune_badges, "abi-immune")
        immune_html = (
            '<div class="gd-immune">'
            '<span class="gd-sublabel">耐性</span>'
            f'<div class="gd-badges">{imm}</div>'
            '</div>'
        )

    sections_html = build_game_ability_sections_html(sections)
    abilities_html = (
        '<div class="gd-abilities">\n'
        '    <span class="gd-sublabel">アビリティ</span>\n'
        f'    <div class="gd-badges">{all_badges_html}</div>\n'
        '  </div>'
        if all_badges_html else ""
    )

    if not (abilities_html or immune_html or sections_html):
        return ""

    return f"""<div class="gd-sec">
  {abilities_html}
  {immune_html}
  {sections_html}
</div>"""


def load_champion_class_map() -> dict[str, str]:
    """BCG抽出済みの champion_classes.txt から binary_id → class を返す"""
    if not CHAMPION_CLASSES_PATH.exists():
        return {}
    header_to_class = {
        "SCIENCE": "Science",
        "MUTANT": "Mutant",
        "SKILL": "Skill",
        "COSMIC": "Cosmic",
        "TECH": "Tech",
        "MYSTIC": "Mystic",
    }
    class_map: dict[str, str] = {}
    current_class = ""
    for line in CHAMPION_CLASSES_PATH.read_text(encoding="utf-8").splitlines():
        m = _re.match(r"\[([A-Z]+)\]", line)
        if m:
            current_class = header_to_class.get(m.group(1), "")
            continue
        value = line.strip()
        if current_class and _re.match(r"^[a-z0-9_]+$", value):
            class_map[value] = current_class
    print(f"ゲーム内クラス定義: {len(class_map)} 件")
    return class_map


def _norm_champion_key(value: str) -> str:
    return _re.sub(r"[^a-z0-9]+", "", (value or "").lower())


def _summary_name_keys(value: str) -> set[str]:
    key = _norm_champion_key(value)
    keys = {key} if key else set()
    if key.endswith("variant"):
        keys.add(key[:-len("variant")])
    return {k for k in keys if k}


def _legacy_loc_prefix_from_binary_id(binary_id: str) -> str:
    return _re.sub(r"[^A-Z0-9]+", "", binary_id.upper())


def _strong_prefix_abbreviations(legacy_prefix: str) -> set[str]:
    letters = _re.sub(r"[^A-Z0-9]+", "", legacy_prefix.upper())
    if not letters:
        return set()
    no_vowels = letters[0] + _re.sub(r"[AEIOUY]", "", letters[1:])
    values = {no_vowels.lower()}
    if len(letters) > 4:
        values.add((letters[0] + letters[-4:]).lower())
    return {v for v in values if v}


def load_champion_summary_prefix_map(abilities: dict) -> dict[str, str]:
    """ゲーム抽出済みsummaryの表示名から、能力prefixを引けるようにする。"""
    if not CHAMPIONS_SUMMARY_PATH.exists():
        return {}
    candidates: dict[str, set[str]] = {}
    for line in CHAMPIONS_SUMMARY_PATH.read_text(encoding="utf-8").splitlines():
        parts = _re.split(r"\s{2,}", line.strip())
        if len(parts) < 3:
            continue
        name, prefix = parts[0], parts[1]
        if name == "(不明)" or prefix not in abilities:
            continue
        for key in _summary_name_keys(name):
            candidates.setdefault(key, set()).add(prefix)
    return {
        key: next(iter(prefixes))
        for key, prefixes in candidates.items()
        if len(prefixes) == 1
    }


def load_ability_prefix_loc_tokens(abilities: dict) -> dict[str, dict[str, int]]:
    """能力prefixごとに、参照しているUIローカライズprefixを集める。"""
    ui_index = load_bcg_ui_stat_index()
    token_re = _re.compile(r"ID_(?:UI_)?STAT(?:_ATTRIBUTE|_FORMAT|_SIGNATURE)?_([A-Z0-9]+)")
    result: dict[str, dict[str, int]] = {}
    for prefix, data in abilities.items():
        counts: dict[str, int] = {}
        for entries in data.get("categories", {}).values():
            for entry in entries:
                for _, key in ui_index.get(entry.get("f12", ""), []):
                    for match in token_re.finditer(key):
                        token = match.group(1)
                        counts[token] = counts.get(token, 0) + 1
        if counts:
            result[prefix] = counts
    return result


def infer_prefix_from_loc_tokens(binary_id: str, prefix_tokens: dict[str, dict[str, int]]) -> str:
    """binary_idとUIローカライズprefixの一致から、曖昧でない能力prefixだけ推定する。"""
    legacy = _legacy_loc_prefix_from_binary_id(binary_id)
    strong_abbrs = _strong_prefix_abbreviations(legacy)
    scores: list[tuple[int, str]] = []
    for prefix, token_counts in prefix_tokens.items():
        score = 0
        for token, count in token_counts.items():
            if token == legacy:
                score = max(score, 100 + count)
            elif len(token) >= 5 and legacy.startswith(token):
                score = max(score, 40 + count)
        if prefix in strong_abbrs:
            score = max(score, 85)
        if score:
            scores.append((score, prefix))
    if not scores:
        return ""
    scores.sort(reverse=True)
    best_score, best_prefix = scores[0]
    second_score = scores[1][0] if len(scores) > 1 else 0
    if best_score >= 85 and best_score - second_score >= 10:
        return best_prefix
    return ""


def load_binary_prefix_map(abilities: dict | None = None) -> dict[str, str]:
    """既存のゲーム抽出マップから binary_id → ability_prefix を作る"""
    binary_to_prefix: dict[str, str] = {}

    slug_to_prefix: dict[str, str] = {}
    if SLUG_MAP_PATH.exists():
        with open(SLUG_MAP_PATH, encoding="utf-8") as f:
            slug_to_prefix = json.load(f)

    slug_to_jp: dict[str, dict] = {}
    if NAME_JP_PATH.exists():
        with open(NAME_JP_PATH, encoding="utf-8") as f:
            slug_to_jp = json.load(f)

    for slug, info in slug_to_jp.items():
        prefix = slug_to_prefix.get(slug, "")
        binary_id = info.get("binary_id", "") if isinstance(info, dict) else ""
        if binary_id and prefix:
            binary_to_prefix[binary_id] = prefix

    if abilities:
        summary_prefix_map = load_champion_summary_prefix_map(abilities)
        prefix_tokens = load_ability_prefix_loc_tokens(abilities)
        if CHAMP_NAMES_PATH.exists():
            champion_name_data = json.loads(CHAMP_NAMES_PATH.read_text(encoding="utf-8"))
            for binary_id, info in champion_name_data.items():
                if binary_id in binary_to_prefix:
                    continue
                keys = _summary_name_keys(info.get("en", "")) | {_norm_champion_key(binary_id)}
                for key in keys:
                    prefix = summary_prefix_map.get(key, "")
                    if prefix:
                        binary_to_prefix[binary_id] = prefix
                        break
                if binary_id not in binary_to_prefix:
                    prefix = infer_prefix_from_loc_tokens(binary_id, prefix_tokens)
                    if prefix:
                        binary_to_prefix[binary_id] = prefix

    for binary_id, prefix in AUTO_BINARY_TO_PREFIX.items():
        if not abilities or prefix in abilities:
            binary_to_prefix[binary_id] = prefix

    binary_to_prefix.update(MANUAL_BINARY_TO_PREFIX)
    return binary_to_prefix


def _slug_from_binary_id(binary_id: str) -> str:
    return "game-roster-" + binary_id.replace("_", "-")


def _portrait_key(value: str) -> str:
    return _re.sub(r'[^a-z0-9]', '', value.lower())


def _name_from_binary_id(binary_id: str) -> str:
    return " ".join(part.upper() if part in {"x", "x23"} else part.capitalize() for part in binary_id.split("_"))


def load_direct_portrait_map() -> dict[str, str]:
    """portrait_{binary_id}.png があるものを binary_id → filename で返す"""
    portrait_dir = BASE / "data" / "portraits"
    if not portrait_dir.exists():
        return {}
    result: dict[str, str] = {}
    for path in portrait_dir.glob("portrait_*.png"):
        binary_id = path.stem[len("portrait_"):]
        result[binary_id.lower()] = path.name
        result.setdefault(_portrait_key(binary_id), path.name)
    return result


def load_game_only_champions(abilities: dict, kv: dict, name_jp_map: dict) -> tuple[list[dict], dict, dict]:
    """スポットライトCSVを使わず、ゲーム内抽出データだけでチャンピオン一覧を構築する"""
    class_map = load_champion_class_map()
    binary_to_prefix = load_binary_prefix_map(abilities)
    direct_portraits = load_direct_portrait_map()
    champion_name_data: dict = {}
    if CHAMP_NAMES_PATH.exists():
        champion_name_data = json.loads(CHAMP_NAMES_PATH.read_text(encoding="utf-8"))

    champions: list[dict] = []
    slug_map: dict[str, str] = {}
    portrait_map: dict[str, str] = {}
    used_prefixes: set[str] = set()
    used_names: set[str] = set()

    extra_champions = load_game_roster_champions(abilities, kv)
    for c in extra_champions:
        c["source"] = "game_roster"
        champions.append(c)
        slug = c.get("slug", "")
        prefix = c.get("ability_prefix", "")
        if prefix:
            slug_map[slug] = prefix
            used_prefixes.add(prefix)
        if c.get("portrait"):
            portrait_map[slug] = c["portrait"]
        extra_binary_id = c.get("binary_id", "") or (
            slug.removeprefix("game-roster-").replace("-", "_") if slug.startswith("game-roster-") else prefix
        )
        name_jp_map[slug] = {"jp": c.get("name_jp", ""), "en": c.get("name", ""), "binary_id": extra_binary_id}
        used_names.add((c.get("name_jp") or c.get("name") or "").lower())

    for binary_id, cls in sorted(class_map.items()):
        if not is_playable_binary_id(binary_id):
            continue
        prefix = binary_to_prefix.get(binary_id, "")
        if prefix and prefix in used_prefixes and binary_id not in ALLOW_DUPLICATE_PREFIX_BINARY_IDS:
            continue

        name_info = champion_name_data.get(binary_id, {})
        name_jp = name_info.get("jp", "")
        name_en = name_info.get("en", "") or _name_from_binary_id(binary_id)
        dedupe_name = (name_jp or name_en).lower()
        if dedupe_name in used_names:
            continue

        portrait = direct_portraits.get(binary_id.lower(), "") or direct_portraits.get(_portrait_key(binary_id), "")
        if not (name_jp or name_en or prefix or portrait):
            continue

        slug = _slug_from_binary_id(binary_id)
        champ = {
            "slug": slug,
            "name": name_en,
            "name_jp": name_jp,
            "champion_class": cls,
            "release_date": "",
            "portrait": portrait,
            "ability_prefix": prefix,
            "loc_prefix": "",
            "legacy_loc_prefixes": [_legacy_loc_prefix_from_binary_id(binary_id)],
            "source": "game_roster",
        }
        champions.append(champ)
        used_names.add(dedupe_name)
        if prefix:
            slug_map[slug] = prefix
            used_prefixes.add(prefix)
        if portrait:
            portrait_map[slug] = portrait
        name_jp_map[slug] = {"jp": name_jp, "en": name_en, "binary_id": binary_id}

    print(f"ゲーム内チャンピオン一覧: {len(champions)} 件")
    return champions, slug_map, portrait_map



def load_game_roster_champions(abilities: dict, kv: dict) -> list[dict]:
    """公式CSVにないプレイアブル勢をゲーム内データから補完する"""
    if not EXTRA_CHAMPIONS_PATH.exists():
        return []
    with open(EXTRA_CHAMPIONS_PATH, encoding="utf-8") as f:
        records = json.load(f)
    champs: list[dict] = []
    for record in records:
        c = dict(record)
        champs.append(c)
    print(f"ゲーム内補完チャンピオン: {len(champs)} 件")
    return champs


def build_cards(champions: list[dict], cache: dict,
                abilities: dict | None = None, slug_map: dict | None = None,
                name_jp_map: dict | None = None,
                loc_prefix_map: dict | None = None,
                kv: dict | None = None,
                portrait_map: dict | None = None) -> str:
    html_parts = []
    abilities      = abilities      or {}
    slug_map       = slug_map       or {}
    name_jp_map    = name_jp_map    or {}
    loc_prefix_map = loc_prefix_map or {}
    kv             = kv             or {}
    portrait_map   = portrait_map   or {}

    # JP champion name -> portrait filename (normalized, for synergy partner lookup via loc DESC)
    def _norm_jp(s: str) -> str:
        import re as _re2
        return _re2.sub(r'[・\s（）()\[\]【】\-－]', '', s).lower()

    _norm_to_portrait: dict[str, str] = {}
    _name_to_binary: dict[str, str] = {}
    _names_data: dict = {}
    _direct_portraits = load_direct_portrait_map()
    if CHAMP_NAMES_PATH.exists():
        import json as _json2
        _names_data = _json2.loads(CHAMP_NAMES_PATH.read_text(encoding='utf-8'))
        for _bid, _info in _names_data.items():
            for _name_value in (_info.get('jp', ''), _info.get('en', '')):
                _name_norm = _norm_jp(_name_value)
                if _name_norm:
                    _name_to_binary[_name_norm] = _bid
            _jp = _info.get('jp', '')
            _fname = _direct_portraits.get(_bid.lower(), '') or _direct_portraits.get(_portrait_key(_bid), '')
            if _jp and _fname:
                _norm_to_portrait[_norm_jp(_jp)] = _fname
    _game_synergy_defs, _game_synergies_by_binary = load_bcg_synergy_index()

    def _binary_id_for_card(c: dict, name_jp: str, name_en: str) -> str:
        slug = c.get("slug", "")
        candidates = [
            c.get("binary_id", ""),
            name_jp_map.get(slug, {}).get("binary_id", ""),
            slug.removeprefix("game-roster-").replace("-", "_") if slug.startswith("game-roster-") else "",
            _name_to_binary.get(_norm_jp(name_jp), ""),
            _name_to_binary.get(_norm_jp(name_en), ""),
        ]
        for candidate in candidates:
            if candidate and candidate in _game_synergies_by_binary:
                return candidate
        return next((candidate for candidate in candidates if candidate), "")

    def _portrait_for_binary_id(binary_id: str) -> str:
        if not binary_id:
            return ""
        info = _names_data.get(binary_id, {}) if isinstance(_names_data, dict) else {}
        return (
            _direct_portraits.get(binary_id.lower(), "") or
            _direct_portraits.get(_portrait_key(binary_id), "") or
            _norm_to_portrait.get(_norm_jp(info.get("jp", "")), "")
        )

    def _game_synergy_entries_for_binary(binary_id: str) -> list[tuple[str, str, list[str]]]:
        entries: list[tuple[str, str, list[str]]] = []
        for sid in _game_synergies_by_binary.get(binary_id, []):
            defn = _game_synergy_defs.get(sid, {})
            title = strip_loc_tags(kv.get(defn.get("title_key", ""), defn.get("title_key", sid)))
            raw_desc = kv.get(defn.get("desc_key", ""), defn.get("desc_key", ""))
            desc = clean_synergy_desc(raw_desc).replace("\n", "<br>") if raw_desc else ""
            portraits: list[str] = []
            seen_bases: set[str] = set()
            for variant_id in defn.get("variants", []):
                base_id = _variant_base_id(variant_id)
                if base_id == binary_id or base_id in seen_bases or not is_playable_binary_id(base_id):
                    continue
                seen_bases.add(base_id)
                portrait = _portrait_for_binary_id(base_id)
                if portrait:
                    portraits.append(portrait)
            if title and (desc or portraits):
                entries.append((title, desc, portraits))
        return entries

    _known_synergy_names: list[tuple[str, str, str, str]] = []
    _seen_known_names: set[tuple[str, str]] = set()

    def _add_known_name(match_name: str, card_name: str, portrait: str) -> None:
        match_norm = _norm_jp(match_name)
        card_norm = _norm_jp(card_name)
        if not match_norm or not card_norm:
            return
        key = (match_norm, card_norm)
        if key in _seen_known_names:
            return
        _known_synergy_names.append((match_norm, card_norm, card_name, portrait))
        _seen_known_names.add(key)

    for _c in champions:
        _slug = _c.get("slug", "")
        _jp = _c.get("name_jp", "") or name_jp_map.get(_slug, {}).get("jp", "")
        if not _jp:
            continue
        _portrait = _c.get("portrait", "") or portrait_map.get(_slug, "")
        if _portrait:
            _norm_to_portrait[_norm_jp(_jp)] = _portrait
        _add_known_name(_jp, _jp, _portrait)
        _base_jp = _re.sub(r'[（(].*$', '', _jp).strip()
        if _base_jp and _base_jp != _jp:
            _add_known_name(_base_jp, _jp, _portrait)

    # シナジー説明には、カード一覧に未収録でもゲーム内名と画像が存在する
    # プレイアブルチャンピオンが出ることがある。
    if CHAMP_NAMES_PATH.exists():
        for _bid, _info in _names_data.items():
            if not is_playable_binary_id(_bid):
                continue
            _jp = _info.get('jp', '')
            _portrait = _direct_portraits.get(_bid.lower(), '') or _direct_portraits.get(_portrait_key(_bid), '')
            if not _jp or not _portrait:
                continue
            _add_known_name(_jp, _jp, _portrait)
            _base_jp = _re.sub(r'[（(].*$', '', _jp).strip()
            if _base_jp and _base_jp != _jp:
                _add_known_name(_base_jp, _jp, _portrait)

    _known_synergy_names.sort(key=lambda item: len(item[0]), reverse=True)

    def _names_in_synergy_label(label: str) -> list[tuple[str, str, str]]:
        label_norm = _norm_jp(label)
        if not label_norm:
            return []
        boundary_chars = set('、,，/&＆+と')
        occupied = [False] * len(label_norm)
        matches: list[tuple[str, str, str]] = []
        seen_cards: set[str] = set()
        for match_norm, card_norm, card_name, portrait in _known_synergy_names:
            start = label_norm.find(match_norm)
            while start >= 0:
                end = start + len(match_norm)
                has_boundary = (
                    len(match_norm) > 3 or
                    ((start == 0 or label_norm[start - 1] in boundary_chars) and
                     (end == len(label_norm) or label_norm[end] in boundary_chars))
                )
                if has_boundary and not any(occupied[start:end]) and card_norm not in seen_cards:
                    for i in range(start, end):
                        occupied[i] = True
                    matches.append((card_norm, card_name, portrait))
                    seen_cards.add(card_norm)
                    break
                start = label_norm.find(match_norm, start + 1)
        return matches

    _syn_by_name: dict[str, list[tuple[str, str, list[str]]]] = {}
    if kv:
        for _entry in collect_localized_synergy_entries(kv):
            _matched: list[tuple[str, str, str]] = []
            _seen_matched: set[str] = set()
            for _label in _entry.get('partners', []):
                for _card_norm, _card_name, _portrait in _names_in_synergy_label(_label):
                    if _card_norm in _seen_matched:
                        continue
                    _matched.append((_card_norm, _card_name, _portrait))
                    _seen_matched.add(_card_norm)
            if not _matched:
                continue
            _partner_names = [_card_name for _, _card_name, _ in _matched]
            for _card_norm, _, _ in _matched:
                _syn_by_name.setdefault(_card_norm, []).append((
                    _entry['title'],
                    _entry['desc'],
                    _partner_names,
                ))

    # slug -> list of partner-portrait-lists, one per synergy entry (in order).
    # ローカライズ本文のパートナー名からポートレートを解決する。
    _slug_syn_portraits: dict[str, list[list[str]]] = {}

    for c in champions:
        slug        = c["slug"]
        name_en     = c["name"]
        name_jp     = c.get("name_jp", "") or name_jp_map.get(slug, {}).get("jp", "")
        cls         = c.get("champion_class", "")
        release     = c.get("release_date", "")
        trans       = cache.get(slug, {})

        # アトリビュート
        raw_attr = c.get("champion_attributes", "")
        attrs = [
            a.strip()
            for a in raw_attr.split("|")
            if a.strip() and "LEARN MORE" not in a
        ]

        # カラー・表示名
        color    = CLASS_COLORS.get(cls, "#607D8B")
        class_jp = CLASS_JP.get(cls, cls)
        # 表示名：日本語名 + 英語名（サブタイトル）
        name = name_jp if name_jp else name_en

        # アトリビュートバッジ
        attr_html = "".join(
            f'<span class="attr-badge">{ATTR_JP.get(a, a)}</span>'
            for a in attrs
        )

        # シナジー
        binary_id = _binary_id_for_card(c, name_jp, name_en)
        syn_list: list[tuple[str, str, list[str]]] = _game_synergy_entries_for_binary(binary_id)

        if not syn_list:
            syn_raw  = c.get("synergy_bonuses", "")
            syn_list_en = [s.strip() for s in syn_raw.split("|") if s.strip()] if syn_raw else []

            loc_prefix = loc_prefix_map.get(slug, "") or c.get("loc_prefix", "")
            loc_syn_names: list[tuple[str, str, list[str]]] = []
            syn_prefixes = [loc_prefix] + c.get("legacy_loc_prefixes", [])
            if "WOLVERINE" in syn_prefixes:
                syn_prefixes.append("WOLV")
            seen_loc_syn: set[str] = set()
            if kv:
                for syn_prefix in syn_prefixes:
                    if not syn_prefix:
                        continue
                    for title, desc, partners in get_champion_synergies_jp(syn_prefix, kv):
                        ident = title + '\n' + desc
                        if ident in seen_loc_syn:
                            continue
                        loc_syn_names.append((title, desc, partners))
                        seen_loc_syn.add(ident)
                for title, desc, partners in _syn_by_name.get(_norm_jp(name_jp), []):
                    ident = title + '\n' + desc
                    if ident in seen_loc_syn:
                        continue
                    loc_syn_names.append((title, desc, partners))
                    seen_loc_syn.add(ident)

            # syn_list: list of (title_str, desc_str, partner_portrait_fnames)
            db_portraits = _slug_syn_portraits.get(slug, [])   # per-synergy partner lists from DB
            db_all_idx = 0   # index into db_portraits (includes generic synergies)
            loc_idx = 0
            for en_idx, en_line in enumerate(syn_list_en):
                en_name = _re.split(r'\s+[-–]\s+|\s+\(', en_line)[0].strip().lower()
                is_generic = any(en_name.startswith(g) for g in _SYNERGY_GENERIC_JP)
                # DB-based portraits (covers both unique and generic synergies)
                db_portraits_here = db_portraits[db_all_idx] if db_all_idx < len(db_portraits) else []
                db_all_idx += 1
                if not is_generic and loc_idx < len(loc_syn_names):
                    loc_title, loc_desc, loc_partners = loc_syn_names[loc_idx]
                    rest = en_line[len(_re.split(r'\s+[-–]\s+|\s+\(', en_line)[0]):]
                    rest = _re.sub(
                        r'\((\d+)-Star\+\)',
                        lambda m: f'（{_STAR_JP.get(m.group(1), m.group(1))}以上）',
                        rest
                    )
                    rest = _re.sub(r'\s*[-–]\s*Unique', '　ユニーク', rest)
                    title_str = loc_title + rest.rstrip()
                    desc_str = loc_desc.replace('\n', '<br>') if loc_desc else ''
                    # Prefer DB portraits (complete); fall back to loc DESC named partners
                    portraits = db_portraits_here or [
                        _norm_to_portrait[_norm_jp(p)]
                        for p in loc_partners
                        if _norm_jp(p) in _norm_to_portrait
                    ]
                    syn_list.append((title_str, desc_str, portraits))
                    loc_idx += 1
                else:
                    title_str = translate_synergy_line(en_line)
                    syn_list.append((title_str, '', db_portraits_here))

            if not syn_list_en and loc_syn_names:
                for loc_title, loc_desc, loc_partners in loc_syn_names:
                    portraits = [
                        _norm_to_portrait[_norm_jp(p)]
                        for p in loc_partners
                        if _norm_jp(p) in _norm_to_portrait
                    ]
                    desc_str = loc_desc.replace('\n', '<br>') if loc_desc else ''
                    syn_list.append((loc_title, desc_str, portraits))

        portrait_fname = c.get("portrait", "") or portrait_map.get(slug, "")
        if portrait_fname:
            syn_list = [
                (title, desc, [p for p in portraits if p != portrait_fname])
                for title, desc, portraits in syn_list
            ]

        def _syn_li(title: str, desc: str, portraits: list[str]) -> str:
            imgs = ''.join(
                f'<img class="syn-portrait" src="portraits/{p}" alt="">'
                for p in portraits
            )
            portraits_html = f'<div class="syn-portraits">{imgs}</div>' if imgs else ''
            desc_html = f'<div class="syn-desc">{desc}</div>' if desc else ''
            return (
                f'<li class="syn-item">'
                f'<div class="syn-title">{title}</div>'
                f'{portraits_html}'
                f'{desc_html}'
                f'</li>'
            )

        syn_items = "".join(_syn_li(t, d, p) for t, d, p in syn_list)

        # ゲームデータセクション
        game_data_html = build_game_data_html(
            slug, abilities, slug_map, loc_prefix_map, kv,
            c.get("legacy_loc_prefixes", []), binary_id
        )

        portrait_html = (
            f'<img class="champ-portrait" src="portraits/{portrait_fname}" alt="{name_en}">'
            if portrait_fname else '<div class="champ-portrait champ-portrait-none"></div>'
        )

        en_sub = f'<span class="champ-en">{name_en}</span>' if name_jp else ""
        release_html = f'<div class="release">リリース: {release}</div>' if release else ""
        card = f"""
<div class="card" data-slug="{slug}" data-class="{cls}" data-name="{(name_jp + ' ' + name_en).lower()}">
  <div class="card-header" style="border-left:4px solid {color}">
    <div class="title-row">
      {portrait_html}
      <div class="champ-title"><h2 class="champ-name">{name}</h2>{en_sub}</div>
      <span class="cls-badge" style="background:{color}">{class_jp}</span>
    </div>
    {release_html}
  </div>
  <div class="card-body">
    {'<details class="syn-details"><summary>シナジー一覧（' + str(len(syn_list)) + '件）</summary><ul class="syn-list">' + syn_items + '</ul></details>' if syn_items else ''}
    {game_data_html}
  </div>
</div>"""
        html_parts.append(card)

    return "\n".join(html_parts)


def generate_html(champions: list[dict], cache: dict,
                  abilities: dict | None = None, slug_map: dict | None = None,
                  name_jp_map: dict | None = None,
                  loc_prefix_map: dict | None = None,
                  kv: dict | None = None,
                  portrait_map: dict | None = None) -> str:
    classes = sorted(
        set(c.get("champion_class", "") for c in champions if c.get("champion_class"))
    )

    filter_btns = '<button class="f-btn active" data-class="all">すべて</button>\n'
    for cls in classes:
        color = CLASS_COLORS.get(cls, "#607D8B")
        jp    = CLASS_JP.get(cls, cls)
        filter_btns += (
            f'<button class="f-btn" data-class="{cls}" '
            f'style="--cc:{color}">{jp}</button>\n'
        )

    cards_html = build_cards(champions, cache, abilities, slug_map, name_jp_map, loc_prefix_map, kv, portrait_map)
    total      = len(champions)

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>MCOC チャンピオン解説（日本語）</title>
<style>
:root{{
  --bg:#f2f3f7;--bg2:#ffffff;--bg3:#eef0f6;
  --text:#1a1a2e;--text2:#65657a;
  --accent:#5044d4;--border:#dcdee9;
}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--bg);color:var(--text);font-family:'Segoe UI','Hiragino Kaku Gothic ProN',sans-serif;min-height:100vh}}

/* ヘッダー */
.site-hd{{background:var(--bg2);border-bottom:1px solid var(--border);padding:14px 20px;position:sticky;top:0;z-index:100}}
.hd-inner{{max-width:1400px;margin:0 auto;display:flex;align-items:center;gap:14px;flex-wrap:wrap}}
.site-title{{font-size:1.3rem;font-weight:700;color:var(--accent);white-space:nowrap}}
.search-wrap{{flex:1;min-width:180px}}
.search-wrap input{{width:100%;background:var(--bg3);border:1px solid var(--border);color:var(--text);padding:7px 13px;border-radius:8px;font-size:14px;outline:none}}
.search-wrap input:focus{{border-color:var(--accent)}}
.cnt{{font-size:13px;color:var(--text2);white-space:nowrap}}

/* フィルターバー */
.f-bar{{background:var(--bg2);border-bottom:1px solid var(--border);padding:9px 20px;overflow-x:auto}}
.f-inner{{max-width:1400px;margin:0 auto;display:flex;gap:7px}}
.f-btn{{padding:5px 13px;border-radius:20px;border:1px solid var(--border);background:transparent;color:var(--text2);cursor:pointer;font-size:13px;white-space:nowrap;transition:.15s}}
.f-btn:hover{{border-color:var(--cc,var(--accent));color:var(--text)}}
.f-btn.active{{background:var(--cc,var(--accent));border-color:transparent;color:#fff;font-weight:600}}

/* グリッド */
.main{{max-width:1400px;margin:0 auto;padding:20px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(350px,1fr));gap:18px}}
.no-res{{text-align:center;color:var(--text2);padding:60px 20px;font-size:1rem;display:none}}

/* カード */
.card{{background:var(--bg2);border:1px solid var(--border);border-radius:12px;overflow:hidden;transition:.15s;box-shadow:0 1px 4px rgba(0,0,0,.06)}}
.card:hover{{transform:translateY(-2px);box-shadow:0 6px 20px rgba(0,0,0,.12)}}
.card-header{{padding:13px 15px 9px;background:var(--bg3)}}
.title-row{{display:flex;align-items:center;justify-content:space-between;gap:8px}}
.champ-portrait{{width:64px;height:64px;border-radius:8px;object-fit:cover;flex-shrink:0;border:1px solid var(--border)}}
.champ-portrait-none{{width:64px;height:64px;border-radius:8px;background:var(--bg);flex-shrink:0}}
.champ-title{{display:flex;flex-direction:column;gap:1px;flex:1;min-width:0}}
.champ-name{{font-size:1.05rem;font-weight:700}}
.champ-en{{font-size:11px;color:var(--text2);font-weight:400}}
.cls-badge{{font-size:11px;font-weight:600;padding:3px 10px;border-radius:12px;color:#fff;white-space:nowrap}}
.release{{font-size:12px;color:var(--text2);margin-top:3px}}
.card-body{{padding:13px 15px;display:flex;flex-direction:column;gap:11px}}

/* アトリビュート */
.attrs-row{{display:flex;flex-wrap:wrap;gap:5px}}
.attr-badge{{font-size:11px;background:rgba(80,68,212,.07);border:1px solid rgba(80,68,212,.22);color:#5044d4;padding:2px 8px;border-radius:4px}}

/* シナジー */
.syn-details{{font-size:13px}}
.syn-details summary{{color:var(--text2);cursor:pointer;padding:3px 0;user-select:none}}
.syn-details summary:hover{{color:var(--text)}}
.syn-list{{margin-top:7px;list-style:none;display:flex;flex-direction:column;gap:6px}}
.syn-item{{background:var(--bg3);border-radius:6px;padding:6px 10px;display:flex;flex-direction:column;gap:5px}}
.syn-title{{color:var(--text);font-size:12px;font-weight:600}}
.syn-portraits{{display:flex;flex-direction:row;gap:4px;flex-wrap:wrap}}
.syn-portrait{{width:32px;height:32px;border-radius:5px;object-fit:cover;border:1px solid var(--border)}}
.syn-desc{{color:var(--text2);font-size:11px;line-height:1.55;padding-left:2px}}

/* ゲームデータセクション（mcoc.gg形式） */
.gd-sec{{border-top:1px solid var(--border);padding-top:10px;display:flex;flex-direction:column;gap:8px}}
.gd-sublabel{{font-size:10px;color:var(--text2);text-transform:uppercase;letter-spacing:.06em;display:block;margin-bottom:4px}}
.gd-badges{{display:flex;flex-wrap:wrap;gap:4px}}
.abi-badge{{display:inline-flex;align-items:center;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:500;border:1px solid}}
.abi-buff{{background:rgba(30,110,255,.07);border-color:rgba(30,110,255,.22);color:#1a6ae0}}
.abi-debuff{{background:rgba(210,40,40,.07);border-color:rgba(210,40,40,.22);color:#c82828}}
.abi-immune{{background:rgba(20,150,70,.07);border-color:rgba(20,150,70,.22);color:#0e9646}}
.abi-neutral{{background:rgba(80,68,212,.07);border-color:rgba(80,68,212,.22);color:#5044d4}}
.gd-immune{{display:block}}
.gd-descs{{display:flex;flex-direction:column;gap:3px}}
.gd-detail summary{{font-size:12px;color:var(--text2);cursor:pointer;padding:3px 0;user-select:none;list-style:none;display:flex;align-items:center;gap:4px}}
.gd-detail summary::before{{content:"▶";font-size:9px;transition:.15s}}
.gd-detail[open] summary::before{{content:"▼"}}
.gd-detail summary:hover{{color:var(--text)}}
.gd-detail[open] summary{{color:var(--accent)}}
.gd-ability-groups{{margin-top:7px;display:flex;flex-direction:column;gap:10px}}
.gd-ability-group{{display:flex;flex-direction:column;gap:4px}}
.gd-ability-title{{font-size:12px;color:var(--text);font-weight:600}}
.gd-texts{{list-style:none;margin-top:5px;display:flex;flex-direction:column;gap:4px;padding-left:2px}}
.gd-texts li{{font-size:12px;color:var(--text2);line-height:1.65;padding-left:8px;border-left:2px solid var(--border)}}

</style>
</head>
<body>

<header class="site-hd">
  <div class="hd-inner">
    <div class="site-title">⚔️ MCOC チャンピオン解説</div>
    <div class="search-wrap">
      <input type="text" id="q" placeholder="チャンピオン名・アビリティで検索…" oninput="run()">
    </div>
    <div class="cnt" id="cnt">{total} 件表示中</div>
  </div>
</header>

<div class="f-bar">
  <div class="f-inner">
    {filter_btns}
  </div>
</div>

<main class="main">
  <div class="grid" id="grid">
    {cards_html}
  </div>
  <div class="no-res" id="noRes">該当するチャンピオンが見つかりませんでした</div>
</main>

<script>
let cls='all',q='';
document.querySelectorAll('.f-btn').forEach(b=>{{
  b.addEventListener('click',function(){{
    document.querySelectorAll('.f-btn').forEach(x=>x.classList.remove('active'));
    this.classList.add('active');
    cls=this.dataset.class;
    run();
  }});
}});
function run(){{
  q=document.getElementById('q').value.toLowerCase();
  let vis=0;
  document.querySelectorAll('.card').forEach(card=>{{
    const mc=cls==='all'||card.dataset.class===cls;
    const mq=!q||card.dataset.name.includes(q)||card.textContent.toLowerCase().includes(q);
    card.style.display=(mc&&mq)?'':'none';
    if(mc&&mq)vis++;
  }});
  document.getElementById('cnt').textContent=vis+' 件表示中';
  document.getElementById('noRes').style.display=vis===0?'block':'none';
}}
</script>
</body>
</html>"""


# ─── メイン ──────────────────────────────────────────────────
def main():
    print("=" * 50)
    print("MCOC チャンピオン日本語ページ生成（ゲーム内抽出のみ）")
    print("=" * 50)

    print("\n[ゲームデータ読み込み]")
    abilities, slug_map = load_abilities()

    name_jp_map: dict = {}

    kv = load_localization()
    champions, game_slug_map, portrait_map = load_game_only_champions(abilities, kv, name_jp_map)
    slug_map = game_slug_map
    loc_prefix_map = build_loc_prefix_map(slug_map, kv) if kv else {}
    for c in champions:
        if c.get("loc_prefix"):
            loc_prefix_map[c["slug"]] = c["loc_prefix"]
    print(f"ローカライズprefixマッピング: {len(loc_prefix_map)} 件")
    print(f"ポートレートマップ: {len(portrait_map)} 件")

    print("\n[HTML 生成フェーズ]")
    cache: dict = {}
    html = generate_html(champions, cache, abilities, slug_map, name_jp_map, loc_prefix_map, kv, portrait_map)

    if OUTPUT_PATH.exists():
        OUTPUT_PATH.unlink()
    OUTPUT_PATH.write_bytes(html.encode("utf-8"))

    size_kb = OUTPUT_PATH.stat().st_size / 1024
    print(f"\n完了: {OUTPUT_PATH}")
    print(f"  チャンピオン数 : {len(champions)} 件")
    print("  データソース   : ゲーム内抽出データのみ")
    print(f"  ファイルサイズ : {size_kb:.1f} KB")


if __name__ == "__main__":
    main()
