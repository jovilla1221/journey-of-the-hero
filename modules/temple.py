"""Temple (Godville-style) — hero builds with materials, not just gold."""

import random
from typing import Optional, Dict, List
from modules.config import GAME_NAME
from modules.db import get_player, upd, get_player as g, get_conn, get_inv, add_item, use_item
from modules.data import tr, iname, ITEMS
from modules.adventure import _diary


# ─── TEMPLE DATA ───────────────────────────────────────────────
TEMPLE_TYPES = [
    {"id":"shrine","name":{"id":"Kuil Kecil","en":"Small Shrine"},
     "desc":{"id":"Tempat ibadah sederhana.","en":"Simple place of worship."},
     "materials":{"stone":10,"wood":5,"sacred_cloth":2},
     "bonus":{"hp":5,"atk":1,"def":0,"exp_bonus":0.01,"gold_bonus":0.02},
     "rarity":"common","emoji":"🏠"},
    {"id":"altar","name":{"id":"Altar","en":"Altar"},
     "desc":{"id":"Tempat persembahan.","en":"Offering place."},
     "materials":{"stone":20,"wood":10,"holy_water":5,"sacred_cloth":3},
     "bonus":{"hp":10,"atk":2,"def":1,"exp_bonus":0.02,"gold_bonus":0.03},
     "rarity":"common","emoji":"⛪"},
    {"id":"temple","name":{"id":"Candi","en":"Temple"},
     "desc":{"id":"Tempat ibadah besar.","en":"Great temple."},
     "materials":{"stone":30,"wood":20,"crystal":5,"holy_water":10,"sacred_cloth":5},
     "bonus":{"hp":20,"atk":3,"def":2,"exp_bonus":0.03,"gold_bonus":0.05},
     "rarity":"uncommon","emoji":"🏛️"},
    {"id":"cathedral","name":{"id":"Katedral","en":"Cathedral"},
     "desc":{"id":"Tempat ibadah megah.","en":"Magnificent sanctuary."},
     "materials":{"stone":50,"wood":30,"crystal":10,"holy_water":20,"gold_leaf":5,"sacred_cloth":10},
     "bonus":{"hp":40,"atk":5,"def":4,"exp_bonus":0.05,"gold_bonus":0.08},
     "rarity":"uncommon","emoji":"⛪"},
    {"id":"sanctuary","name":{"id":"Santuario","en":"Sanctuary"},
     "desc":{"id":"Tempat suci penuh keajaiban.","en":"Sacred place."},
     "materials":{"ancient_brick":10,"crystal":20,"gold_leaf":10,"holy_water":30,"sacred_cloth":20},
     "bonus":{"hp":60,"atk":8,"def":6,"exp_bonus":0.08,"gold_bonus":0.12},
     "rarity":"rare","emoji":"🕍"},
    {"id":"citadel","name":{"id":"Benteng Suci","en":"Holy Citadel"},
     "desc":{"id":"Benteng suci tak tergoyahkan.","en":"Unyielding holy fortress."},
     "materials":{"ancient_brick":20,"crystal":30,"gold_leaf":20,"holy_water":40,"sacred_cloth":30},
     "bonus":{"hp":100,"atk":12,"def":10,"exp_bonus":0.12,"gold_bonus":0.20},
     "rarity":"epic","emoji":"🏰"},
    {"id":"sanctum","name":{"id":"Sanctum","en":"Sanctum"},
     "desc":{"id":"Tempat paling suci.","en":"Holiest place."},
     "materials":{"ancient_brick":30,"crystal":50,"gold_leaf":30,"holy_water":50,"sacred_cloth":50},
     "bonus":{"hp":200,"atk":20,"def":15,"exp_bonus":0.20,"gold_bonus":0.30},
     "rarity":"legendary","emoji":"🌟"},
]

TEMPLE_ORDER = [t["id"] for t in TEMPLE_TYPES]

TEMPLE_NAMES_ID = [
    "{deity} Agung", "Rumah {deity}", "Kuil {deity}",
    "Menara {deity}", "Mahkota {deity}", "Singgasana {deity}",
    "Pelataran {deity}", "Candi {deity} Abadi", "Kubah {deity}",
    "Pilar {deity}", "Benteng {deity}", "Istana {deity}",
]

