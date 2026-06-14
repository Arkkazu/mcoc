#!/usr/bin/env python3
"""
MCOC チャンピオン日本語解説ページ生成スクリプト

ゲーム内抽出データ（BCG由来のクラス/アビリティ/ローカライズ）を使い、
単一の検索・フィルター機能付き HTML ページを生成する。

使用方法:
  python3 generate_jp_page.py
"""

import html
import json
from pathlib import Path

# ─── パス設定 ───────────────────────────────────────────────
BASE = Path(__file__).parent
OUTPUT_PATH     = BASE / "index.html"
PORTRAIT_SRC_DIR = "data/portraits"
SITE_URL = "https://marvel-allstar-battle.tokyo/"
ADSENSE_CLIENT = "ca-pub-1334543920393100"
ABILITIES_PATH  = BASE / "data" / "abilities_all.json"
SLUG_MAP_PATH   = BASE / "data" / "slug_to_prefix.json"
NAME_JP_PATH    = BASE / "data" / "slug_to_jp.json"
WORDS_PATH      = BASE / "words_main.json"
CHAMP_NAMES_PATH = BASE / "data" / "champion_names_jp.json"
CHAMPION_CLASSES_PATH = BASE / "champion_classes.txt"
CHAMPIONS_SUMMARY_PATH = BASE / "champions_summary.txt"
LOCAL_BCG_PATH = BASE / "B64FC6A6D6243DB2A88B295572F5B5F145A66393.bin"
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
    "resist_physical":  "物理抵抗力",
    "resist_magic":     "エネルギー抵抗力",
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
    "crit_resist":          "クリティカル抵抗力",
    "crit_resist_mod":      "クリティカル抵抗力増幅",
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
    "antman": "antu",
    "attuma": "atma",
    "beast": "bst",
    "bishop": "bishn",
    "blackpanther": "bpu",
    "blackpanther_cw": "blkpanther",
    "blackpanther_realm": "jabpantu",
    "blackwidow_movie": "bwmcu",
    "blackwidow_timely": "cvbw",
    "brothervoodoo": "drvood",
    "captainamerica": "cpam",
    "captainamerica_movie": "capiw",
    "captainamerica_ww2": "cpww2",
    "captainmarvel_movie": "cptmcu",
    "carnage": "car",
    "cassandranova": "cnova",
    "champion": "thechamp",
    "civilwarrior": "cwu",
    "colossus": "colos",
    "countnefaria": "cnef",
    "cullobsidian": "cul",
    "cyclops": "clclps",
    "daredevil_netflix": "dhk",
    "daredevil": "drdvl",
    "deadpool_gold": "dplgld",
    "deadpool_x_force": "dpxuwu",
    "deadpool_xforce": "dpxuwu",
    "destroyer": "thdstrr",
    "diablo": "diau",
    "doc_ock": "doc",
    "doctorbong": "bong",
    "dragonman": "dman",
    "ebonymaw": "ebm",
    "falcon": "flcu",
    "falcon_joaquintorres": "flcjt",
    "frankencastle": "frnk",
    "ghostrider_cosmic": "cgr",
    "groot_king": "kgu",
    "groot_king_deathless": "kg",
    "guillotine": "guu",
    "guillotine_2099": "glt29",
    "guillotine_nameless": "gltn",
    "hawkeye": "hawko",
    "howardfrontend": "htdu",
    "howardmech": "htdu",
    "hulk": "hulku",
    "hulkbuster_movie": "hkbst",
    "hulkling": "hlklng",
    "iceman": "icm",
    "icephoenix": "icmphx",
    "ironman_movie": "imi",
    "ironman_silvercenturion": "immrk",
    "ironman_superior": "supman",
    "ironfist": "ifist",
    "ironfist_white": "ifistw",
    "isophyne": "iphyne",
    "jjj_spiderslayer": "jjj",
    "joefixit": "joov",
    "juggernaut": "jugger",
    "karnak": "krku",
    "kittypryde": "ktyp",
    "lukecage": "luke",
    "maestro_overseer": "ovrsr",
    "madelynepryor": "mady",
    "magneto": "mgcl",
    "magneto_marvelnow": "mgnx",
    "mangog": "mgog",
    "misterknight": "mrkn",
    "misternegative": "mrneg",
    "mistersinister": "mrsin",
    "mistyknight": "mkt",
    "moleman": "molmn",
    "msmarvel_kamala": "kmla",
    "nebula": "nblu",
    "negasonicteenagewarhead": "ntw",
    "nightcarnage": "ncarn",
    "nightcrawler": "ngc",
    "nightthrasher": "nthra",
    "okoye": "oky",
    "phoenix_dark": "phx",
    "phylavell": "phyla",
    "punisher": "pnshru",
    "punisher_2099": "pn29u",
    "red_goblin": "rgob",
    "redskull": "rskulln",
    "rhino": "rhno",
    "sasquatch": "sqch",
    "scarletwitch": "swtch",
    "scarletwitch_current": "scitch",
    "shatterstar": "shatter",
    "shehulk_deathless": "sheh",
    "spidergwen": "spgwn",
    "spiderman_morales": "spmmu",
    "spiderman_movie": "spmcu",
    "spiderman_pavitr": "pvitr",
    "spiderman_black": "spdrmn",
    "spiderman_stealth": "stlspdr",
    "spiderpunk": "spunk",
    "spiderwitch": "spwtch",
    "squirrelgirl": "sqg",
    "starlord_stellar": "slsf",
    "storm_realm": "stormr",
    "superior_iron_man": "supman",
    "thanos_deathless_trophy": "thanos",
    "thor": "thor",
    "thor_janefoster": "thrj",
    "ultron": "ultc",
    "ultron_prime": "ultu",
    "unstoppable_colossus": "clsun",
    "venompool": "vplu",
    "venomtheduck": "vtd",
    "vision_deathless": "vsn",
    "vision": "vsn",
    "vision_movie": "vsmov",
    "vision_timely": "visaark",
    "vulture_movie": "vlt",
    "wiccan": "wccn",
    "wolverine": "wlvrn",
    "wolverine_oldman": "oml",
    "x23": "x23u",
    "wolverine_x_23": "x23u",
    "yelenabelova": "ylb",
    "yellowjacket": "yju",
    "colossus_unstoppable": "clsun",
}

SUPPLEMENTAL_ABILITY_PREFIXES = {
    # Classic Abomination stores its old all-attacks Fury as a one-entry abm_* bundle.
    "abmntn": ("abm",),
    # Cyclops (New Xavier School) splits current signature rows from legacy optic-blast rows.
    "clclps": ("cyclps",),
    # Iron Fist (Immortal) shares the base Iron Fist combat kit but has a different signature.
    "ifistw": ("ifist",),
    # Vision (Age of Ultron) keeps the movie power-steal row in the base Vision bundle.
    "vsmov": ("vsn",),
}

PORTRAIT_BINARY_ID_ALIASES = {
    # ゲーム内binary idとportraitファイル名が一致しないもの。
    "beast": "portrait_Beast_Allnew.png",
    "captainamerica_movie": "portrait_captainamerica_infinitywar.png",
    "captainamerica_ww2": "portrait_capamerica_wwii.png",
    "drstrange": "portrait_doctor_strange.png",
    "groot_king_deathless": "portrait_groot_king_blackorder.png",
    "guillotine_nameless": "portrait_guillotine_blackorder.png",
    "gwenperion": "portrait_ALT_gwenperion.png",
    "howardfrontend": "portrait_howardmech.png",
    "humantorch": "portrait_johnnystorm.png",
    "icephoenix": "portrait_ALT_icephoenix.png",
    "jeangrey": "portrait_jean_grey_current.png",
    "jessicajones_current": "portrait_jessica_jones.png",
    "korg": "portrait_korg_movie.png",
    "maestro_trophy": "portrait_maestro.png",
    "magneto_marvelnow": "portrait_magneto_white.png",
    "nightcarnage": "portrait_ALT_nightcarnage.png",
    "sentry": "portrait_sentry_current.png",
    "spiderwitch": "portrait_ALT_spider_witch.png",
    "thanos_deathless_trophy": "portrait_thanos_nameless.png",
    "vision_deathless": "portrait_vision_blackorder.png",
    "void": "portrait_void_current.png",
}

ROSTER_BINARY_ID_ALIASES = {
    # slug由来ID・旧表示IDと、ロスタータグ定義のbinary idが一致しないもの。
    "captain_marvel_movie": "captainmarvel_movie",
    "kang_the_conqueror": "kang",
    "rocket_raccoon": "rocket",
    "spider_man_classic": "spiderman",
    "howardfrontend": "howardmech",
    "jeangrey": "jeangrey_current",
    "jessicajones": "jessicajones_current",
    "skrull": "skrull_super",
}

LOC_PREFIX_ALIASES = {
    # binary_idから機械生成したprefixと、実際の日本語ローカライズprefixが違うもの。
    "cassandranova": ("CASSANDRA",),
    "hulk_red": ("REDHULK",),
    "madelynepryor": ("MADELYNE",),
    "thanos_deathless_trophy": ("THANOS_DEATHLESS_TROPHY",),
    "thor_janefoster": ("JANEF",),
    "thor_ragnarok": ("RAGTHOR",),
    "x23": ("X23U",),
}

CLASS_FALLBACKS = {
    # champion_classes.txt の抽出が internal class=chemical/trained を拾えない場合の補完。
    "abomination": "Science",
    "abomination_immortal": "Science",
    "antivenom": "Science",
    "antman": "Science",
    "bluemarvel": "Science",
    "captainamerica": "Science",
    "captainamerica_movie": "Science",
    "captainamerica_ww2": "Science",
    "cassielang": "Science",
    "countnefaria": "Science",
    "electro": "Science",
    "highevolutionary": "Science",
    "hulk": "Science",
    "hulk_immortal": "Science",
    "hulk_ragnarok": "Science",
    "hulk_red": "Science",
    "humantorch": "Science",
    "invisiblewoman": "Science",
    "jessicajones": "Science",
    "joefixit": "Science",
    "leader": "Science",
    "lizard": "Science",
    "lukecage": "Science",
    "maestro_overseer": "Science",
    "misternegative": "Science",
    "modok": "Science",
    "morbius": "Science",
    "mrfantastic": "Science",
    "falcon_joaquintorres": "Science",
    "photon": "Science",
    "quake": "Science",
    "quicksilver": "Science",
    "redguardian": "Science",
    "rhino": "Science",
    "sandman": "Science",
    "scorpion": "Science",
    "sentry": "Science",
    "shehulk": "Science",
    "shehulk_deathless": "Science",
    "silk": "Science",
    "spidergwen": "Science",
    "spiderham": "Science",
    "spiderman": "Science",
    "spiderman_2099": "Science",
    "spiderman_morales": "Science",
    "spiderpunk": "Science",
    "spiderwoman": "Science",
    "spot": "Science",
    "thing": "Science",
    "titania": "Science",
    "void": "Science",
    "wasp": "Science",
    "wave": "Science",
    "yellowjacket": "Science",
    "aegon": "Skill",
    "agentvenom": "Skill",
    "attuma": "Skill",
    "baronzemo": "Skill",
    "blackcat": "Skill",
    "blackpanther": "Skill",
    "blackpanther_cw": "Skill",
    "blackpanther_realm": "Skill",
    "blackwidow": "Skill",
    "blackwidow_movie": "Skill",
    "blade": "Skill",
    "bullseye": "Skill",
    "cheeilth": "Skill",
    "crossbones": "Skill",
    "daredevil": "Skill",
    "daredevil_netflix": "Skill",
    "elektra": "Skill",
    "elsabloodstone": "Skill",
    "falcon": "Skill",
    "doctorbong": "Skill",
    "frankencastle": "Skill",
    "gwenpool": "Skill",
    "hawkeye": "Skill",
    "hitmonkey": "Skill",
    "karnak": "Skill",
    "katebishop": "Skill",
    "killmonger": "Skill",
    "kingpin": "Skill",
    "korg": "Skill",
    "kraven": "Skill",
    "lumatrix": "Skill",
    "mantis": "Skill",
    "masacre": "Skill",
    "mbaku": "Skill",
    "misterknight": "Skill",
    "mistyknight": "Skill",
    "moleman": "Skill",
    "moondragon": "Skill",
    "moonknight": "Skill",
    "nickfury": "Skill",
    "nightthrasher": "Skill",
    "okoye": "Skill",
    "punisher": "Skill",
    "patriot": "Skill",
    "ronin": "Skill",
    "shangchi": "Skill",
    "silversable": "Skill",
    "spiderman_stealth": "Skill",
    "squirrelgirl": "Skill",
    "starlord_stellar": "Skill",
    "taskmaster": "Skill",
    "thor_ragnarok": "Skill",
    "valkyrie": "Skill",
    "wintersoldier": "Skill",
    "yelenabelova": "Skill",
    "shatterstar": "Mutant",
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
    "ares",
    "chair",
    "cerastes",
    "grandmaster",
    "grandmaster_event",
    "gwenperion",
    "herbie",
    "icephoenix",
    "infinityclaw",
    "isosphere",
    "lockheed",
    "lockjaw",
    "lotan",
    "nightcarnage",
    "orochi",
    "spiderwitch",
    "sym_cos_beam",
    "sym_cos_thanos",
    "sym_mut_electric",
    "sym_mut_ground",
    "venomtheduckfrontend",
    "wolverine_xforce",
    "x23_legacy",
}

