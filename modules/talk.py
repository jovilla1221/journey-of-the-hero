"""Dewa ↔ Hero chat. Template replies + optional Gemini flavor."""

from __future__ import annotations

import json
import random
import urllib.error
import urllib.request
from typing import Optional

from modules.config import GOOGLE_API_KEY
from modules.db import get_player, upd
from modules.adventure import _diary


# ── template replies (natural, not stiff) ──
_TEMPLATES_ID = [
    "Eh? {deity} manggil? Aku lagi {doing}. {reply}",
    "Wah, dewa-ku ngomong. {reply} (sambil {doing})",
    "\"{msg}\" — oke, oke. {reply}",
    "Dengar, {deity}. {reply} Nanti aku lapor lagi.",
    "Heh. {reply} Maaf kalau jawabannya acak-acakan, lagi {doing}.",
    "Siap, Dewa {deity}. {reply}",
]

_TEMPLATES_EN = [
    "Huh? {deity} calling? I'm {doing}. {reply}",
    "Oh, my deity speaks. {reply} (while {doing})",
    "\"{msg}\" — alright. {reply}",
    "Heard you, {deity}. {reply} I'll report later.",
    "Heh. {reply} Sorry if it's messy — busy {doing}.",
    "Yes, Deity {deity}. {reply}",
]

_DOING_ID = [
    "jalan di {zone}",
    "istirahat sebentar",
    "cari loot",
    "ngumpet dari musuh",
    "ngeliat peta",
    "ngemil bekal",
    "bersihin pedang",
]

_DOING_EN = [
    "walking in {zone}",
    "resting a bit",
    "looking for loot",
    "hiding from foes",
    "checking the map",
    "eating rations",
    "cleaning my sword",
]

# keyword → short reply snippets
_SNIPPETS_ID = {
    "hati": ["Aku hati-hati kok… kira-kira.", "Hati-hati? Aku coba, deh."],
    "careful": ["I'll try to be careful… ish."],
    "semangat": ["Semangat! …meski kaki pegal.", "Oke, gas terus!"],
    "bagus": ["Makasih, Dewa. Jarang dipuji.", "Oh, pujian? Simpen di diary."],
    "good": ["Thanks. Rare compliment.", "I'll write that down."],
    "diam": ["…oke, diam dulu.", "Siap. Mulut dicomot."],
    "istirahat": ["Istirahat? Boleh juga. Sebentar ya.", "Rest mode… on."],
    "rest": ["Rest? Sure. Briefly.", "Rest mode… on."],
    "lawan": ["Lawan? Oke, siap… kira-kira.", "Aku lawan yang ada di depan."],
    "fight": ["Fight? Okay… ish.", "I'll fight what's ahead."],
    "mana": ["Di {zone}. Masih hidup.", "Somewhere in {zone}."],
    "where": ["In {zone}. Still alive.", "Somewhere around {zone}."],
    "sayang": ["…eh. Malu dikit.", "A-ah. Oke deh."],
    "love": ["…uh. Okay then.", "Noted. Blushing quietly."],
    "tolong": ["Tolong? Aku coba bantu… caraku sendiri.", "I'll try."],
    "help": ["Help? I'll try… my way.", "On it, sort of."],
}

_DEFAULT_REPLY_ID = [
    "Aku denger. Nanti aku bikin jadi kenyataan… semoga.",
    "Oke. Catet di otak (yang agak bocor).",
    "Sip. Lanjut jalan dulu ya.",
    "Diterima. Hero-mu agak bingung, tapi nurut.",
    "Baik. Aku usahain gak mati dulu.",
]

_DEFAULT_REPLY_EN = [
    "I hear you. I'll make it real… hopefully.",
    "Okay. Noted in my leaky brain.",
    "Got it. Walking on.",
    "Received. Your hero is confused but obedient.",
    "Alright. I'll try not to die first.",
]


def _zone_name(p: dict, lang: str) -> str:
    from modules.data import zname
    return zname(p.get("zone") or "plains", lang)