TEMPLE_NAMES_EN = [
    "Shrine of {deity}", "Temple of {deity}", "Sanctuary of {deity}",
    "Altar of {deity}", "Hall of {deity}", "Throne of {deity}",
    "Cathedral of {deity}", "Monument of {deity}", "Cenotaph of {deity}",
    "Keep of {deity}", "Vault of {deity}", "Chapel of {deity}",
]

MATERIAL_DROP_RATES = {
    "stone":         {"chance": 0.08},
    "wood":          {"chance": 0.06},
    "crystal":       {"chance": 0.03},
    "sacred_cloth":  {"chance": 0.02},
    "holy_water":    {"chance": 0.02},
    "gold_leaf":     {"chance": 0.01},
    "ancient_brick": {"chance": 0.005},
}


def _random_name(deity: str, lang: str) -> str:
    if lang == "id":
        return random.choice(TEMPLE_NAMES_ID).format(deity=deity)
    return random.choice(TEMPLE_NAMES_EN).format(deity=deity)


def _progress_bar(level: int) -> str:
    total = 10
    n = max(1, min((min(level, 50) * 10) // 50, 10))
    return "▰" * n + "▱" * (total - n)


def _get_type(type_id: str) -> dict:
    return next((t for t in TEMPLE_TYPES if t["id"] == type_id), TEMPLE_TYPES[0])


# ─── MATERIAL HELPERS ──────────────────────────────────────────
def get_material_count(uid: int, mat: str) -> int:
    inv = get_inv(uid)
    return next((i["quantity"] for i in inv if i["item_key"] == mat), 0)


def get_all_materials(uid: int) -> Dict[str, int]:
    inv = get_inv(uid)
    mats = {}
    for i in inv:
        if ITEMS.get(i["item_key"], {}).get("type") == "material":
            mats[i["item_key"]] = i["quantity"]
    return mats


def consume_materials(uid: int, mats: Dict[str, int]) -> bool:
    """Subtract materials. Returns True if all consumed successfully."""
    for mat, qty in mats.items():
        have = get_material_count(uid, mat)
        if have < qty:
            return False
        add_item(uid, mat, -qty)
    return True


def can_build_next_type(uid: int) -> tuple:
    """Return (can_build, next_type_dict, missing_dict)."""
    p = get_player(uid)
    if not p:
        return False, None, {}
    current_idx = TEMPLE_ORDER.index(p.get("temple_type") or "shrine")
    if current_idx >= len(TEMPLE_TYPES) - 1:
        return False, None, {}
    next_type = TEMPLE_TYPES[current_idx + 1]
    inv = get_all_materials(uid)
    missing = {}
    for mat, need in next_type["materials"].items():
        have = inv.get(mat, 0)
        if have < need:
            missing[mat] = need - have
    return len(missing) == 0, next_type, missing


def can_level_up_current(uid: int) -> tuple:
    """Same type, next level. Returns (can, missing)."""
    p = get_player(uid)
    if not p:
        return False, {}
    current_type = _get_type(p.get("temple_type") or "shrine")
    if current_type["id"] == "sanctum":
        return False, {}
    level = p.get("temple_level") or 0
    mul = level + 1
    inv = get_all_materials(uid)
    missing = {}
    for mat, need in current_type["materials"].items():
        have = inv.get(mat, 0)
        need_scaled = need * mul
        if have < need_scaled:
            missing[mat] = need_scaled - have
    return len(missing) == 0, missing


# ─── TEMPLE ACTIONS (return strings for UI) ─────────────────────
def temple_info(uid: int, lang: str) -> dict:
    p = get_player(uid)
    if not p:
        return None
    return {
        "built": bool(p.get("temple_built")),
        "type": p.get("temple_type") or "shrine",
        "name": p.get("temple_name") or "",
        "level": p.get("temple_level") or 0,
        "deity": p.get("deity_name") or (("Dewa") if lang == "id" else "Deity"),
        "hero": p.get("name") or "Hero",
    }


def build_text(uid: int, lang: str) -> str:
    """Plain text for current temple state."""
    p = get_player(uid)
    if not p:
        return "?"

    lang = p.get("lang") or lang
    info = temple_info(uid, lang)

    if not info["built"]:
        t = _get_type("shrine")
        lines = [
            "🏛️ *Bangunan Candi*",
            "━━━━━━━━━━━━━",
            "Hero belum membangun candi untuk dewa.",
            f"Candi pertama: *{t['name'].get(lang, t['name']['id'])}* {t['emoji']}",
            "",
            "📋 *Bahan Bangunan Diperlukan:*",
        ]
        for mat, qty in t["materials"].items():
            have = get_material_count(uid, mat)
            lines.append(f"  {iname(mat, lang)} — *{have}/{qty}* {'✅' if have >= qty else '❌'}")
        lines.append("")
        lines.append("_Kumpulkan bahan dari petualangan, bukan beli!_")
        lines.append("_Tiap hero doodle di jalan, dapet material_")
        return "\n".join(lines)

    t = _get_type(info["type"])
    bar = _progress_bar(info["level"])

    next_type_idx = TEMPLE_ORDER.index(info["type"]) + 1
    is_max = next_type_idx >= len(TEMPLE_TYPES)

    lines = [
        f"{t['emoji']} *{info['name']}*",
        "━━━━━━━━━━━━━",
        f"Jenis: {t['name'].get(lang, t['name']['id'])}",
        f"Tingkat: *{info['level']}*",
        f"{bar} {info['level']}/50",
        "",
        f"📜 {t['desc'].get(lang, t['desc']['id'])}",
        f"⚔️ HP+{t['bonus']['hp']} ATK+{t['bonus']['atk']} DEF+{t['bonus']['def']}",
        f"📈 EXP+{int(t['bonus']['exp_bonus']*100)}% Gold+{int(t['bonus']['gold_bonus']*100)}%",
        "",
        "📐 _Keunikan: Setiap candi punya tipe berbeda,_",
        "_bonus unik, dan material yang beda._",
    ]

    if not is_max:
        nt = TEMPLE_TYPES[next_type_idx]
        lines.append("")
        lines.append(f"📋 *Berikutnya: {nt['name'].get(lang, nt['name']['id'])} {nt['emoji']}*")
        for mat, qty in nt["materials"].items():
            have = get_material_count(uid, mat)
            lines.append(f"  {iname(mat, lang)} — *{have}/{qty}* {'✅' if have >= qty else '❌'}")
        lines.append("")
        lines.append(f"_Level up tipe sekarang butuh {info['level']+1}x material._")
    else:
        lines.append("")
        lines.append("🌟 *Sudah MAX! Tipe tertinggi.*")
    return "\n".join(lines)


def do_build(uid: int) -> str:
    """Build first temple — must have all shrine materials."""
    p = get_player(uid)
    if not p:
        return "?"
    lang = p.get("lang") or "id"
    # already has a temple (either temple_built or temple_name/temple_type)
    if p.get("temple_built") or p.get("temple_name") or p.get("temple_type"):
        # upgrade level instead
        return do_donate(uid)
    # build shrine
    shrine = TEMPLE_TYPES[0]
    if not consume_materials(uid, shrine["materials"]):
        # not enough
        lines = ["❌ Bahan belum lengkap:"]
        for mat, qty in shrine["materials"].items():
            have = get_material_count(uid, mat)
            if have < qty:
                lines.append(f"  {iname(mat, lang)}: butuh {qty}, punya {have}")
        return "\n".join(lines)

    deity = p.get("deity_name") or (("Dewa") if lang == "id" else "Deity")
    name = _random_name(deity, lang)
    upd(uid, temple_built=1, temple_type="shrine", temple_name=name, temple_level=1, temple_gold=0)
    _diary(uid, f"🏠 Hero membangun *{shrine['name'][lang]} {name}*! Material habis dipakai.")

    # → Personality: temple event (devotion + wisdom)
    try:
        from modules.personality import apply_event
        pe = apply_event(get_player(uid), "temple")
        if pe:
            udb = get_conn()
            for k, v in pe.items():
                udb.execute(f"UPDATE players SET {k}=? WHERE user_id=?", (v, uid))
            udb.commit()
            udb.close()
    except Exception:
        pass

    return build_text(uid, lang)


def do_upgrade(uid: int) -> str:
    """Upgrade current temple to next type. Requires materials of next type."""
    p = get_player(uid)
    if not p or not p.get("temple_built"):
        return do_build(uid)
    lang = p.get("lang") or "id"
    can, next_type, missing = can_build_next_type(uid)
    if not can:
        lines = ["❌ Belum siap upgrade. Perlu tambahan:"]
        for mat, qty in missing.items():
            lines.append(f"  {iname(mat, lang)}: butuh {qty} lagi")
        return "\n".join(lines)
    consume_materials(uid, next_type["materials"])
    deity = p.get("deity_name") or (("Dewa") if lang == "id" else "Deity")
    new_name = _random_name(deity, lang)
    upd(uid, temple_type=next_type["id"], temple_name=new_name, temple_level=1)
    _diary(uid, f"⬆️ Hero merenovasi menjadi *{next_type['name'][lang]} {new_name}*! Material terpasang.")
    return build_text(uid, lang)


def do_donate(uid: int) -> str:
    """Donate materials to level up current temple (same type, more level)."""
    p = get_player(uid)
    if not p or not p.get("temple_built"):
        return do_build(uid)
    lang = p.get("lang") or "id"
    can, missing = can_level_up_current(uid)
    if not can:
        lines = ["❌ Bahan belum lengkap untuk level up:"]
        for mat, qty in missing.items():
            lines.append(f"  {iname(mat, lang)}: butuh {qty} lagi")
        return "\n".join(lines)
    current_type = _get_type(p.get("temple_type") or "shrine")
    level = p.get("temple_level") or 0
    mul = level + 1
    cost = {mat: qty * mul for mat, qty in current_type["materials"].items()}
    consume_materials(uid, cost)
    new_level = level + 1
    upd(uid, temple_level=new_level)
    _diary(uid, f"⬆️ *{p.get('temple_name')}* level {new_level}! Material terpasang.")
    return build_text(uid, lang)


# Backwards compat names
def temple_text(uid: int, lang: str) -> str:
    return build_text(uid, lang)


def temple_build(uid: int, lang: str) -> str:
    return do_build(uid)


def temple_donate(uid: int, lang: str) -> str:
    return do_donate(uid)


# ─── MATERIAL DROPS ─────────────────────────────────────────────
def maybe_drop_material(uid: int, zone: str) -> Optional[str]:
    """On adventure, may drop material based on probability."""
    p = get_player(uid)
    if not p:
        return None
    candidates = []
    for mat, info in MATERIAL_DROP_RATES.items():
        if random.random() < info["chance"]:
            candidates.append(mat)
    if not candidates:
        return None
    mat = random.choice(candidates)
    add_item(uid, mat, 1)
    lang = p.get("lang") or "id"
    _diary(uid, f"🔨 Hero temukan *{iname(mat, lang)}* di {zone}!")
    return mat


# ─── UI BUILDERS ──────────────────────────────────────────────
def temple_menu(uid: int, lang: str):
    """Return (text, InlineKeyboardMarkup)."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    p = get_player(uid)
    if not p:
        return "?", InlineKeyboardMarkup([])
    lang = p.get("lang") or "id"

    text = build_text(uid, lang)
    rows = []

    if not p.get("temple_built"):
        # Build shrine
        shrine = TEMPLE_TYPES[0]
        ready = all(get_material_count(uid, m) >= q for m, q in shrine["materials"].items())
        if ready:
            rows.append([InlineKeyboardButton("🛠 Bangun Candi" if lang == "id" else "🛠 Build",
                                              callback_data="temple_build")])
        else:
            rows.append([InlineKeyboardButton("🛠 Belum Siap" if lang == "id" else "⛔ Not Ready",
                                              callback_data="temple_none")])
    else:
        # donate: same type level up
        can_lvl, missing = can_level_up_current(uid)
        if can_lvl:
            rows.append([InlineKeyboardButton("🎁 Sumbang Material" if lang == "id" else "🎁 Donate",
                                              callback_data="temple_donate")])
        # upgrade: next type
        can_up, _, _ = can_build_next_type(uid)
        if can_up:
            rows.append([InlineKeyboardButton("⬆️ Upgrade Tipe" if lang == "id" else "⬆️ Upgrade Type",
                                              callback_data="temple_upgrade")])
    rows.append([InlineKeyboardButton("🔙 Tutup" if lang == "id" else "🔙 Close",
                                      callback_data="temple_close")])
    return text, InlineKeyboardMarkup(rows)


def temple_progress_text(uid: int) -> str:
    """Short progress for hero card."""
    p = get_player(uid)
    if not p or not p.get("temple_built"):
        return ""
    t = _get_type(p.get("temple_type") or "shrine")
    bar = _progress_bar(p.get("temple_level") or 0)
    return f"\n{t['emoji']} *{p.get('temple_name')}* Lv.{p.get('temple_level') or 0} {bar}"