ALLOW_DUPLICATE_PREFIX_BINARY_IDS = {
    "phoenix_dark",
    "shehulk_deathless",
    "spiderman_black",
    "storm_realm",
    "thanos_deathless_trophy",
    "vision_deathless",
}

NO_GAME_ABILITY_PREFIX_BINARY_IDS = {
    # Deathless Thanos shares the base thanos BCG prefix, but the current local
    # BCG export does not expose a clean playable ability subset for him.
    "hulk_red",
    "thanos_deathless_trophy",
    "thor_ragnarok",
}

SHARED_PREFIX_ABILITY_FILTERS = {
    # Dark Phoenix uses the normal Phoenix ability prefix (phx), so remove its
    # boss-only entries when building the playable Phoenix card.
    "phoenix": {
        "exclude_entry": ("phx_dk_",),
        "exclude_ui": ("phoenix_dark_",),
    },
    "phoenix_dark": {
        "include_entry": ("phx_dk_",),
        "include_ui": ("phoenix_dark_",),
    },
    "ironfist_white": {
        "exclude_entry": ("ifist_sig",),
    },
    "shehulk_deathless": {
        "include_entry": ("sheh_dthls_",),
    },
    "spiderman_black": {
        "exclude_entry": ("spdrmn_sig", "spdrmn_tnt_", "spdrmn_web_", "spdrmn_stn_opp_"),
        "exclude_ui": ("spiderman_spider_sense_", "spiderman_taunt", "spiderman_webbing"),
    },
    "vision": {
        "exclude_entry": ("vsmov_", "vsn_mov_", "vsn_dthls_"),
        "exclude_ui": ("dvision_",),
    },
    "vision_deathless": {
        "include_entry": ("vsn_dthls_",),
        "include_ui": ("dvision_",),
    },
    "vision_movie": {
        "include_entry": ("vsmov_", "vsn_mov_"),
    },
}


def _has_roster_year_tag(tags: list[str]) -> bool:
    return any(_re.fullmatch(r"tg_20\d{2}", tag) for tag in tags)


def _has_roster_size_tag(tags: list[str]) -> bool:
    return any(tag.startswith("tg_size") for tag in tags)


def is_game_playable_roster_record(binary_id: str, record: dict | None) -> bool:
    """BCGロスター行だけから、一覧に出すプレイアブルかを判定する。"""
    if not record:
        return False
    if binary_id.endswith("_legacy"):
        return False
    if any(binary_id.startswith(prefix) for prefix in NON_PLAYABLE_BINARY_PREFIXES):
        return False
    if record.get("champion_class") not in CLASS_JP:
        return False
    tags = record.get("tags", [])
    if not _has_roster_year_tag(tags) or not _has_roster_size_tag(tags):
        return False
    return bool(record.get("header_links"))


def load_game_playable_binary_ids() -> set[str]:
    """BCGロスター定義からプレイアブルbinary id集合を返す。"""
    global _BCG_PLAYABLE_BINARY_ID_CACHE
    if _BCG_PLAYABLE_BINARY_ID_CACHE is not None:
        return _BCG_PLAYABLE_BINARY_ID_CACHE
    records = load_bcg_roster_records()
    _BCG_PLAYABLE_BINARY_ID_CACHE = {
        binary_id
        for binary_id, record in records.items()
        if is_game_playable_roster_record(binary_id, record)
    }
    return _BCG_PLAYABLE_BINARY_ID_CACHE


def is_playable_binary_id(binary_id: str) -> bool:
    if load_bcg_roster_records():
        return binary_id in load_game_playable_binary_ids()
    if binary_id.endswith("_legacy"):
        return False
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

_LOC_GLOSSARY_TAG_RE = _re.compile(r'\[k=glossary/([^\]]+)\](.*?)\[/k\]')
_LOC_LINK_TAG_RE = _re.compile(r'\[k=[^\]]+\](.*?)\[/k\]')
_LOC_COLOR_TAG_RE = _re.compile(r'\[(?:[-#a-fA-F0-9]{1,10})\]')


def _strip_loc_color_tags(text: str) -> str:
    """色タグだけ除去し、glossaryリンクは必要に応じて残せるようにする。"""
    return _LOC_COLOR_TAG_RE.sub('', text)


def _normalize_loc_link_tags(text: str) -> str:
    """一部ローカライズに混じる [k] 閉じタグ表記を標準の [/k] に寄せる。"""
    return text.replace('[k]', '[/k]')


def strip_loc_tags(text: str) -> str:
    """カラータグ・リンクタグを除去してプレーンテキストにする"""
    text = _normalize_loc_link_tags(text)
    text = _LOC_LINK_TAG_RE.sub(r'\1', text)
    text = _strip_loc_color_tags(text)
    return text.strip()


def _clean_loc_text(value: str, preserve_glossary: bool = False) -> str:
    """ローカライズ本文を整形する。能力本文ではglossaryタグを保持できる。"""
    value = _normalize_loc_link_tags(value)
    if preserve_glossary:
        value = _strip_loc_color_tags(value)
        value = _re.sub(r'\[k=(?!glossary/)[^\]]+\](.*?)\[/k\]', r'\1', value)
    else:
        value = strip_loc_tags(value)
    value = _re.sub(r'\{\d+\}', '〔数値〕', value)
    value = _re.sub(r'\s+', ' ', value)
    return value.strip()


GLOSSARY_DEFINITION_KEYS = {
    # ゲーム内ローカライズの汎用説明キー。存在するものだけHTML化する。
    "armor_break": ("ID_ARAK64T", "ID_ARAK64D"),
    "armor_shattered": ("ID_ARMSHAT_T", "ID_ARMSHAT_D"),
    "armor_up": ("ID_ARMOR_UP_T", "ID_ARMOR_UP_D"),
    "bleed": ("ID_BLED98T", "ID_BLED98D"),
    "coldsnap": ("ID_COAP58403T", "ID_COAP58403D"),
    "degen": ("ID_DEON94T", "ID_DEON94D"),
    "degeneration": ("ID_DEON94T", "ID_DEON94D"),
    "phys_res": ("ID_PHCE117T", "ID_PHCE117D"),
    "energy_res": ("ID_ENCE116T", "ID_ENCE116D"),
    "fury": ("ID_FURY107T", "ID_FURY107D"),
    "precision": ("ID_PRON80T", "ID_PRON80D"),
    "prowess": ("ID_PRSS83T", "ID_PRSS83D"),
    "unblockable": ("ID_UNLE83T", "ID_UNLE83D"),
    "evade": ("ID_EVON101T", "ID_EVON101D"),
    "parry": ("ID_UI_TUTORIAL_PARRY_TITLE", "ID_PS_PARRY_ICON_D_V2"),
    "hinder": ("ID_DSTRR_HNDRT", "ID_DSTRR_HNDRD"),
    "enervate": ("ID_ENTE109T", "ID_ENTE109D"),
    "exhaustion": ("ID_EXON35T", "ID_EXON35D"),
    "fatigue": ("ID_FAUE106T", "ID_FAUE106D"),
    "fear": ("ID_FEAR_T", "ID_FEAR_D"),
    "frostbite": ("ID_FRTE58403T", "ID_FRTE58403D"),
    "heal_block": ("ID_HECK90T", "ID_HECK90D"),
    "infuriate": ("ID_INFURIATET", "ID_INFURIATED"),
    "incinerate": ("ID_INTE211T", "ID_INTE211D"),
    "intimidate": ("ID_INTIM_T", "ID_INTIM_D"),
    "petrify": ("ID_PEFY58372T", "ID_PEFY58372D"),
    "power_lock": ("ID_POCK109T", "ID_POCK109D"),
    "power_sting": ("ID_PONG91T", "ID_PONG91D"),
    "power_gain": ("ID_POIN78T", "ID_POIN78D"),
    "power_steal": ("ID_POAL78T", "ID_POAL78D"),
    "poison": ("ID_POON122T", "ID_POON122D"),
    "cleanse": ("ID_CLNS_T", "ID_CLNS_D"),
    "combo_shield": ("ID_COLD220T", "ID_COLD220D"),
    "weakness": ("ID_WESS99T", "ID_WESS99D"),
    "acid_burn": ("ID_ACDT", "ID_ACDD"),
    "energy_vulnerability": ("ID_UI_STAT_ATTRIBUTE_ENERGY_VULNERABILITY_PT", "ID_UI_STAT_ATTRIBUTE_ENERGY_VULNERABILITY_PD"),
    "sabotage": ("ID_PS_SABOTAGE_T", "ID_PS_SABOTAGE_D"),
    "shock": ("ID_SHCK79T", "ID_SHCK79D"),
    "spectre": ("ID_SPECTRE_T", "ID_SPECTRE_D"),
    "stagger": ("ID_STER8216T", "ID_STER8216D"),
    "stun": ("ID_STUN115T", "ID_STUN115D"),
    "taunt": ("ID_TANT193T", "ID_TANT193D"),
    "tranquilize": ("ID_PS_TRANQUILIZE_T", "ID_PS_TRANQUILIZE_D"),
    "wither": ("ID_UI_STAT_ATTRIBUTE_WITHER_PT", "ID_UI_STAT_ATTRIBUTE_WITHER_PD"),
    "power_burn": ("ID_UI_STAT_FORMAT_POWER_BURN_TITLE", "ID_UI_STAT_FORMAT_POWER_BURN_DESC"),
    "power_dissolve": ("ID_PS_POWER_DISSOLVE_T", "ID_PS_POWER_DISSOLVE_D"),
    "power_efficiency": ("ID_POWEREFFICIENCY_T", "ID_POWEREFFICIENCY_D"),
    "power_reroute": ("ID_PS_POWER_REROUTE_T", "ID_PS_POWER_REROUTE_D"),
    "neuroshock": ("ID_PS_DANIMOONSTAR_NEUROSHOCK_T", "ID_PS_DANIMOONSTAR_NEUROSHOCK_D"),
    "trauma": ("ID_TRAUMAT", "ID_TRAUMAD"),
    "ensnare": ("ID_ENRE194T", "ID_ENRE194D"),
    "nova_flame": ("ID_TORCHNOVAT", "ID_TORCHNOVAD"),
    "charm": ("ID_CHARM_T", "ID_CHARM_D"),
    "soul_barb": ("ID_SOUL_BARB_T", "ID_SOUL_BARB_D"),
    "marked": ("ID_MARKED_T", "ID_MARKED_D"),
    "buff_accel": ("ID_MGK_BUFFACCEL_PAUSE_T", "ID_MGK_BUFFACCEL_PAUSE_D"),
    "buff_decel": ("ID_MGK_BUFFDECEL_PAUSE_T", "ID_MGK_BUFFDECEL_PAUSE_D"),
    "buff_immunity": ("ID_ANTIVENOMBIPT", "ID_ANTIVENOMBIPD"),
    "unsteady": ("ID_UNSTDYT", "ID_UNSTDYD"),
    "reckless": ("ID_PS_RECKLESS_T", "ID_PS_RECKLESS_D"),
    "ineptitude": ("ID_UI_STAT_FORMAT_DMAN_PAUSE_INEPT_TITLE", "ID_UI_STAT_FORMAT_DMAN_PAUSE_INEPT_DESC"),
    "slow": ("ID_UI_STAT_SLOW_DEBUFF", "ID_UI_STAT_SLOW_DEBUFF_LONG_V2"),
}

_GLOSSARY_DEFS_CACHE: dict[str, dict[str, str]] | None = None