def _template_reply(uid: int, msg: str, lang: str) -> str:
    p = get_player(uid) or {}
    deity = p.get("deity_name") or ("Dewa" if lang == "id" else "Deity")
    zone = _zone_name(p, lang)
    low = msg.lower()

    snippet = None
    for key, opts in _SNIPPETS_ID.items():
        if key in low:
            # filter by lang roughly
            if lang == "en" and key in ("hati", "semangat", "bagus", "diam", "istirahat", "lawan", "mana", "sayang", "tolong"):
                continue
            if lang == "id" and key in ("careful", "good", "rest", "fight", "where", "love", "help"):
                continue
            snippet = random.choice(opts)
            break

    if not snippet:
        snippet = random.choice(_DEFAULT_REPLY_ID if lang == "id" else _DEFAULT_REPLY_EN)

    doing = random.choice(_DOING_ID if lang == "id" else _DOING_EN).format(zone=zone)
    tpl = random.choice(_TEMPLATES_ID if lang == "id" else _TEMPLATES_EN)
    reply = snippet.format(zone=zone, deity=deity)
    return tpl.format(
        deity=deity,
        doing=doing,
        reply=reply,
        msg=msg[:80],
        zone=zone,
    )


def _gemini_reply(uid: int, msg: str, lang: str) -> Optional[str]:
    """Optional short hero reply via Gemini text model. None on failure/quota."""
    if not GOOGLE_API_KEY:
        return None
    p = get_player(uid) or {}
    deity = p.get("deity_name") or "Dewa"
    hero = p.get("name") or "Hero"
    zone = _zone_name(p, lang)
    hp = p.get("hp", 0)
    mhp = p.get("max_hp", 100)
    level = p.get("level", 1)
    sys = (
        f"Kamu hero RPG bernama {hero}, dewa-mu {deity}. "
        f"Zona: {zone}, Lv{level}, HP {hp}/{mhp}. "
        f"Jawab singkat (1-2 kalimat), santai, lucu, bahasa {'Indonesia' if lang == 'id' else 'English'}. "
        f"Jangan formal. Jangan markdown panjang. Hanya dialog hero."
        if lang == "id" else
        f"You are RPG hero {hero}, deity {deity}. "
        f"Zone: {zone}, Lv{level}, HP {hp}/{mhp}. "
        f"Reply short (1-2 sentences), casual, funny, English only. "
        f"No formal tone. No long markdown. Hero dialogue only."
    )
    body = {
        "contents": [{
            "parts": [{"text": f"{sys}\n\nDewa bilang: {msg}\n\nHero:"}]
        }],
        "generationConfig": {
            "temperature": 0.9,
            "maxOutputTokens": 80,
        },
    }
    # prefer flash-lite for cheap/fast
    model = "gemini-2.0-flash-lite"
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={GOOGLE_API_KEY}"
    )
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        parts = (((data.get("candidates") or [{}])[0].get("content") or {}).get("parts")) or []
        text = "".join(p.get("text", "") for p in parts).strip()
        if text and len(text) < 400:
            return text.split("\n")[0][:280]
    except Exception:
        return None
    return None


def hero_reply(uid: int, deity_msg: str, lang: str = "id", use_ai: bool = True) -> str:
    """Generate hero reply; prefer AI if available, else template."""
    msg = (deity_msg or "").strip()[:200]
    if not msg:
        return "…?" if lang != "id" else "…ya?"

    if use_ai:
        ai = _gemini_reply(uid, msg, lang)
        if ai:
            return ai
    return _template_reply(uid, msg, lang)


def process_talk(uid: int, deity_msg: str, lang: str = "id") -> str:
    """
    Dewa speaks → log both sides in diary → return message to show deity.
    """
    p = get_player(uid) or {}
    deity = p.get("deity_name") or ("Dewa" if lang == "id" else "Deity")
    hero = p.get("name") or "Hero"
    msg = (deity_msg or "").strip()[:200]
    if not msg:
        return "Ketik pesan dulu." if lang == "id" else "Type a message first."

    # diary: deity line
    _diary(uid, f"⚡ {deity}: {msg}")

    reply = hero_reply(uid, msg, lang, use_ai=True)
    _diary(uid, f"🦸 {hero}: {reply}")

    if lang == "id":
        return (
            f"💬 *Ngobrol dengan {hero}*\n"
            f"━━━━━━━━━━━━━━\n"
            f"⚡ *{deity}:* {msg}\n\n"
            f"🦸 *{hero}:*\n_{reply}_"
        )
    return (
        f"💬 *Chat with {hero}*\n"
        f"━━━━━━━━━━━━━━\n"
        f"⚡ *{deity}:* {msg}\n\n"
        f"🦸 *{hero}:*\n_{reply}_"
    )
