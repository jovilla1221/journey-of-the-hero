"""Temple (Godville-style) — hero builds for deity."""

import random
from modules.config import GAME_NAME
from modules.db import get_player, upd, get_conn
from modules.data import tr, iname
from modules.adventure import _diary


# Random temple names (auto-generated, hero picks one)
_TEMPLE_NAMES_ID = [
    "{deity} Agung", "Rumah {deity}", "Kuil {deity}",
    "Menara {deity}", "Mahkota {deity}", "Singgasana {deity}",
    "Pelataran {deity}", "Candi {deity} Abadi", "Kubah {deity}",
    "Pilar {deity}", "Benteng {deity}", "Istana {deity}",
]

_TEMPLE_NAMES_EN = [
    "Shrine of {deity}", "Temple of {deity}", "Sanctuary of {deity}",
    "Altar of {deity}", "Hall of {deity}", "Throne of {deity}",
    "Cathedral of {deity}", "Monument of {deity}", "Cenotaph of {deity}",
    "Keep of {deity}", "Vault of {deity}", "Chapel of {deity}",
]


def _random_name(deity: str, lang: str) -> str:
    if lang == "id":
        return random.choice(_TEMPLE_NAMES_ID).format(deity=deity)
    return random.choice(_TEMPLE_NAMES_EN).format(deity=deity)


def _progress_bar(level: int) -> str:
    """Visual progress: ▰▰▰▰▱▱▱"""
    max_lv = 50
    filled = min(level, max_lv)
    total = 10
    n = (filled * total) // max_lv if max_lv else 1
    n = max(1, min(n, total))
    return "▰" * n + "▱" * (total - n)


def temple_info(uid: int, lang: str) -> dict:
    """Return dict with info or None if not built."""
    p = get_player(uid)
    if not p:
        return None
    data = {
        "built": bool(p.get("temple_built")),
        "name": p.get("temple_built") or "",
        "level": p.get("temple_level") or 0,
        "gold": p.get("temple_gold") or 0,
        "deity": p.get("deity_name") or ("Dewa" if lang == "id" else "Deity"),
        "hero": p.get("name") or "Hero",
        "lang": lang,
    }
    return data


def temple_text(uid: int, lang: str) -> str:
    info = temple_info(uid, lang)
    if not info:
        return tr(lang, "temple_none", hero="?", deity="?")
    if not info["built"]:
        return tr(lang, "temple_none", hero=info["hero"], deity=info["deity"])

    max_lv = 50
    cost = 500 * (info["level"] + 1)
    progress = _progress_bar(info["level"])
    desc = tr(lang, "temple_progress", progress=progress, max_lv=max_lv)
    if lang == "id":
        text = (
            f"🏛️ *{info['name']}*\n"
            f"━━━━━━━━━━━━━━\n"
            f"Tingkat: {info['level']}\n"
            f"{progress}  {info['level']}/{max_lv}\n"
            f"\n"
            f"Selanjutnya: +500 gold untuk naik.\n"
            f"Sumbang: 💰500 ⚡+bonus EXP +stats.\n\n"
            f"Bonus: HP+{info['level']*10} ATK/DEF+{info['level']}"
        )
    else:
        text = (
            f"🏛️ *{info['name']}*\n"
            f"━━━━━━━━━━━━━━\n"
            f"Level: {info['level']}\n"
            f"{progress}  {info['level']}/{max_lv}\n"
            f"\n"
            f"Next: +500 gold to level up.\n"
            f"Donate: 💰500 → EXP boost +stats.\n\n"
            f"Bonus: HP+{info['level']*10} ATK/DEF+{info['level']}"
        )
    return text


def temple_build(uid: int, lang: str) -> str:
    """Start building first temple. Returns status message."""
    p = get_player(uid)
    if not p:
        return "?"
    deity = p.get("deity_name") or ("Dewa" if lang == "id" else "Deity")
    hero = p.get("name") or "Hero"
    cost = 1000
    if (p.get("gold") or 0) < cost:
        if lang == "id":
            return f"Gold kurang. Butuh 💰{cost:,} buat mulai."
        return f"Need 💰{cost:,} gold to start."
    name = _random_name(deity, lang)
    upd(uid, gold=p["gold"] - cost, temple_built=name, temple_level=1, temple_gold=cost)
    _diary(uid, f"🏛️ Bangun {name}")
    return temple_text(uid, lang)


def temple_donate(uid: int, lang: str) -> str:
    """Auto-donate gold to temple (~20% of gold, min 500, max 2000)."""
    p = get_player(uid)
    if not p or not p.get("temple_built"):
        return temple_build(uid, lang) if lang == "id" else temple_build(uid, lang)
    deity = p.get("deity_name") or ("Dewa" if lang == "id" else "Deity")
    gold = p.get("gold") or 0
    level = p.get("temple_level") or 0
    max_lv = 50
    if gold < 500:
        return "Gold kurang" if lang == "id" else "Not enough gold"
    # donate 15% gold, capped at 2000
    donate = max(500, min(int(gold * 0.15), 2000))
    if donate > gold:
        donate = gold
    new_gold = gold - donate
    new_tg = (p.get("temple_gold") or 0) + donate
    # 500 per level
    new_lv = min(max_lv, new_tg // 500)
    leveled = new_lv > level
    name = p["temple_built"]
    upd(uid, gold=new_gold, temple_gold=new_tg, temple_level=new_lv)
    _diary(uid, f"🏛️ Sumbang 💰{donate} ke {name}")
    if lang == "id":
        msg = f"🙏 Sumbang 💰{donate} ke *{name}*"
        if leveled:
            msg += f"\n🎉 *{name}* naik ke tingkat {new_lv}!"
    else:
        msg = f"🙏 Donated 💰{donate} to *{name}*"
        if leveled:
            msg += f"\n🎉 *{name}* reached level {new_lv}!"
    return msg