# ゲーム本文には glossary タグが付かず、平文だけで出る用語がある。
# ただし「精度」「回避」「直撃」のように別語の一部になりやすい語は誤リンクを避ける。
PLAINTEXT_GLOSSARY_TERMS = {
    "acid_burn",
    "armor_break",
    "armor_shattered",
    "armor_up",
    "bleed",
    "buff_accel",
    "buff_decel",
    "buff_immunity",
    "charm",
    "cleanse",
    "coldsnap",
    "combo_shield",
    "degen",
    "energy_res",
    "energy_vulnerability",
    "enervate",
    "ensnare",
    "exhaustion",
    "fatigue",
    "fear",
    "frostbite",
    "fury",
    "heal_block",
    "incinerate",
    "ineptitude",
    "infuriate",
    "intimidate",
    "marked",
    "neuroshock",
    "nova_flame",
    "parry",
    "petrify",
    "phys_res",
    "power_burn",
    "power_dissolve",
    "power_efficiency",
    "power_gain",
    "power_lock",
    "power_reroute",
    "power_steal",
    "power_sting",
    "prowess",
    "reckless",
    "shock",
    "slow",
    "soul_barb",
    "spectre",
    "stagger",
    "stun",
    "taunt",
    "tranquilize",
    "trauma",
    "unblockable",
    "unsteady",
    "weakness",
    "wither",
}


def _collect_glossary_term_labels(kv: dict) -> dict[str, dict[str, int]]:
    labels: dict[str, dict[str, int]] = {}
    for value in kv.values():
        raw = _normalize_loc_link_tags(str(value))
        for match in _LOC_GLOSSARY_TAG_RE.finditer(raw):
            term = match.group(1).strip().lower()
            label = strip_loc_tags(match.group(2)).strip()
            if not term or not label:
                continue
            labels.setdefault(term, {})
            labels[term][label] = labels[term].get(label, 0) + 1
    return labels


def _best_glossary_label(term: str, labels: dict[str, int]) -> str:
    if labels:
        return max(labels, key=labels.get)
    return ABILITY_TYPE_JP.get(term, term.replace("_", " "))


def _safe_exact_glossary_definitions(term_labels: dict[str, dict[str, int]],
                                     kv: dict,
                                     known_terms: set[str]) -> dict[str, dict[str, str]]:
    """同じベース名のタイトル/説明ペアだけから、安全にglossary説明を補完する。"""
    label_to_terms: dict[str, set[str]] = {}
    for term, labels in term_labels.items():
        for label in labels:
            label_to_terms.setdefault(label, set()).add(term)

    candidates: dict[str, list[tuple[int, int, str, str, str]]] = {}
    for title_key, raw_title in kv.items():
        key_up = title_key.upper()
        bases: list[str] = []
        for suffix in ("_T", "T", "_TITLE"):
            if key_up.endswith(suffix):
                bases.append(title_key[:-len(suffix)])
        if not bases:
            continue

        title = _clean_loc_text(raw_title)
        terms = label_to_terms.get(title, set())
        if not terms:
            continue

        for base in bases:
            desc_key = ""
            for suffix in ("_D", "D", "_DESC", "_DESCRIPTION", "_LONG"):
                candidate_key = base + suffix
                if candidate_key in kv:
                    desc_key = candidate_key
                    break
            if not desc_key:
                continue

            desc = _clean_loc_text(kv[desc_key])
            if not desc or len(desc) < 8 or len(desc) > 260:
                continue

            for term in terms:
                if term in known_terms:
                    continue
                # 同じ表示名が複数のglossary keyに使われる場合は誤対応を避ける。
                if len(terms) > 1 and _re.sub(r'[^a-z0-9]', '', term) not in _re.sub(r'[^a-z0-9]', '', title_key.lower()):
                    continue
                penalty = 0
                bad_parts = ("SIGNATURE", "SYNERGY", "SPECIAL_ATTACK", "BIOS", "TUT", "TUTORIAL", "TRAINING")
                if any(part in key_up for part in bad_parts):
                    penalty += 100
                if key_up.startswith(("ID_UI_STAT_FORMAT_", "ID_UI_STAT_ATTRIBUTE_", "ID_STAT_ATTRIBUTE_")):
                    penalty += 15
                if key_up.startswith("ID_PS_"):
                    penalty += 5
                penalty += len(title_key)
                candidates.setdefault(term, []).append((penalty, abs(len(desc) - 70), title_key, title, desc))

    result: dict[str, dict[str, str]] = {}
    for term, items in candidates.items():
        items.sort(key=lambda item: (item[0], item[1], item[2]))
        _, _, _, title, desc = items[0]
        result[term] = {"title": title, "desc": desc}
    return result


def get_glossary_definitions(kv: dict) -> dict[str, dict[str, str]]:
    """glossary/key → {title, desc}。説明が取れない用語はクリック化しない。"""
    global _GLOSSARY_DEFS_CACHE
    if _GLOSSARY_DEFS_CACHE is not None:
        return _GLOSSARY_DEFS_CACHE
    defs: dict[str, dict[str, str]] = {}
    for term, (title_key, desc_key) in GLOSSARY_DEFINITION_KEYS.items():
        title = strip_loc_tags(kv.get(title_key, "")).strip()
        desc = _clean_loc_text(kv.get(desc_key, "")).strip()
        if title and desc:
            defs[term.lower()] = {"title": title, "desc": desc}
    term_labels = _collect_glossary_term_labels(kv)
    defs.update(_safe_exact_glossary_definitions(term_labels, kv, set(defs)))
    _GLOSSARY_DEFS_CACHE = defs
    return defs


def _glossary_button_html(term: str, label: str, glossary_defs: dict[str, dict[str, str]]) -> str:
    key = term.strip().lower()
    definition = glossary_defs.get(key)
    clean_label = strip_loc_tags(label)
    if not definition:
        return html.escape(clean_label)
    return (
        '<button type="button" class="glossary-term" '
        f'data-glossary-key="{html.escape(key, quote=True)}" '
        f'data-glossary-title="{html.escape(definition["title"], quote=True)}" '
        f'data-glossary-desc="{html.escape(definition["desc"], quote=True)}">'
        f'{html.escape(clean_label)}</button>'
    )


def render_plain_text_with_glossary_links(text: str,
                                          glossary_defs: dict[str, dict[str, str]]) -> str:
    """glossaryタグがないがゲーム内説明を持つ一部用語を本文中でリンク化する。"""
    clean = strip_loc_tags(text)
    link_terms = [
        (term, glossary_defs[term]["title"])
        for term in PLAINTEXT_GLOSSARY_TERMS
        if term in glossary_defs and glossary_defs[term].get("title")
    ]
    if not link_terms:
        return html.escape(clean)
    link_terms.sort(key=lambda item: len(item[1]), reverse=True)

    parts: list[str] = []
    pos = 0
    while pos < len(clean):
        matched: tuple[str, str] | None = None
        for term, label in link_terms:
            if clean.startswith(label, pos):
                matched = (term, label)
                break
        if not matched:
            parts.append(html.escape(clean[pos]))
            pos += 1
            continue
        term, label = matched
        parts.append(_glossary_button_html(term, label, glossary_defs))
        pos += len(label)
    return "".join(parts)


def render_ability_text_html(text: str, glossary_defs: dict[str, dict[str, str]]) -> str:
    """能力本文のglossaryタグを、クリック可能な用語ボタンに変換する。"""
    parts: list[str] = []
    pos = 0
    for match in _LOC_GLOSSARY_TAG_RE.finditer(text):
        if match.start() > pos:
            parts.append(render_plain_text_with_glossary_links(text[pos:match.start()], glossary_defs))
        parts.append(_glossary_button_html(match.group(1), match.group(2), glossary_defs))
        pos = match.end()
    if pos < len(text):
        parts.append(render_plain_text_with_glossary_links(text[pos:], glossary_defs))
    return "".join(parts)


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
_BCG_CHAMPION_TAG_CACHE: dict[str, list[str]] | None = None
_BCG_ROSTER_RECORD_CACHE: dict[str, dict] | None = None
_BCG_PLAYABLE_BINARY_ID_CACHE: set[str] | None = None

ROSTER_CLASS_TOKENS = {"chemical", "mutant", "trained", "cosmic", "tech", "mystic", "superior"}
ROSTER_CLASS_TO_CHAMPION_CLASS = {
    "chemical": "Science",
    "mutant": "Mutant",
    "trained": "Skill",
    "cosmic": "Cosmic",
    "tech": "Tech",
    "mystic": "Mystic",
}
ROSTER_RARITY_TOKENS = {"common", "uncommon", "rare", "epic", "legendary", "t6", "t7"}
ROSTER_SIZE_TOKENS = {"small", "average", "large", "giant"}
ROSTER_TAG_PREFIXES = (
    "typ_", "tg_", "saga_", "aw_", "eq_", "raid_", "tbe_", "cc_", "ave_", "col_",
)
ROSTER_LINK_PLACEHOLDERS = {"ff", "fff", "ffff", "ffV", "33", "333", "Ga", "ga"}
ROSTER_TAG_LABEL_FALLBACKS = {
    "tg_xmen": "X-Men",
    "tg_shld": "S.H.I.E.L.D.",
    "tg_wknda": "ワカンダ人",
    "aw_stone": "アライアンスウォー：ストーン",
    "aw_dinosaur": "アライアンスウォー：ダイナソー",
    "aw_ricochet": "アライアンスウォー：跳弾",
    "aw_stabilize": "アライアンスウォー：安定化",
    "tbe_wild": "派閥ビルダー：ワイルド",
}


def _latest_game_bcg_path() -> Path | None:
    if GAME_BCG_OUT.exists():
        bins = sorted(
            GAME_BCG_OUT.glob("*.bin"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if bins:
            return bins[0]
    return LOCAL_BCG_PATH if LOCAL_BCG_PATH.exists() else None


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


def _is_roster_tag_token(value: str) -> bool:
    return value.startswith(ROSTER_TAG_PREFIXES)


def load_champion_tag_labels() -> dict[str, str]:
    """タグID → 表示名。日本語ラベルが無いものは最小限のフォールバックを使う。"""
    labels: dict[str, str] = {}
    if CHAMP_NAMES_PATH.exists():
        try:
            data = json.loads(CHAMP_NAMES_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {}
        for key, info in data.items():
            if not _is_roster_tag_token(key) or not isinstance(info, dict):
                continue
            jp = strip_loc_tags(info.get("jp", "")).strip()
            if jp:
                labels[key] = jp
    labels.update(ROSTER_TAG_LABEL_FALLBACKS)
    return labels


def format_roster_tag_label(tag_key: str, labels: dict[str, str]) -> str:
    label = labels.get(tag_key, "")
    if label:
        return label
    year_match = _re.fullmatch(r"tg_(20\d{2})", tag_key)
    if year_match:
        return year_match.group(1)
    return tag_key.replace("_", " ")


def _roster_header_link_tokens(tokens: list[tuple[int, str]], header_idx: int, roster_idx: int) -> list[str]:
    """ロスター行ヘッダ内の実リンクIDだけを返す。ff/333等の埋め草は除外する。"""
    ignored = set(ROSTER_LINK_PLACEHOLDERS)
    ignored.update(f"{suffix}_regen" for suffix in _HERO_RARITY_SUFFIXES)
    links: list[str] = []
    seen: set[str] = set()
    for _, token in tokens[header_idx + 4:roster_idx]:
        if (
            token in ignored
            or _re.fullmatch(r"f+", token)
            or _re.fullmatch(r"3+", token)
        ):
            continue
        if token not in seen:
            links.append(token)
            seen.add(token)
    return links


def load_bcg_roster_records() -> dict[str, dict]:
    """BCGのロスター定義から binary_id ごとの class/tags/リンク情報を抽出する。"""
    global _BCG_ROSTER_RECORD_CACHE
    if _BCG_ROSTER_RECORD_CACHE is not None:
        return _BCG_ROSTER_RECORD_CACHE

    bcg_path = _latest_game_bcg_path()
    if not bcg_path:
        _BCG_ROSTER_RECORD_CACHE = {}
        return _BCG_ROSTER_RECORD_CACHE

    try:
        raw = bcg_path.read_bytes()
    except OSError:
        _BCG_ROSTER_RECORD_CACHE = {}
        return _BCG_ROSTER_RECORD_CACHE

    token_re = _re.compile(rb"[A-Za-z0-9_./:+-]{2,}")
    variant_re = _re.compile(r"^([a-z][a-z0-9_]*_(?:cm|un|rar|ep|leg|t6|t7))$")
    tokens = [
        (m.start(), m.group().decode("ascii", "ignore"))
        for m in token_re.finditer(raw)
    ]

    records: dict[str, dict] = {}
    for idx, (pos, token) in enumerate(tokens):
        if not variant_re.match(token):
            continue
        binary_id = _variant_base_id(token)
        suffix = _variant_suffix(token)
        if idx + 3 >= len(tokens):
            continue
        if tokens[idx + 1][1] != f"{binary_id}h" or tokens[idx + 2][1] not in ROSTER_CLASS_TOKENS:
            continue
        class_token = tokens[idx + 2][1]

        roster_idx = None
        for scan_idx in range(idx + 3, min(idx + 45, len(tokens) - 4)):
            if (
                tokens[scan_idx][1] == token
                and tokens[scan_idx + 1][1] == binary_id
                and tokens[scan_idx + 2][1] == class_token
                and tokens[scan_idx + 3][1] in ROSTER_RARITY_TOKENS
            ):
                roster_idx = scan_idx
                break
        if roster_idx is None:
            continue

        tags: list[str] = []
        seen: set[str] = set()
        for _, tag_token in tokens[roster_idx + 4:min(roster_idx + 45, len(tokens))]:
            if tag_token in ROSTER_SIZE_TOKENS:
                break
            if _variant_suffix(tag_token):
                break
            if not _is_roster_tag_token(tag_token) or tag_token in seen:
                continue
            tags.append(tag_token)
            seen.add(tag_token)

        rank = _HERO_RARITY_RANK.get(suffix, -1)
        record = records.setdefault(binary_id, {
            "class_token": class_token,
            "champion_class": ROSTER_CLASS_TO_CHAMPION_CLASS.get(class_token, ""),
            "variants": {},
            "tags_by_suffix": {},
            "pos": pos,
        })
        record["class_token"] = class_token
        record["champion_class"] = ROSTER_CLASS_TO_CHAMPION_CLASS.get(class_token, "")
        record["pos"] = min(record.get("pos", pos), pos)
        record["variants"][suffix] = {
            "rank": rank,
            "pos": pos,
            "header_idx": idx,
            "roster_idx": roster_idx,
            "header_links": _roster_header_link_tokens(tokens, idx, roster_idx),
        }
        record["tags_by_suffix"][suffix] = tags

    for binary_id, record in records.items():
        variants = record.get("variants", {})
        if not variants:
            continue
        best_suffix = max(
            variants,
            key=lambda suffix: (variants[suffix].get("rank", -1), variants[suffix].get("pos", -1)),
        )
        record["best_suffix"] = best_suffix
        record["tags"] = record.get("tags_by_suffix", {}).get(best_suffix, [])
        record["header_links"] = variants[best_suffix].get("header_links", [])
        record["suffixes"] = sorted(
            variants.keys(),
            key=lambda suffix: _HERO_RARITY_RANK.get(suffix, -1),
        )

    _BCG_ROSTER_RECORD_CACHE = records
    print(f"ゲーム内ロスター定義: {len(_BCG_ROSTER_RECORD_CACHE)} 件")
    return _BCG_ROSTER_RECORD_CACHE


def load_bcg_champion_tags() -> dict[str, list[str]]:
    """BCGのロスター定義から binary_id → チャンピオンタグID一覧を抽出する。"""
    global _BCG_CHAMPION_TAG_CACHE
    if _BCG_CHAMPION_TAG_CACHE is not None:
        return _BCG_CHAMPION_TAG_CACHE

    records = load_bcg_roster_records()
    _BCG_CHAMPION_TAG_CACHE = {
        binary_id: record.get("tags", [])
        for binary_id, record in records.items()
        if record.get("tags")
    }
    print(f"ゲーム内チャンピオンタグ: {len(_BCG_CHAMPION_TAG_CACHE)} 件")
    return _BCG_CHAMPION_TAG_CACHE


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
        return _clean_loc_text(value, preserve_glossary=True)

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


def _replace_percent_placeholder(text: str, idx: int, raw_value) -> str:
    """ローカライズ文の符号と実数値の符号が二重表示にならないよう置換する。"""
    formatted = _fmt_game_value(raw_value, True)
    if not formatted:
        return text
    abs_formatted = formatted[1:] if formatted[0] in "+-" else formatted

    def repl(match: _re.Match) -> str:
        prefix = match.group(1)
        if prefix == "+":
            return formatted if formatted.startswith("-") else f"+{abs_formatted}"
        if prefix == "-":
            return formatted if formatted.startswith("-") else f"-{abs_formatted}"
        return formatted

    return _re.sub(rf"([+-]?)\{{{idx}\}}%", repl, text)


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


def _variant_entry_score(entry: dict) -> tuple[int, int]:
    """同じ表示IDのランク別/星別エントリから、表示に使う代表を選ぶためのスコア。"""
    entry_id = str(entry.get("id", "")).lower()
    score = 0
    if entry_id.endswith("_200"):
        score = 200
    elif entry_id.endswith("_99"):
        score = 99
    elif entry_id.endswith("_5s"):
        score = 5
    elif entry_id.endswith("_4s"):
        score = 4
    return (score, len(entry_id))


def _prefer_signature_variant_entries(entries: list[dict]) -> list[dict]:
    """シグネチャー内で同じUI本文を参照する星/ランク違いを1つに絞る。"""
    best_by_ui: dict[str, dict] = {}
    order: list[str] = []
    passthrough: list[dict] = []
    for entry in entries:
        ui_id = entry.get("f12", "")
        if not ui_id:
            passthrough.append(entry)
            continue
        if ui_id not in best_by_ui:
            best_by_ui[ui_id] = entry
            order.append(ui_id)
            continue
        if _variant_entry_score(entry) > _variant_entry_score(best_by_ui[ui_id]):
            best_by_ui[ui_id] = entry
    return passthrough + [best_by_ui[ui_id] for ui_id in order]


def _prefer_category_entries(cat: str, entries: list[dict]) -> list[dict]:
    preferred = _prefer_rank_variant_entries(entries)
    if cat == "signature":
        preferred = _prefer_signature_variant_entries(preferred)
    return preferred


def _keep_entry_for_active_sections(cat: str, entry: dict, active_ids: set[str]) -> bool:
    if not active_ids or entry.get("id") in active_ids:
        return True
    return cat == "signature" and bool(entry.get("f12"))


def _is_signature_display_entry(cat: str, entry: dict) -> bool:
    ui_id = entry.get("f12", "")
    if not ui_id or ui_id.endswith(("_hud", "_icon")):
        return False
    return cat == "signature" or ui_id.startswith("sig_")


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
            result[cat] = _prefer_category_entries(cat, filtered)
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


def _filter_non_playable_variant_categories(cats: dict[str, list[dict]], binary_id: str) -> dict[str, list[dict]]:
    """同じability prefix内で複数キャラが混ざる場合、表示行をキャラ別に絞る。"""
    filters = SHARED_PREFIX_ABILITY_FILTERS.get(binary_id, {})
    include_entry_prefixes = tuple(filters.get("include_entry", ()))
    include_ui_prefixes = tuple(filters.get("include_ui", ()))
    exclude_entry_prefixes = tuple(filters.get("exclude_entry", ()))
    exclude_ui_prefixes = tuple(filters.get("exclude_ui", ()))
    if not any((include_entry_prefixes, include_ui_prefixes, exclude_entry_prefixes, exclude_ui_prefixes)):
        return cats

    result: dict[str, list[dict]] = {}
    for cat, entries in cats.items():
        filtered = []
        for entry in entries:
            entry_id = str(entry.get("id", "")).lower()
            ui_id = str(entry.get("f12", "")).lower()
            if include_entry_prefixes or include_ui_prefixes:
                if not (
                    (include_entry_prefixes and entry_id.startswith(include_entry_prefixes)) or
                    (include_ui_prefixes and ui_id.startswith(include_ui_prefixes))
                ):
                    continue
            if exclude_entry_prefixes and entry_id.startswith(exclude_entry_prefixes):
                continue
            if exclude_ui_prefixes and ui_id.startswith(exclude_ui_prefixes):
                continue
            filtered.append(entry)
        if filtered:
            result[cat] = filtered
    return result


def _section_text_count(sections: list[tuple[str, list[str]]]) -> int:
    return sum(len(texts) for _, texts in sections)


def _has_non_special_section(sections: list[tuple[str, list[str]]]) -> bool:
    return any(
        not title.startswith("必殺技") and not title.startswith("シグネチャー")
        for title, texts in sections
        if texts
    )


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


def _entry_targets_opponent(entry: dict) -> bool:
    return str(entry.get("f55", "")).lower() == "opponent"


OPPONENT_DEBUFF_TYPE_LABELS = {
    # BCG内部名がABILITY_TYPE_JPに無いが、ゲーム内では相手へ付与する弱体効果として表示されるもの。
    "buff_immunity": "バフ耐性",
    "hinder": "妨害",
    "fragility": "虚弱",
    "spectre": "怪異",
    "tranquilize": "鎮静化",
    "mana_loss": "パワードレイン",
    "mana_steal": "パワースティール",
    "provoke": "挑発",
    "panic": "パニック",
    "stifle": "窒息",
    "neurotoxin": "神経毒",
    "ineptitude": "不適当",
    "reckless": "無謀",
    "distract": "錯乱",
    "disintegrate_vuln": "崩壊弱点",
    "incin_vuln": "焼却弱点",
    "fear_of_the_void": "ボイドの恐怖",
    "agility_debuff": "機敏性デバフ",
}


def _opponent_debuff_label_from_entry(entry: dict,
                                      ui_index: dict[str, list[tuple[int, str]]],
                                      kv: dict) -> str:
    """相手に付与するデバフ/弱体効果として絞り込みに使う表示名を返す。"""
    if not _entry_targets_opponent(entry):
        return ""

    raw = entry.get("f2", "")
    display_title = ""
    display_texts: list[str] = []
    if kv:
        display_title, display_texts = _entry_display_text(entry, ui_index, kv)

    if display_title in DEBUFF_LABELS_JP:
        return display_title

    jp = OPPONENT_DEBUFF_TYPE_LABELS.get(raw) or ABILITY_TYPE_JP.get(raw, "")
    if not jp:
        return ""

    if raw in DEBUFF_TYPES or jp in DEBUFF_LABELS_JP or raw in OPPONENT_DEBUFF_TYPE_LABELS:
        return jp

    return ""


def _immunity_kind_from_entry(entry: dict) -> str:
    trigger = str(entry.get("f4", "")).lower()
    condition = str(entry.get("f11", "") or "").strip()
    state_gate = str(entry.get("f5", "") or "").strip()
    if condition or state_gate:
        return "conditional"
    if trigger in {"onstart", "always"}:
        return "full"
    return "conditional"


def _clean_game_text(value: str, entry: dict | None = None,
                     preserve_glossary: bool = False) -> str:
    value = _clean_loc_text(value, preserve_glossary=preserve_glossary)
    if entry:
        value = _replace_percent_placeholder(value, 0, entry.get("f13"))
        value = _replace_percent_placeholder(value, 1, entry.get("f14"))
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
        text = _clean_game_text(kv[key], entry, preserve_glossary=True)
        if text and len(text) > 5 and text not in texts:
            texts.append(text)

    if not texts and not prefer_simple:
        for tag, key in fields:
            if tag != 0x2a or key not in kv:
                continue
            text = _clean_game_text(kv[key], entry, preserve_glossary=True)
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


def _ui_description_text(ui_id: str, ui_index: dict[str, list[tuple[int, str]]], kv: dict) -> str:
    for tag, key in ui_index.get(ui_id, []):
        if tag not in (0x22, 0x2a, 0x32) or key not in kv:
            continue
        text = _clean_game_text(kv[key], preserve_glossary=True)
        if text:
            return text
    return ""


def _bladesf_signature_section(active_cats: dict[str, list[dict]],
                               ui_index: dict[str, list[tuple[int, str]]],
                               kv: dict) -> tuple[str, list[str]] | None:
    sig_entries = active_cats.get("signature", [])
    if not any(str(entry.get("id", "")).startswith("bladesf_sig_") for entry in sig_entries):
        return None

    title = "シグネチャー - 強化吸血不死"
    title_entry = next((entry for entry in sig_entries if entry.get("f12") == "bladesf_ui_sig_regen"), {})
    if title_entry:
        title = _signature_section_title(title_entry.get("f12", ""), ui_index, kv) or title

    texts: list[str] = []
    for ui_id in ("bladesf_regenblk_trig", "bladesf_regenblk_hud"):
        text = _ui_description_text(ui_id, ui_index, kv)
        if text and text not in texts:
            texts.append(text)
    return (title, texts) if texts else None


def _localized_signature_section(loc_prefixes: list[str], kv: dict) -> tuple[str, list[str]] | None:
    """Some newer champions store signature text as PREFIX_SIG_1/2 without a UI index link."""
    skip_suffixes = {"TITLE", "TITLE_LOWER", "SHORT", "HUD", "ICON", "CALLOUT"}

    def suffix_order(suffix: str) -> tuple[int, str]:
        if suffix.isdigit():
            return (int(suffix), suffix)
        if len(suffix) == 1 and suffix.isalpha():
            return (100 + ord(suffix.upper()), suffix)
        return (500, suffix)

    for prefix in loc_prefixes:
        if not prefix:
            continue
        title = "シグネチャー"
        for key in (
            f"ID_UI_{prefix}_SIG_TITLE",
            f"ID_UI_STAT_FORMAT_{prefix}_SIG_TITLE",
            f"ID_UI_STAT_ATTRIBUTE_{prefix}_SIG_TITLE",
            f"ID_STAT_ATTRIBUTE_{prefix}_SIG_TITLE",
            f"ID_UI_STAT_SIGNATURE_{prefix}_TITLE",
        ):
            if key in kv:
                clean_title = _clean_game_text(kv[key])
                if clean_title:
                    title = f"シグネチャー - {clean_title}"
                    break

        ordered_texts: list[tuple[tuple[int, str], str]] = []
        for head in (
            f"ID_UI_STAT_FORMAT_{prefix}_SIG_",
            f"ID_UI_STAT_ATTRIBUTE_{prefix}_SIG_",
            f"ID_STAT_ATTRIBUTE_{prefix}_SIG_",
        ):
            for key, value in kv.items():
                if not key.startswith(head):
                    continue
                suffix = key[len(head):]
                if suffix in skip_suffixes or suffix.endswith(("_TITLE", "_SHORT", "_HUD", "_ICON", "_CALLOUT")):
                    continue
                text = _clean_game_text(value, preserve_glossary=True)
                if text and len(text) > 5:
                    ordered_texts.append((suffix_order(suffix), text))

        texts: list[str] = []
        for _, text in sorted(ordered_texts, key=lambda item: item[0]):
            if text not in texts:
                texts.append(text)
        if texts:
            return title, texts
    return None


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
            return _clean_game_text(kv[key], preserve_glossary=True)
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
        first_lower in {"none", "onstart", "onentermatch", "onabilityactivate", "ontypeactivate"} or
        first_lower.endswith(".ontypeactivate")
    )
    raw_tokens = [second, first] if second and generic_first else [first, second]
    result: list[str] = []
    for raw in raw_tokens:
        token = _re.sub(r"[^A-Za-z0-9_]+", "", raw).upper()
        compact_token = _re.sub(r"[^A-Za-z0-9]+", "", raw).upper()
        for candidate in (token, compact_token):
            if candidate and candidate != "NONE" and candidate not in result:
                result.append(candidate)
    return result


def _localized_event_section_title(entry: dict, kv: dict) -> str:
    """ゲーム内ローカライズ済みの発動条件見出しを返す。"""
    group_title = _localized_group_section_title(entry, kv)
    if group_title:
        return group_title

    for token in _event_trigger_tokens(entry):
        key = f"ID_UI_STAT_ATTRIBUTE_TRIGGER_SUBTITLE_{token}"
        if key in kv:
            title = strip_loc_tags(kv[key])
            if title:
                return title
    return ""


def _localized_group_section_title(entry: dict, kv: dict) -> str:
    """f5に入るゲーム内グループ見出しを、イベント名より優先して返す。"""
    raw = str(entry.get("f5", "") or "")
    token = _re.sub(r"[^A-Za-z0-9_]+", "", raw).upper()
    if not token or token == "NONE" or "_" not in token:
        return ""
    key = f"ID_UI_STAT_ATTRIBUTE_TRIGGER_SUBTITLE_{token}"
    if key not in kv:
        return ""
    title = strip_loc_tags(kv[key])
    return title.strip()


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
        filtered = [e for e in entries if _keep_entry_for_active_sections(cat, e, active_ids)]
        if filtered:
            active_cats[cat] = _prefer_category_entries(cat, filtered)
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
    signature_entries: list[dict] = []
    for cat, entries in active_cats.items():
        for entry in entries:
            if _is_signature_display_entry(cat, entry):
                signature_entries.append(entry)

    signature_fallback_title = ""
    for entry in signature_entries:
        display_title = _signature_section_title(entry.get("f12", ""), ui_index, kv)
        if display_title and display_title != "シグネチャー":
            signature_fallback_title = display_title
            break

    signature_texts_by_title: dict[str, list[str]] = {}
    for entry in signature_entries:
        ui_id = entry.get("f12", "")
        _, texts = _entry_display_text(entry, ui_index, kv)
        if not texts:
            continue
        display_title = _signature_section_title(ui_id, ui_index, kv)
        if display_title == "シグネチャー" and signature_fallback_title:
            display_title = signature_fallback_title
        bucket = signature_texts_by_title.setdefault(display_title, [])
        for text in texts:
            if text not in bucket:
                bucket.append(text)
    bladesf_signature = _bladesf_signature_section(active_cats, ui_index, kv)
    if bladesf_signature:
        title, texts = bladesf_signature
        bucket = signature_texts_by_title.setdefault(title, [])
        for text in texts:
            if text not in bucket:
                bucket.append(text)
    localized_signature = (
        _localized_signature_section(loc_prefixes, kv)
        if active_cats.get("signature") and not signature_texts_by_title
        else None
    )
    if localized_signature:
        title, texts = localized_signature
        bucket = signature_texts_by_title.setdefault(title, [])
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
            group_title = _localized_group_section_title(entry, kv)
            if _entry_special_indices(entry) and not group_title:
                continue
            ui_id = entry.get("f12", "")
            if not ui_id or ui_id.startswith("sig_") or ui_id.endswith(("_hud", "_icon")):
                continue
            title, texts = _entry_display_text(entry, ui_index, kv)
            if not texts:
                continue
            section_title = _all_attacks_section_title(entry) or group_title or _always_active_section_title(entry) or _event_section_title(entry, kv) or _trigger_section_title(entry) or title or normal_titles.get(cat) or "能力補足"
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
                if _localized_group_section_title(entry, kv):
                    continue
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


def build_game_ability_sections_html(sections: list[tuple[str, list[str]]],
                                     glossary_defs: dict[str, dict[str, str]] | None = None) -> str:
    """能力説明を単一の「能力」アコーディオン内に平坦表示する"""
    if not sections:
        return ""

    glossary_defs = glossary_defs or {}
    groups: list[str] = []
    for title, texts in sections:
        safe_title = render_ability_text_html(title, glossary_defs)
        text_li = "".join(f'<li>{render_ability_text_html(t, glossary_defs)}</li>' for t in texts if t)
        if not text_li:
            continue
        groups.append(
            f'<div class="gd-ability-group">'
            f'<div class="gd-ability-title">{safe_title}</div>'
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
    glossary_defs = get_glossary_definitions(kv) if kv else {}
    if not prefix or prefix not in abilities:
        sections = get_champion_sections(loc_prefix, kv, legacy_loc_prefixes) if kv else []
        sections_html = build_game_ability_sections_html(sections, glossary_defs)
        if not sections_html:
            return ""
        return f"""<div class="gd-sec">
  {sections_html}
</div>"""

    cats = _filter_non_playable_variant_categories(
        _merged_ability_categories(abilities, prefix),
        binary_id,
    )
    active_by_binary, active_by_prefix = load_bcg_active_ability_ids(abilities)
    active_ids = set(active_by_binary.get(binary_id, set()) or active_by_prefix.get(prefix, set()))
    active_ids.update(_supplemental_ability_ids(abilities, prefix))
    active_cats = {
        cat: _prefer_category_entries(cat, [entry for entry in entries if _keep_entry_for_active_sections(cat, entry, active_ids)])
        for cat, entries in cats.items()
    }
    active_cats = _prefer_rank_variant_categories(active_cats)

    # ローカライズ説明セクション。BCGの有効ID検出がプリファイトなどに寄って
    # 本体能力を落とす場合だけ、同じゲーム内prefixの全表示行へフォールバックする。
    sections: list[tuple[str, list[str]]] = []
    section_cats = active_cats
    manual_section_builder = {
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
    opponent_debuff_badges: list[str] = []
    opponent_debuff_seen: set[str] = set()
    immune_badges: list[tuple[str, str]] = []
    other_badges:  list[str] = []
    ui_index = load_bcg_ui_stat_index()

    for e in all_entries:
        opponent_debuff_jp = _opponent_debuff_label_from_entry(e, ui_index, kv or {})
        if opponent_debuff_jp and opponent_debuff_jp not in opponent_debuff_seen:
            opponent_debuff_seen.add(opponent_debuff_jp)
            opponent_debuff_badges.append(opponent_debuff_jp)

        immune_jps = [] if _entry_targets_opponent(e) else _immune_badges_from_entry(e)
        if immune_jps:
            for immune_jp in immune_jps:
                if immune_jp not in seen_set:
                    seen_set.add(immune_jp)
                    immune_badges.append((immune_jp, _immunity_kind_from_entry(e)))
            continue
        if not e.get("f12"):
            continue
        raw = e.get("f2", "")
        if not raw or raw in SKIP_F2:
            continue
        jp = ABILITY_TYPE_JP.get(raw, None)
        display_title = ""
        display_texts: list[str] = []
        if kv:
            display_title, display_texts = _entry_display_text(e, ui_index, kv)
        if display_title in BUFF_LABELS_JP or display_title in DEBUFF_LABELS_JP:
            jp = display_title
        if jp is None:
            continue
        jp = _resistance_badge_label_from_display(raw, jp, display_title, display_texts)
        if jp in seen_set:
            continue
        seen_set.add(jp)
        if raw.endswith("_immune") or raw.endswith("_immunity"):
            if _entry_targets_opponent(e):
                debuff_badges.append(jp)
            else:
                immune_badges.append((jp, _immunity_kind_from_entry(e)))
        elif jp in BUFF_LABELS_JP or raw in BUFF_TYPES:
            buff_badges.append(jp)
        elif jp in DEBUFF_LABELS_JP or raw in DEBUFF_TYPES:
            debuff_badges.append(jp)
        else:
            other_badges.append(jp)

    def badges(items: list[str], css: str) -> str:
        return "".join(f'<span class="abi-badge {css}">{jp}</span>' for jp in items)

    def immune_badges_html(items: list[tuple[str, str]]) -> str:
        return "".join(
            f'<span class="abi-badge abi-immune" data-resistance-kind="{kind}">{jp}</span>'
            for jp, kind in items
        )

    all_badges_html = (
        badges(buff_badges,   "abi-buff") +
        badges(debuff_badges, "abi-debuff") +
        badges(other_badges,  "abi-neutral")
    )

    # 免疫・耐性セクション
    raw_immune_html = ""
    if immune_badges:
        imm = immune_badges_html(immune_badges)
        raw_immune_html = (
            '<div class="gd-immune">'
            '<span class="gd-sublabel">耐性</span>'
            f'<div class="gd-badges">{imm}</div>'
            '</div>'
        )

    sections_html = build_game_ability_sections_html(sections, glossary_defs)
    immune_html = raw_immune_html
    if raw_immune_html or sections_html:
        resistance_items = extract_resistance_items_from_game_data_html(
            f'<div class="gd-sec">{raw_immune_html}{sections_html}</div>'
        )
        full_items = list(dict.fromkeys(resistance_items["full"]))
        conditional_items = [
            item
            for item in dict.fromkeys(resistance_items["conditional"])
            if item not in full_items
        ]

        def resistance_group_html(label: str, items: list[str]) -> str:
            if not items:
                return ""
            kind = "conditional" if label == "条件付き耐性" else "full"
            return (
                '<div class="gd-immune">'
                f'<span class="gd-sublabel">{label}</span>'
                f'<div class="gd-badges">{immune_badges_html([(item, kind) for item in items])}</div>'
                '</div>'
            )

        classified_immune_html = (
            resistance_group_html("完全耐性", full_items) +
            resistance_group_html("条件付き耐性", conditional_items)
        )
        if classified_immune_html:
            immune_html = classified_immune_html

    abilities_html = (
        '<div class="gd-abilities">\n'
        '    <span class="gd-sublabel">アビリティ</span>\n'
        f'    <div class="gd-badges">{all_badges_html}</div>\n'
        '  </div>'
        if all_badges_html else ""
    )

    if not (abilities_html or immune_html or sections_html):
        return ""

    opponent_debuff_search = html.escape("|".join(opponent_debuff_badges))
    return f"""<div class="gd-sec">
<div class="gd-meta" hidden data-opponent-debuffs="{opponent_debuff_search}"></div>
  {abilities_html}
  {immune_html}
  {sections_html}
</div>"""


_RESISTANCE_TERM_MAP = [
    ("防御ブレイカー", "防御ブレーカー"),
    ("防御ブレーカー", "防御ブレーカー"),
    ("防御不能な必殺技", "防御不能"),
    ("防御不能な攻撃", "防御不能"),
    ("防御不能の攻撃", "防御不能"),
    ("防御不能攻撃", "防御不能"),
    ("防御不能", "防御不能"),
    ("リバース・コントロール", "リバース・コントロール"),
    ("リバースコントロール", "リバース・コントロール"),
    ("経時的ダメージ効果", "経時的ダメージ効果"),
    ("パワースティール", "パワースティール"),
    ("パワー・スティール", "パワースティール"),
    ("パワードレイン", "パワードレイン"),
    ("パワーバーン", "パワーバーン"),
    ("パワーロック", "パワーロック"),
    ("必殺技ロック", "必殺技ロック"),
    ("必殺ロック", "必殺技ロック"),
    ("パワー操作全般", "パワー操作"),
    ("パワー操作", "パワー操作"),
    ("ヒールブロック", "ヒールブロック"),
    ("回復ブロック", "ヒールブロック"),
    ("アーマー破壊", "アーマー破壊"),
    ("アーマー粉砕", "アーマー粉砕"),
    ("コールドスナップ", "コールドスナップ"),
    ("フロストバイト", "フロストバイト"),
    ("ノヴァ・フレイム", "ノヴァ・フレイム"),
    ("スキル精度変更", "スキル精度変更"),
    ("スキル精度低減", "スキル精度変更"),
    ("スキル精度の影響", "スキル精度変更"),
    ("スキル精度", "スキル精度変更"),
    ("リバース", "リバース・コントロール"),
    ("運命封印", "運命封印"),
    ("運命刻印", "運命封印"),
    ("無効化", "無効化"),
    ("よろめき", "よろめき"),
    ("中和", "中和"),
    ("断裂", "断裂"),
    ("スロー", "スロー"),
    ("弱体化", "弱体化"),
    ("停留", "固定"),
    ("固定", "固定"),
    ("押し潰し", "押し潰し"),
    ("挑発", "挑発"),
    ("威圧", "威圧"),
    ("激昂", "激昂"),
    ("ひるみ", "ひるみ"),
    ("怪異", "怪異"),
    ("疲労", "疲労"),
    ("極度の疲労", "極度の疲労"),
    ("脳震とう", "脳震盪"),
    ("脳震盪", "脳震盪"),
    ("衰え", "衰え"),
    ("消滅", "消滅"),
    ("崩壊", "崩壊"),
    ("化石化", "化石化"),
    ("回復率変更", "回復率変更"),
    ("ダメージ効果", "ダメージ効果"),
    ("死への耐性", "死への耐性"),
    ("気絶", "気絶"),
    ("流血", "流血"),
    ("出血", "流血"),
    ("毒", "毒"),
    ("焼却", "焼却"),
    ("放火", "焼却"),
    ("ショック", "ショック"),
    ("衝撃", "ショック"),
    ("凍傷", "フロストバイト"),
]
_RESISTANCE_TERM_MAP.sort(key=lambda item: len(item[0]), reverse=True)
_RESISTANCE_MARKERS = (
    "耐性", "免疫", "受けない", "影響を受けない", "効果を受けない",
    "ダメージを受けない", "防御でき", "防御が可能", "抵抗できる",
    "抵抗する", "抵抗力を持つ", "完全に身を守る", "完全に防ぐ",
    "効果を無効化", "効果を無効に", "デバフによるダメージ",
    "変更不可能", "変動せず", "変更されない", "低下させることができない",
)
_RESISTANCE_SKIP_LABELS = {"耐性低下"}
_FULL_RESISTANCE_TITLE_MARKERS = ("常時発動", "常に発動", "常時稼働", "常時")
_CONDITIONAL_RESISTANCE_TITLE_MARKERS = (
    "シグネチャー", "必殺技", "強攻撃", "弱攻撃", "中攻撃", "防御中", "攻撃中",
    "攻撃を受けた", "ブロック", "フォーム", "形態", "フェーズ", "発動中",
    "シナジー", "戦闘前",
)
_CONDITIONAL_RESISTANCE_TEXT_MARKERS = (
    "発動中", "発動している間", "持っている間", "中は", "場合", "時、", "とき",
    "間、", "している間", "対して", "ヒーロー", "属性", "以外", "防御中",
    "攻撃中", "必殺技", "フォーム", "形態", "シグネチャー", "戦闘前", "チーム",
    "シナジー", "発動すると", "発動時", "チャージ中", "受けると",
    "受けたとき", "中に", "強攻撃", "オートブロック", "防御でき",
    "防御が可能", "抵抗できる", "抵抗すると", "との対戦", "対戦では",
)
_FULL_RESISTANCE_TEXT_MARKERS = (
    "完全な耐性", "完全な免疫", "免疫を持つ", "効果を受けない",
    "ダメージを受けない", "完全に身を守る", "完全に防ぐ",
)
_WEAK_CONDITIONAL_RESISTANCE_TITLE_MARKERS = {"フォーム", "形態"}
_WEAK_CONDITIONAL_RESISTANCE_TEXT_MARKERS = {"フォーム", "形態", "対して"}


def _resistance_label(canon: str) -> str:
    if not canon:
        return ""
    if canon.endswith("耐性"):
        return canon
    return f"{canon}耐性"


def _normalize_resistance_label(label: str) -> str:
    label = html.unescape(label).strip()
    label = label.rstrip("：:")
    label = label.replace("出血耐性", "流血耐性")
    label = label.replace("凍傷耐性", "フロストバイト耐性")
    label = label.replace("必殺ロック耐性", "必殺技ロック耐性")
    label = label.replace("回復ブロック耐性", "ヒールブロック耐性")
    label = label.replace("防御ブレイカー耐性", "防御ブレーカー耐性")
    return label


def _resistance_badge_label_from_display(raw: str, fallback: str,
                                         display_title: str,
                                         display_texts: list[str]) -> str:
    display = " ".join([display_title, *display_texts])
    if raw == "unblockable_immune" and _re.search(r"防御ブレ[イー]カー", display):
        return "防御ブレーカー耐性"
    title_label = _normalize_resistance_label(display_title)
    if title_label.endswith("耐性") or title_label == "死への耐性":
        return title_label
    return _normalize_resistance_label(fallback)


def _add_resistance_label(groups: dict[str, list[str]], seen: set[tuple[str, str]],
                          label: str, kind: str) -> None:
    label = _normalize_resistance_label(label)
    if not label or label in _RESISTANCE_SKIP_LABELS:
        return
    if not (label.endswith("耐性") or label == "死への耐性"):
        return
    kind = "conditional" if kind == "conditional" else "full"
    key = (kind, label)
    if key not in seen:
        seen.add(key)
        groups[kind].append(label)


def _resistance_kind(title: str, segment: str) -> str:
    title = title.strip()
    segment = segment.strip()
    title_conditional_markers = {
        marker for marker in _CONDITIONAL_RESISTANCE_TITLE_MARKERS
        if marker in title
    }
    hard_title_conditional_markers = (
        title_conditional_markers - _WEAK_CONDITIONAL_RESISTANCE_TITLE_MARKERS
    )
    if hard_title_conditional_markers:
        return "conditional"
    full_text = any(marker in segment for marker in _FULL_RESISTANCE_TEXT_MARKERS)
    conditional_markers = {
        marker for marker in _CONDITIONAL_RESISTANCE_TEXT_MARKERS
        if marker in segment
    }
    hard_conditional_markers = conditional_markers - _WEAK_CONDITIONAL_RESISTANCE_TEXT_MARKERS
    if full_text and not hard_conditional_markers:
        return "full"
    if any(marker in segment for marker in _CONDITIONAL_RESISTANCE_TEXT_MARKERS):
        return "conditional"
    if any(marker in title for marker in _FULL_RESISTANCE_TITLE_MARKERS):
        return "full"
    if full_text:
        return "full"
    return "conditional"


def _looks_like_opponent_resistance_condition(segment: str) -> bool:
    """相手側の耐性を条件にした説明を、自分の耐性として拾わない。"""
    if "対戦相手による" in segment or "相手から受ける" in segment:
        return False
    if _re.search(r"(対戦相手|相手|敵)が[^。]{0,45}耐性", segment):
        return True
    if _re.search(r"(対戦相手|相手|敵)は[^。]{0,45}(耐性|免疫)", segment):
        return True
    if _re.search(r"(対戦相手|相手|敵)に[^。]{0,30}耐性[^。]{0,12}(付与|食らわせる|与える)", segment):
        return True
    if "耐性デバフ" in segment and any(word in segment for word in ("付与", "食らわせる", "与える")):
        return True
    return False


def _resistance_text_segments(text: str) -> list[str]:
    chunks = _re.split(r"(?<=。)|[；;]", text)
    result: list[str] = []
    for chunk in chunks:
        parts = _re.split(r"(?:さらに、|また、|加え、|、?非接触攻撃に対して)", chunk)
        for part in parts:
            part = part.strip()
            if part and any(marker in part for marker in _RESISTANCE_MARKERS):
                result.append(part)
    return result


def extract_resistance_items_from_game_data_html(game_data_html: str) -> dict[str, list[str]]:
    """表示本文・バッジから、完全耐性/条件付き耐性を正規化して抽出する。"""
    groups: dict[str, list[str]] = {"full": [], "conditional": []}
    seen: set[tuple[str, str]] = set()
    badge_labels: list[tuple[str, str]] = []

    for badge in _re.finditer(r'<span class="abi-badge abi-immune"([^>]*)>([^<]+)</span>', game_data_html):
        attrs = badge.group(1)
        label = _normalize_resistance_label(badge.group(2))
        kind_match = _re.search(r'data-resistance-kind="(full|conditional)"', attrs)
        explicit_kind = kind_match.group(1) if kind_match else ""
        if label.endswith("耐性") or label == "死への耐性":
            badge_labels.append((label, explicit_kind))

    group_re = _re.compile(
        r'<div class="gd-ability-group"><div class="gd-ability-title">(.*?)</div>'
        r'<ul class="gd-texts">(.*?)</ul></div>',
        _re.S,
    )
    for group in group_re.finditer(game_data_html):
        title = html.unescape(_re.sub(r"<.*?>", "", group.group(1))).strip()
        for li in _re.finditer(r"<li>(.*?)</li>", group.group(2), _re.S):
            text = html.unescape(_re.sub(r"<.*?>", "", li.group(1))).strip()
            if not any(marker in text for marker in _RESISTANCE_MARKERS):
                continue
            for segment in _resistance_text_segments(text):
                if _looks_like_opponent_resistance_condition(segment):
                    continue
                kind = _resistance_kind(title, segment)
                for raw, canon in _RESISTANCE_TERM_MAP:
                    if raw in segment:
                        if canon == "無効化" and _re.search(r"効果を無効化", segment):
                            continue
                        _add_resistance_label(groups, seen, _resistance_label(canon), kind)
                if "スティール" in segment and "パワー" in segment:
                    _add_resistance_label(groups, seen, "パワースティール耐性", kind)
                if "バーン" in segment and "パワー" in segment:
                    _add_resistance_label(groups, seen, "パワーバーン耐性", kind)
                if _re.search(r"(バフ耐性|バフへの耐性|バフに対する耐性|バフの影響を受けず)", segment):
                    _add_resistance_label(groups, seen, "バフ耐性", kind)
                if _re.search(r"(デバフ耐性|デバフへの耐性|デバフに対する耐性)", segment):
                    _add_resistance_label(groups, seen, "デバフ耐性", kind)

    text_full = set(groups["full"])
    text_conditional = set(groups["conditional"])
    for label, explicit_kind in badge_labels:
        if (
            label == "防御不能耐性"
            and "防御不能耐性" not in text_full
            and "防御不能耐性" not in text_conditional
            and (
                "防御ブレーカー耐性" in text_full
                or "防御ブレーカー耐性" in text_conditional
            )
        ):
            continue
        if label in text_conditional and label not in text_full:
            kind = "conditional"
        elif label in text_full:
            kind = "full"
        elif explicit_kind in {"full", "conditional"}:
            kind = explicit_kind
        elif label == "防御不能耐性":
            kind = "conditional"
        else:
            kind = "full"
        _add_resistance_label(groups, seen, label, kind)

    return groups


def load_champion_class_map() -> dict[str, str]:
    """BCGロスター定義から binary_id → class を返す。失敗時のみ旧抽出ファイルへ戻す。"""
    roster_records = load_bcg_roster_records()
    if roster_records:
        class_map = {
            binary_id: record.get("champion_class", "")
            for binary_id, record in roster_records.items()
            if record.get("champion_class")
        }
        print(f"ゲーム内クラス定義: {len(class_map)} 件（BCGロスター）")
        return class_map

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
    class_map.update(CLASS_FALLBACKS)
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
    if binary_id == "phylavell":
        return "Phyla-Vell"
    return " ".join(part.upper() if part in {"x", "x23"} else part.capitalize() for part in binary_id.split("_"))


def infer_jp_name_from_bio(binary_id: str, kv: dict) -> str:
    """champion_namesに無い新規IDの表示名を、ゲーム内バイオ文から最小限補完する。"""
    legacy = _legacy_loc_prefix_from_binary_id(binary_id)
    bio = strip_loc_tags(kv.get(f"ID_CHARACTER_BIOS_{legacy}", "")).strip()
    if not bio:
        return ""
    patterns = (
        r"として生まれた([^、。]{2,30})は",
        r"存在、([^、。]{2,30})は",
        r"^([^、。]{2,30})は",
    )
    for pattern in patterns:
        match = _re.search(pattern, bio)
        if match:
            name = match.group(1).strip()
            if name:
                return name
    return ""


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


def resolve_direct_portrait(binary_id: str, direct_portraits: dict[str, str]) -> str:
    alias = PORTRAIT_BINARY_ID_ALIASES.get(binary_id.lower())
    if alias and (BASE / "data" / "portraits" / alias).exists():
        return alias
    return direct_portraits.get(binary_id.lower(), "") or direct_portraits.get(_portrait_key(binary_id), "")


def load_game_only_champions(abilities: dict, kv: dict, name_jp_map: dict) -> tuple[list[dict], dict, dict]:
    """スポットライトCSVを使わず、ゲーム内抽出データだけでチャンピオン一覧を構築する"""
    class_map = load_champion_class_map()
    roster_records = load_bcg_roster_records()
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

    for binary_id, cls in sorted(class_map.items()):
        record = roster_records.get(binary_id, {})
        if roster_records:
            if not is_game_playable_roster_record(binary_id, record):
                continue
            cls = record.get("champion_class", cls)
        elif not is_playable_binary_id(binary_id):
            continue
        prefix = "" if binary_id in NO_GAME_ABILITY_PREFIX_BINARY_IDS else binary_to_prefix.get(binary_id, "")
        if prefix and prefix in used_prefixes and binary_id not in ALLOW_DUPLICATE_PREFIX_BINARY_IDS:
            continue

        name_info = champion_name_data.get(binary_id, {})
        name_jp = name_info.get("jp", "") or infer_jp_name_from_bio(binary_id, kv)
        name_en = name_info.get("en", "") or _name_from_binary_id(binary_id)
        dedupe_name = (name_jp or name_en).lower()
        if dedupe_name in used_names:
            continue

        portrait = resolve_direct_portrait(binary_id, direct_portraits)
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
            "legacy_loc_prefixes": list(dict.fromkeys(
                [_legacy_loc_prefix_from_binary_id(binary_id)] +
                list(LOC_PREFIX_ALIASES.get(binary_id, ()))
            )),
            "binary_id": binary_id,
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
            _fname = resolve_direct_portrait(_bid, _direct_portraits)
            if _jp and _fname:
                _norm_to_portrait[_norm_jp(_jp)] = _fname
    _game_synergy_defs, _game_synergies_by_binary = load_bcg_synergy_index()
    _game_tags_by_binary = load_bcg_champion_tags()
    _tag_labels = load_champion_tag_labels()

    def _binary_id_for_card(c: dict, name_jp: str, name_en: str) -> str:
        slug = c.get("slug", "")
        candidates = [
            c.get("binary_id", ""),
            name_jp_map.get(slug, {}).get("binary_id", ""),
            slug.removeprefix("game-roster-").replace("-", "_") if slug.startswith("game-roster-") else "",
            _name_to_binary.get(_norm_jp(name_jp), ""),
            _name_to_binary.get(_norm_jp(name_en), ""),
        ]
        expanded_candidates: list[str] = []
        for candidate in candidates:
            if not candidate:
                continue
            expanded_candidates.append(candidate)
            alias = ROSTER_BINARY_ID_ALIASES.get(candidate, "")
            if alias:
                expanded_candidates.append(alias)
        for candidate in expanded_candidates:
            if candidate and (candidate in _game_synergies_by_binary or candidate in _game_tags_by_binary):
                return candidate
        return next((candidate for candidate in expanded_candidates if candidate), "")

    def _ability_binary_id_for_card(c: dict, name_jp: str, name_en: str) -> str:
        slug = c.get("slug", "")
        candidates = [
            c.get("binary_id", ""),
            name_jp_map.get(slug, {}).get("binary_id", ""),
            slug.removeprefix("game-roster-").replace("-", "_") if slug.startswith("game-roster-") else "",
            _name_to_binary.get(_norm_jp(name_jp), ""),
            _name_to_binary.get(_norm_jp(name_en), ""),
        ]
        return next((candidate for candidate in candidates if candidate), "")

    def _portrait_for_binary_id(binary_id: str) -> str:
        if not binary_id:
            return ""
        info = _names_data.get(binary_id, {}) if isinstance(_names_data, dict) else {}
        return (
            resolve_direct_portrait(binary_id, _direct_portraits) or
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
            _portrait = resolve_direct_portrait(_bid, _direct_portraits)
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

        # シナジー
        binary_id = _binary_id_for_card(c, name_jp, name_en)
        ability_binary_id = _ability_binary_id_for_card(c, name_jp, name_en) or binary_id
        syn_list: list[tuple[str, str, list[str]]] = _game_synergy_entries_for_binary(binary_id)

        tag_keys = _game_tags_by_binary.get(binary_id, [])
        tag_items: list[str] = []
        seen_tags: set[str] = set()
        for tag_key in tag_keys:
            tag_name = format_roster_tag_label(tag_key, _tag_labels)
            if tag_name and tag_name not in seen_tags:
                tag_items.append(tag_name)
                seen_tags.add(tag_name)
        for attr in attrs:
            attr_name = ATTR_JP.get(attr, attr)
            if attr_name and attr_name not in seen_tags:
                tag_items.append(attr_name)
                seen_tags.add(attr_name)
        year_items = [
            match.group(1)
            for tag_key in tag_keys
            for match in [_re.fullmatch(r"tg_(20\d{2})", tag_key)]
            if match
        ]
        tag_html = (
            f'<details class="tag-details"><summary>タグ一覧（{len(tag_items)}件）</summary>' +
            '<div class="tags-row">' +
            ''.join(f'<span class="tag-badge">{tag}</span>' for tag in tag_items) +
            '</div></details>'
            if tag_items else ""
        )
        tag_search = " ".join(tag_keys + tag_items)
        year_search = " ".join(year_items)

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
                f'<img class="syn-portrait" src="{PORTRAIT_SRC_DIR}/{p}" alt="">'
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
        game_loc_prefix_map = loc_prefix_map
        if c.get("loc_prefix") and not (loc_prefix_map or {}).get(slug):
            game_loc_prefix_map = dict(loc_prefix_map or {})
            game_loc_prefix_map[slug] = c["loc_prefix"]
        game_data_html = build_game_data_html(
            slug, abilities, slug_map, game_loc_prefix_map, kv,
            c.get("legacy_loc_prefixes", []), ability_binary_id
        )
        opponent_debuff_match = _re.search(r'data-opponent-debuffs="([^"]*)"', game_data_html)
        opponent_debuff_search = (
            html.unescape(opponent_debuff_match.group(1))
            if opponent_debuff_match else ""
        )
        resistance_items = extract_resistance_items_from_game_data_html(game_data_html)
        full_immunity_items = list(dict.fromkeys(resistance_items["full"]))
        conditional_immunity_items = [
            item
            for item in dict.fromkeys(resistance_items["conditional"])
            if item not in full_immunity_items
        ]
        immunity_search = "|".join(dict.fromkeys(full_immunity_items + conditional_immunity_items))
        full_immunity_search = "|".join(full_immunity_items)
        conditional_immunity_search = "|".join(conditional_immunity_items)

        portrait_html = (
            f'<img class="champ-portrait" src="{PORTRAIT_SRC_DIR}/{portrait_fname}" alt="{name_en}">'
            if portrait_fname else '<div class="champ-portrait champ-portrait-none"></div>'
        )

        en_sub = f'<span class="champ-en">{name_en}</span>' if name_jp else ""
        release_html = f'<div class="release">リリース: {release}</div>' if release else ""
        card = f"""
<div class="card" data-slug="{slug}" data-binary-id="{html.escape(binary_id)}" data-class="{cls}" data-years="{year_search}" data-immunities="{html.escape(immunity_search)}" data-immunities-full="{html.escape(full_immunity_search)}" data-immunities-conditional="{html.escape(conditional_immunity_search)}" data-debuffs="{html.escape(opponent_debuff_search)}" data-name="{html.escape((name_jp + ' ' + name_en + ' ' + tag_search + ' ' + opponent_debuff_search.replace('|', ' ')).lower())}">
  <div class="card-header" style="border-left:4px solid {color}">
    <div class="title-row">
      {portrait_html}
      <div class="champ-title"><h2 class="champ-name">{name}</h2>{en_sub}</div>
      <span class="cls-badge" style="background:{color}">{class_jp}</span>
    </div>
    {release_html}
  </div>
  <div class="card-body">
    {game_data_html}
    {'<details class="syn-details"><summary>シナジー一覧（' + str(len(syn_list)) + '件）</summary><ul class="syn-list">' + syn_items + '</ul></details>' if syn_items else ''}
    {tag_html}
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

    filter_btns = '<button class="f-btn class-btn active" data-class="all">すべて</button>\n'
    for cls in classes:
        color = CLASS_COLORS.get(cls, "#607D8B")
        jp    = CLASS_JP.get(cls, cls)
        filter_btns += (
            f'<button class="f-btn class-btn" data-class="{cls}" '
            f'style="--cc:{color}">{jp}</button>\n'
        )

    cards_html = build_cards(champions, cache, abilities, slug_map, name_jp_map, loc_prefix_map, kv, portrait_map)
    years = sorted(set(_re.findall(r'data-years="[^"]*\b(20\d{2})\b[^"]*"', cards_html)))
    year_btns = '<button class="f-btn year-btn active" data-year="all">全年</button>\n'
    for year in years:
        year_btns += f'<button class="f-btn year-btn" data-year="{year}">{year}</button>\n'
    full_immunity_values: set[str] = set()
    for raw in _re.findall(r'data-immunities-full="([^"]*)"', cards_html):
        for item in html.unescape(raw).split("|"):
            if item:
                full_immunity_values.add(item)
    conditional_immunity_values: set[str] = set()
    for raw in _re.findall(r'data-immunities-conditional="([^"]*)"', cards_html):
        for item in html.unescape(raw).split("|"):
            if item:
                conditional_immunity_values.add(item)
    full_immunity_btns = '<button class="f-btn immunity-btn full-immunity-btn active" data-full-immunity="all">指定なし</button>\n'
    for item in sorted(full_immunity_values):
        safe_item = html.escape(item)
        full_immunity_btns += f'<button class="f-btn immunity-btn full-immunity-btn" data-full-immunity="{safe_item}">{safe_item}</button>\n'
    conditional_immunity_btns = '<button class="f-btn immunity-btn conditional-immunity-btn active" data-conditional-immunity="all">指定なし</button>\n'
    for item in sorted(conditional_immunity_values):
        safe_item = html.escape(item)
        conditional_immunity_btns += f'<button class="f-btn immunity-btn conditional-immunity-btn" data-conditional-immunity="{safe_item}">{safe_item}</button>\n'
    opponent_debuff_values: set[str] = set()
    for raw in _re.findall(r'data-debuffs="([^"]*)"', cards_html):
        for item in html.unescape(raw).split("|"):
            if item:
                opponent_debuff_values.add(item)
    opponent_debuff_btns = '<button class="f-btn debuff-btn active" data-debuff="all">指定なし</button>\n'
    for item in sorted(opponent_debuff_values):
        safe_item = html.escape(item)
        opponent_debuff_btns += f'<button class="f-btn debuff-btn" data-debuff="{safe_item}">{safe_item}</button>\n'
    total      = len(champions)
    seo_title = f"MCOC チャンピオン一覧・能力検索（日本語）｜{total}体対応"
    seo_description = (
        f"Marvel Contest of Champions（MCOC）のチャンピオン{total}体を日本語で検索・絞り込みできる一覧。"
        "クラス、リリース年、完全耐性、条件付き耐性、相手に付与するデバフ、タグ、能力説明、シナジーを確認できます。"
    )
    seo_keywords = (
        "MCOC,Marvel Contest of Champions,マーベルコンテストオブチャンピオンズ,"
        "チャンピオン一覧,チャンピオン能力,日本語,耐性,デバフ,シナジー,攻略"
    )
    seo_json_ld = json.dumps(
        [
            {
                "@context": "https://schema.org",
                "@type": "WebApplication",
                "name": seo_title,
                "url": SITE_URL,
                "alternateName": [
                    "MCOC チャンピオン解説",
                    "MCOC Japanese Champion Database",
                ],
                "description": seo_description,
                "inLanguage": "ja",
                "applicationCategory": "GameApplication",
                "operatingSystem": "Any",
                "isAccessibleForFree": True,
                "about": {
                    "@type": "VideoGame",
                    "name": "Marvel Contest of Champions",
                },
                "offers": {
                    "@type": "Offer",
                    "price": "0",
                    "priceCurrency": "JPY",
                },
            },
            {
                "@context": "https://schema.org",
                "@type": "Dataset",
                "name": "MCOC チャンピオン日本語データ",
                "url": SITE_URL,
                "description": seo_description,
                "inLanguage": "ja",
                "about": {
                    "@type": "VideoGame",
                    "name": "Marvel Contest of Champions",
                },
                "keywords": seo_keywords,
            },
        ],
        ensure_ascii=False,
        separators=(",", ":"),
    )

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{html.escape(seo_title)}</title>
<link rel="canonical" href="{html.escape(SITE_URL, quote=True)}">
<meta name="description" content="{html.escape(seo_description, quote=True)}">
<meta name="keywords" content="{html.escape(seo_keywords, quote=True)}">
<meta name="robots" content="index,follow,max-image-preview:large">
<meta name="googlebot" content="index,follow,max-image-preview:large">
<meta name="google-adsense-account" content="{html.escape(ADSENSE_CLIENT, quote=True)}">
<meta name="application-name" content="MCOC チャンピオン解説">
<meta name="theme-color" content="#5044d4">
<meta name="format-detection" content="telephone=no">
<meta property="og:type" content="website">
<meta property="og:url" content="{html.escape(SITE_URL, quote=True)}">
<meta property="og:locale" content="ja_JP">
<meta property="og:site_name" content="MCOC チャンピオン解説">
<meta property="og:title" content="{html.escape(seo_title, quote=True)}">
<meta property="og:description" content="{html.escape(seo_description, quote=True)}">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{html.escape(seo_title, quote=True)}">
<meta name="twitter:description" content="{html.escape(seo_description, quote=True)}">
<script type="application/ld+json">{html.escape(seo_json_ld, quote=False)}</script>
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={html.escape(ADSENSE_CLIENT, quote=True)}" crossorigin="anonymous"></script>
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
.f-inner{{max-width:1400px;margin:0 auto;display:flex;gap:7px;flex-wrap:nowrap}}
.f-label{{font-size:12px;color:var(--text2);font-weight:700;align-self:center;white-space:nowrap;margin-right:3px}}
.f-btn{{padding:5px 13px;border-radius:20px;border:1px solid var(--border);background:transparent;color:var(--text2);cursor:pointer;font-size:13px;white-space:nowrap;transition:.15s}}
.f-btn:hover{{border-color:var(--cc,var(--accent));color:var(--text)}}
.f-btn.active{{background:var(--cc,var(--accent));border-color:transparent;color:#fff;font-weight:600}}
@media (min-width:900px){{
  .f-bar{{overflow-x:visible}}
  .f-inner{{flex-wrap:wrap;row-gap:7px}}
}}

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

/* タグ */
.tag-details{{font-size:13px}}
.tag-details summary{{color:var(--text2);cursor:pointer;padding:3px 0;user-select:none}}
.tag-details summary:hover{{color:var(--text)}}
.tags-row{{display:flex;flex-wrap:wrap;gap:5px;margin-top:7px}}
.tag-badge{{font-size:11px;background:rgba(80,68,212,.07);border:1px solid rgba(80,68,212,.22);color:#5044d4;padding:2px 8px;border-radius:4px;line-height:1.45}}

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
.card-body > .gd-sec:first-child{{border-top:0;padding-top:0}}
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
.glossary-term{{appearance:none;background:transparent;border:0;border-bottom:1px dotted var(--accent);color:var(--accent);font:inherit;line-height:inherit;padding:0 1px;cursor:pointer}}
.glossary-term:hover,.glossary-term:focus-visible{{color:var(--text);border-bottom-color:var(--accent);outline:none}}
.glossary-popover{{position:fixed;z-index:50;display:none;max-width:min(330px,calc(100vw - 24px));background:var(--bg2);border:1px solid var(--border);border-radius:8px;box-shadow:0 10px 28px rgba(0,0,0,.2);padding:10px 12px}}
.glossary-popover.show{{display:block}}
.glossary-pop-title{{font-size:13px;font-weight:700;color:var(--text);margin-bottom:5px}}
.glossary-pop-desc{{font-size:12px;color:var(--text2);line-height:1.55}}
.site-foot{{max-width:1400px;margin:10px auto 0;padding:18px 20px 28px;color:var(--text2);font-size:12px;line-height:1.7}}
.foot-links{{display:flex;flex-wrap:wrap;gap:12px;margin-bottom:8px}}
.foot-links a{{color:var(--accent);text-decoration:none}}
.foot-links a:hover{{text-decoration:underline}}
.foot-note{{max-width:900px}}

</style>
</head>
<body>

<header class="site-hd">
  <div class="hd-inner">
    <h1 class="site-title">MCOC チャンピオン解説</h1>
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
<div class="f-bar year-bar">
  <div class="f-inner">
    {year_btns}
  </div>
</div>
<div class="f-bar immunity-bar">
  <div class="f-inner">
    <span class="f-label">完全耐性</span>
    {full_immunity_btns}
  </div>
</div>
<div class="f-bar immunity-bar conditional-immunity-bar">
  <div class="f-inner">
    <span class="f-label">条件付き耐性</span>
    {conditional_immunity_btns}
  </div>
</div>
<div class="f-bar debuff-bar">
  <div class="f-inner">
    <span class="f-label">相手デバフ</span>
    {opponent_debuff_btns}
  </div>
</div>

<main class="main">
  <div class="grid" id="grid">
    {cards_html}
  </div>
  <div class="no-res" id="noRes">該当するチャンピオンが見つかりませんでした</div>
</main>

<footer class="site-foot">
  <nav class="foot-links" aria-label="サイト情報">
    <a href="/">トップ</a>
    <a href="/privacy.html">プライバシーポリシー</a>
    <a href="/disclaimer.html">免責事項</a>
    <a href="/sitemap.xml">サイトマップ</a>
  </nav>
  <p class="foot-note">このサイトは Marvel Contest of Champions の非公式ファンサイトです。Marvel、Kabam、各キャラクターおよび関連画像の権利は各権利者に帰属します。</p>
</footer>

<script>
let cls='all',yr='all',q='';
let selectedFullImmunities=[];
let selectedConditionalImmunities=[];
let selectedDebuffs=[];
const glossaryPopover=document.createElement('div');
glossaryPopover.className='glossary-popover';
glossaryPopover.innerHTML='<div class="glossary-pop-title"></div><div class="glossary-pop-desc"></div>';
document.body.appendChild(glossaryPopover);
function hideGlossary(){{
  glossaryPopover.classList.remove('show');
}}
function showGlossary(term){{
  const title=term.dataset.glossaryTitle||term.textContent;
  const desc=term.dataset.glossaryDesc||'';
  glossaryPopover.querySelector('.glossary-pop-title').textContent=title;
  glossaryPopover.querySelector('.glossary-pop-desc').textContent=desc;
  glossaryPopover.classList.add('show');
  const rect=term.getBoundingClientRect();
  const popRect=glossaryPopover.getBoundingClientRect();
  const margin=10;
  let left=rect.left;
  let top=rect.bottom+8;
  if(left+popRect.width+margin>window.innerWidth)left=window.innerWidth-popRect.width-margin;
  if(left<margin)left=margin;
  if(top+popRect.height+margin>window.innerHeight)top=rect.top-popRect.height-8;
  if(top<margin)top=margin;
  glossaryPopover.style.left=left+'px';
  glossaryPopover.style.top=top+'px';
}}
document.addEventListener('click',function(event){{
  const term=event.target.closest('.glossary-term');
  if(term){{
    event.preventDefault();
    event.stopPropagation();
    if(glossaryPopover.classList.contains('show')&&glossaryPopover.dataset.key===term.dataset.glossaryKey){{
      hideGlossary();
      glossaryPopover.dataset.key='';
    }}else{{
      glossaryPopover.dataset.key=term.dataset.glossaryKey||'';
      showGlossary(term);
    }}
    return;
  }}
  if(!event.target.closest('.glossary-popover'))hideGlossary();
}});
document.addEventListener('keydown',function(event){{
  if(event.key==='Escape')hideGlossary();
}});
window.addEventListener('scroll',hideGlossary,{{passive:true}});
window.addEventListener('resize',hideGlossary);
document.querySelectorAll('.class-btn').forEach(b=>{{
  b.addEventListener('click',function(){{
    document.querySelectorAll('.class-btn').forEach(x=>x.classList.remove('active'));
    this.classList.add('active');
    cls=this.dataset.class;
    run();
  }});
}});
document.querySelectorAll('.year-btn').forEach(b=>{{
  b.addEventListener('click',function(){{
    document.querySelectorAll('.year-btn').forEach(x=>x.classList.remove('active'));
    this.classList.add('active');
    yr=this.dataset.year;
    run();
  }});
}});
function bindMultiFilter(selector,items,datasetKey){{
  document.querySelectorAll(selector).forEach(b=>{{
    b.addEventListener('click',function(){{
    const value=this.dataset[datasetKey];
    if(value==='all'){{
      items.splice(0,items.length);
    }}else if(items.includes(value)){{
      items.splice(items.indexOf(value),1);
    }}else{{
      items.push(value);
    }}
    document.querySelectorAll(selector).forEach(x=>{{
      const item=x.dataset[datasetKey];
      x.classList.toggle('active',item==='all'?items.length===0:items.includes(item));
    }});
    run();
  }});
}});
}}
bindMultiFilter('.full-immunity-btn',selectedFullImmunities,'fullImmunity');
bindMultiFilter('.conditional-immunity-btn',selectedConditionalImmunities,'conditionalImmunity');
bindMultiFilter('.debuff-btn',selectedDebuffs,'debuff');
function run(){{
  q=document.getElementById('q').value.toLowerCase();
  let vis=0;
  document.querySelectorAll('.card').forEach(card=>{{
    const mc=cls==='all'||card.dataset.class===cls;
    const my=yr==='all'||(card.dataset.years||'').split(' ').includes(yr);
    const fullImmunities=(card.dataset.immunitiesFull||'').split('|').filter(Boolean);
    const conditionalImmunities=(card.dataset.immunitiesConditional||'').split('|').filter(Boolean);
    const debuffs=(card.dataset.debuffs||'').split('|').filter(Boolean);
    const mf=selectedFullImmunities.every(item=>fullImmunities.includes(item));
    const mi=selectedConditionalImmunities.every(item=>conditionalImmunities.includes(item));
    const md=selectedDebuffs.every(item=>debuffs.includes(item));
    const mq=!q||card.dataset.name.includes(q)||card.textContent.toLowerCase().includes(q);
    card.style.display=(mc&&my&&mf&&mi&&md&&mq)?'':'none';
    if(mc&&my&&mf&&mi&&md&&mq)vis++;
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
