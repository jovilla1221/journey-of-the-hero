"""
Pixel art generator — sprite PNG + animated GIF (2-frame idle).
Cache per user so re-discover doesn't re-generate.
"""

import os
import io
import hashlib
import random
from typing import Optional

from modules.config import GAME_NAME

CACHE_DIR = os.path.join(os.path.dirname(__file__), ".pixel_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

# ── SPRITE DATA ──────────────────────────────────────────────
# Each sprite = list of 8 strings (8x8 chars), char -> (R,G,B) or None for transparent
PIXEL = {"X": (30, 30, 30), "W": (255, 255, 255), "R": (220, 50, 50), "B": (50, 80, 220),
         "G": (50, 180, 50), "Y": (220, 200, 50), "O": (200, 120, 40), "P": (180, 80, 180),
         "K": (80, 60, 40), "L": (150, 100, 60), "S": (200, 200, 200), "N": (40, 40, 40),
         "H": (50, 150, 200), "M": (180, 160, 140), "Z": (100, 60, 200), "U": (100, 180, 100)}

SPRITES = {
    # ─── MONSTERS ───────────────────────────────────────────
    "slime": {
        "frames": [
            ["........",
             "..YYYY..",
             ".YYYYYY.",
             ".Y.BB.Y.",
             ".YYYYYY.",
             ".YBBYBY.",
             "..YY.Y..",
             "........"],
            ["........",
             "..YYYY..",
             ".YYYYYY.",
             ".Y.BB.Y.",
             ".YYYYYY.",
             "..YY.Y..",
             "..YY.Y..",
             "........"],
        ],
        "scale": 4, "bg": (20, 22, 28),
        "desc_id": "B青龙 kecil yang gelatin. Loncat-loncat tapi gak bahaya. Starter enemy.",
        "desc_en": "Small gelatinous blob. Bouncy but harmless. Starter enemy.",
        "boss": False,
    },
    "goblin": {
        "frames": [
            ["..KKKK..",
             ".NNYYYY.",
             ".YOOOOY.",
             ".YY..YY.",
             "..YYYY..",
             ".RR..RR.",
             ".RR..RR.",
             "..KK..KK"],
            ["..KKKK..",
             ".NNYYYY.",
             ".YOOOOY.",
             ".YY..YY.",
             "..YYYY..",
             ".RR..RR.",
             ".RR..RR.",
             "..KK..KK"],
        ],
        "scale": 4, "bg": (20, 22, 28),
        "desc_id": "Makhluk hijau cerdik. Curang, lempar batu, kabur kalau kalah.",
        "desc_en": "Green trickster. Throws rocks, runs if losing.",
        "boss": False,
    },
    "orc": {
        "frames": [
            ["..NNNN..",
             ".NNNNNN.",
             ".YYYYYY.",
             ".YOOOOY.",
             ".YYYYYY.",
             ".NNYYNN.",
             "..RRRR..",
             ".NNNNNN."],
            ["..NNNN..",
             ".NNNNNN.",
             ".YYYYYY.",
             ".YOOOOY.",
             ".YYYYYY.",
             "..RRRR..",
             "..NNNN..",
             ".NNNNNN."],
        ],
        "scale": 4, "bg": (20, 22, 28),
        "desc_id": "Gajah besar dan galak. HP tebal, lempar gada. Level 3+.",
        "desc_en": "Big angry boar. Thick HP, swings a club. Level 3+.",
        "boss": False,
    },
    "troll": {
        "frames": [
            ["...KK...",
             ".NNNNNN.",
             ".NYYYYN.",
             ".YOOOOY.",
             ".NNNNNN.",
             ".NLLLLN.",
             ".NRRRNR.",
             ".NNNNNN."],
            ["...KK...",
             ".NNNNNN.",
             ".NYYYYN.",
             ".YOOOOY.",
             ".NNNNNN.",
             ".NLLLLN.",
             ".NRRRNR.",
             ".NNNNNN."],
        ],
        "scale": 4, "bg": (20, 22, 28),
        "desc_id": "Monster hutan besar. Regenerasi HP di battle. Level 5+.",
        "desc_en": "Huge forest monster. Regenerates HP in battle. Level 5+.",
        "boss": False,
    },
    "slime_king": {
        "frames": [
            ["..YYYY..",
             ".YYYYYY.",
             ".YYY.YY.",
             ".YYYYYY.",
             ".Y.BBBY.",
             ".YYYYYY.",
             "..YYYY..",
             "...YY..."],
            ["...YY...",
             "..YYYY..",
             ".YYYYYY.",
             ".Y.BBBY.",
             ".YYYYYY.",
             "..YYYY..",
             "...YY...",
             "........"],
        ],
        "scale": 5, "bg": (40, 10, 80),
        "desc_id": "👑 Raja Slime! Crystall core, lempar slime. Diamond dari dia.",
        "desc_en": "👑 Slime King! Crystalline core, throws slime balls. Drops diamonds.",
        "boss": True, "emoji": "👑",
    },
    "dragon": {
        "frames": [
            ["...RRR...",
             "..RYYR...",
             ".RYYYRR.",
             ".YZYYZZ.",
             ".RZZRZZ.",
             ".RRRZZ..",
             "..RRR...",
             "..NNN..."],
            ["....RRR..",
             "...RYYR..",
             "..RYYYRR.",
             "..YZZYZZ.",
             "..RZZRZZ.",
             "...RRRZZ.",
             "....RRR..",
             "....NNN.."],
        ],
        "scale": 5, "bg": (80, 20, 10),
        "desc_id": "🐉 Naga legendaris. Napas api, sisik keras. Diamond chance tinggi.",
        "desc_en": "🐉 Legendary dragon. Fire breath, hard scales. High diamond chance.",
        "boss": True, "emoji": "🐉",
    },
    "skeleton": {
        "frames": [
            ["..SSSS..",
             ".SSSSSS.",
             "..YSSY..",
             ".SSYYSS.",
             "..SSSS..",
             ".SSSSSS.",
             ".RR..RR.",
             ".SS..SS."],
            ["..SSSS..",
             ".SSSSSS.",
             "..YSSY..",
             ".SSYYSS.",
             "..SSSS..",
             ".SSSSSS.",
             ".RR..RR.",
             ".SS..SS."],
        ],
        "scale": 4, "bg": (20, 22, 28),
        "desc_id": "💀 Skeleton — tulang hidup. Rapi dan mematikan.",
        "desc_en": "💀 Skeleton — animated bones. Neatly lethal.",
        "boss": False,
    },
    "wraith": {
        "frames": [
            ["..NNNN..",
             ".NNNNNN.",
             "..YYNN..",
             ".NNYYNN.",
             "..NNNN..",
             ".NNNNNN.",
             "..RRRR..",
             "..PPPP.."],
            ["...NNN..",
             ".NNNNNN.",
             "..YYNN..",
             ".NNYYNN.",
             "..NNNN..",
             ".NNNNNN.",
             "..RRRR..",
             "...PP..."],
        ],
        "scale": 4, "bg": (15, 10, 30),
        "desc_id": "👻 Wraith — hantu gelap. Attaknya bypass DEF.",
        "desc_en": "👻 Wraith — shadow spirit. Attack ignores DEF.",
        "boss": False,
    },
    "spider": {
        "frames": [
            ["K......K",
             ".KKKKKK.",
             "..SSSS..",
             ".SSYYSS.",
             ".SSYYSS.",
             "..SSSS..",
             ".KKKKKK.",
             "K......K"],
            [".K....K.",
             "KKKKKKKK",
             "..SSSS..",
             ".SSYYSS.",
             ".SSYYSS.",
             "..SSSS..",
             "KKKKKKKK",
             ".K....K."],
        ],
        "scale": 4, "bg": (20, 22, 28),
        "desc_id": "🕷️ Spider — banyak kaki, bisa poison. HP kecil tapi nyerang 2x.",
        "desc_en": "🕷️ Spider — eight legs, can poison. Low HP but double attack.",
        "boss": False,
    },
    "demon": {
        "frames": [
            ["R......R",
             ".RRRRRR.",
             ".NNNNNN.",
             ".NRRRN.",
             ".NNYYNN.",
             ".NNNNNN.",
             ".LLLLLL.",
             ".NNNNNN."],
            ["...RR...",
             "RRRRRRRR",
             ".NNNNNN.",
             ".NRRRN.",
             ".NNYYNN.",
             ".NNNNNN.",
             ".LLLLLL.",
             ".NNNNNN."],
        ],
        "scale": 4, "bg": (30, 5, 5),
        "desc_id": "👹 Demon — dari neraka. DMG tinggi, bisa crit 2x.",
        "desc_en": "👹 Demon — from the underworld. High damage, can crit 2x.",
        "boss": True, "emoji": "👹",
    },
    # ─── PETS ────────────────────────────────────────────────
    "wolf_pet": {
        "frames": [
            ["..KKKK..",
             ".KKLLKK.",
             ".KYYYYK.",
             ".KYYKY.",
             ".KLLLLK.",
             ".KK..KK.",
             "..KK.KK..",
             "........"],
            ["..KKKK..",
             ".KKLLKK.",
             ".KYYYYK.",
             ".KYYKY.",
             ".KLLLLK.",
             "..KK.KK.",
             ".KK..KK.",
             "........"],
        ],
        "scale": 4, "bg": (20, 30, 20),
        "desc_id": "🐺 Wolf — companion. +20% gold.",
        "desc_en": "🐺 Wolf — companion. +20% gold.",
    },
    "phoenix_pet": {
        "frames": [
            ["..RRRR..",
             ".RYYYYR.",
             ".RYYYYR.",
             "..RYYR..",
             ".RRRYYR.",
             ".RRRRR..",
             ".YYYR...",
             "..YY...."],
            [".RYYYYR.",
             ".RYYYYR.",
             "..RYYR..",
             ".RRRYYR.",
             ".RRRRR..",
             "..RRR...",
             ".YYYR...",
             "....YY.."],
        ],
        "scale": 4, "bg": (200, 80, 10),
        "desc_id": "🔥 Phoenix — rebirth. +15% EXP.",
        "desc_en": "🔥 Phoenix — rebirth. +15% EXP.",
    },
    "dragon_pet": {
        "frames": [
            ["...RR...",
             "..RZZR..",
             ".RZZZZR.",
             ".RZYYZR.",
             ".RZZZZR.",
             "..RRRR..",
             ".YYYR...",
             "..YYY..."],
            ["..RZZR..",
             ".RZZZZR.",
             ".RZYYZR.",
             ".RZZZZR.",
             "..RRRR..",
             ".YYYR...",
             "..YYY...",
             "........"],
        ],
        "scale": 4, "bg": (60, 30, 140),
        "desc_id": "🐉 Dragon Pet — companion langka. +30% gold +10% EXP.",
        "desc_en": "🐉 Dragon Pet — rare companion. +30% gold +10% EXP.",
    },
    "cat_pet": {
        "frames": [
            ["..KKKK..",
             ".KKKKKK.",
             ".KSSSSK.",
             ".KYYYSK.",
             ".KSSSSK.",
             ".KKKKKK.",
             ".KK..KK.",
             "........"],
            ["..KKKK..",
             ".KKKKKK.",
             ".KSSSSK.",
             ".KYYYSK.",
             ".KSSSSK.",
             ".KKKKKK.",
             "..KK.KK.",
             "........"],
        ],
        "scale": 4, "bg": (25, 22, 20),
        "desc_id": "🐱 Cat — manja tapi setia. +10% gold.",
        "desc_en": "🐱 Cat — mischievous but loyal. +10% gold.",
    },
    "fairy_pet": {
        "frames": [
            ["...PP...",
             "..PPPPP.",
             ".PPPPP..",
             ".PYYYP..",
             ".PYYYP..",
             ".PPPPPP.",
             ".PPP.PP.",
             "........"],
            ["..PPPPP.",
            ".PPPYP..",
            ".PYYYP..",
            ".PYYYP..",
            ".PPPPPP.",
            ".PPP.PP.",
            "...PP...",
            "........"],
        ],
        "scale": 4, "bg": (180, 140, 220),
        "desc_id": "🧚 Fairy — magic boost. +20% EXP.",
        "desc_en": "🧚 Fairy — magic boost. +20% EXP.",
    },
    # ─── ITEMS (weapon) ─────────────────────────────────────
    "wooden_sword": {
        "frames": [["..R...", ".RR...", "..R...", ".RR...", "..R...", "....L.", "...L..", "....L."],
                   ["..R...", "..RR..", "..R...", ".RR...", "..R...", "....L.", "...L..", "....L."]],
        "scale": 6, "bg": (30, 25, 20),
        "desc_id": "🗡️ Pedang kayu sederhana. Starter weapon. +5 ATK.",
        "desc_en": "🗡️ Simple wooden sword. Starter weapon. +5 ATK.",
    },
    "iron_sword": {
        "frames": [["..SS...", ".SSS...", "..SSS..", "..S....", "..S....", "....L.", "...L..", "....L."],
                   ["..SS...", ".SSS...", "..SSS..", "..S....", "..S....", "....L.", "...L..", "....L."]],
        "scale": 6, "bg": (30, 30, 40),
        "desc_id": "⚔️ Pedang besi. +15 ATK. Beli di shop.",
        "desc_en": "⚔️ Iron sword. +15 ATK. Buy at shop.",
    },
    "steel_sword": {
        "frames": [["..SSSSS", ".SSSSS.", "..SSSSS", "..SS...", "..SS...", "...L...", "..L....", "...L..."],
                   ["...SSS.", ".SSSSS.", "..SSSSS", "..SS...", "..SS...", "...L...", "..L....", "...L..."]],
        "scale": 5, "bg": (20, 40, 70),
        "desc_id": "⚔️ Pedang baja tajam. +30 ATK.",
        "desc_en": "⚔️ Sharp steel sword. +30 ATK.",
    },
    "legendary_sword": {
        "frames": [["Z.ZZZZZ", "ZZZYYZZ", "..ZYYZ.", "..ZZZZ.", "..Z.YZ.", "...ZZ..", "...L...", "...L..."],
                   ["ZZZZZZZ", "ZYYYYYZ", "ZZZYYZZ", "..ZZZZ.", "..Z.YZ.", "...ZZ..", "...L...", "...L..."]],
        "scale": 5, "bg": (180, 150, 10),
        "desc_id": "⚔️✨ Pedang legendaris. +100 ATK. Shop premium.",
        "desc_en": "⚔️✨ Legendary sword. +100 ATK. Premium shop.",
    },
    # ─── ARMOR ──────────────────────────────────────────────
    "leather_armor": {
        "frames": [["...KK...", ".KKKKKK.", "KKKKKKKK", "KKKKKKKK", "KKK..KKK", ".KK..KK.", "..KKKK..", "........"],
                   ["...KK...", ".KKKKKK.", "KKKKKKKK", "KKKKKKKK", "K KK KK ", ".KK..KK.", "..KKKK..", "........"]],
        "scale": 4, "bg": (40, 30, 20),
        "desc_id": "🛡️ Armor kulit. +5 DEF. Starter armor.",
        "desc_en": "🛡️ Leather armor. +5 DEF. Starter armor.",
    },
    "iron_armor": {
        "frames": [["...SS...", ".SSSSSS.", "SSSSSSSS", "SSSSSSSS", "SSS..SSS", ".SS..SS.", "..SSSS..", "........"],
                   ["...SS...", ".SSSSSS.", "SSSSSSSS", "SSSSSSSS", "SS S SS ", ".SS..SS.", "..SSSS..", "........"]],
        "scale": 4, "bg": (30, 30, 50),
        "desc_id": "🛡️ Armor besi. +15 DEF.",
        "desc_en": "🛡️ Iron armor. +15 DEF.",
    },
    "dragon_armor": {
        "frames": [["...ZZ...", ".ZZZZZZ.", "ZZZZZZZZ", "ZZZHZZZZ", "ZZZHHZZZ", ".ZZZZZZ.", "..ZZZZ..", "........"],
                   ["...ZZ...", ".ZZZZZZ.", "ZZZZZZZZ", "ZZZHZZZZ", "ZZZHHZZZ", ".ZZZZZZ.", "..ZZZZ..", "........"]],
        "scale": 4, "bg": (60, 20, 20),
        "desc_id": "🛡️🐉 Armor naga. +80 DEF. Shop premium.",
        "desc_en": "🛡️🐉 Dragon armor. +80 DEF. Premium shop.",
    },
    # ─── POTIONS ───────────────────────────────────────────
    "health_potion": {
        "frames": [["....R...", "...RRR..", "..RRRRR.", ".RRRRRR.", ".RRRRRR.", ".RRRRRR.", "..RRRR..", "........"],
                   ["....R...", "...RRR..", "..RRRRR.", ".RRRRRR.", ".RRRRRR.", ".RRRRRR.", "..RRRR..", "........"]],
        "scale": 6, "bg": (40, 20, 20),
        "desc_id": "🧪 Ramuan HP — +30 HP.",
        "desc_en": "🧪 HP Potion — +30 HP.",
    },
    "energy_potion": {
        "frames": [["....YY...", "...YYYY..", "..YYYYYY.", ".YYYYYYY.", ".YYYYYYY.", ".YYYYYYY.", "..YYYYY..", "........"],
                   ["....YY...", "...YYYY..", "..YYYYYY.", ".YYYYYYY.", ".YYYYYYY.", ".YYYYYYY.", "..YYYYY..", "........"]],
        "scale": 6, "bg": (40, 35, 10),
        "desc_id": "⚡ Ramuan Energi — +25 Energy.",
        "desc_en": "⚡ Energy Potion — +25 Energy.",
    },
    "big_potion": {
        "frames": [["....R...", "...RRR..", "..RRRRR.", ".RRRRRR.", ".RRRRRR.", ".RRRRRR.", "..RRRR..", "...LL..."],
                   ["....R...", "...RRR..", "..RRRRR.", ".RRRRRR.", ".RRRRRR.", ".RRRRRR.", "..RRRR..", "...LL..."]],
        "scale": 6, "bg": (60, 15, 15),
        "desc_id": "🧪💎 Ramuan HP Besar — +80 HP.",
        "desc_en": "🧪💎 Big HP Potion — +80 HP.",
    },
}


def _render_sprite(frame: list, scale: int, bg: tuple) -> bytes:
    """Render one sprite frame as PNG bytes."""
    try:
        from PIL import Image
    except Exception:
        return b""

    w, h = len(frame[0]), len(frame)
    img = Image.new("RGBA", (w * scale, h * scale), bg + (255,))
    for y, row in enumerate(frame):
        for x, ch in enumerate(row):
            color = PIXEL.get(ch)
            if color:
                img.paste(color + (255,), (x * scale, y * scale, (x + 1) * scale, (y + 1) * scale))
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def _render_animated(frame1: list, frame2: list, scale: int, bg: tuple, key: str) -> bytes:
    """Render 2-frame animated GIF."""
    try:
        from PIL import Image
    except Exception:
        return b""

    w, h = len(frame1[0]), len(frame1)
    W, H = w * scale, h * scale
    frames = []
    for frame in [frame1, frame2]:
        img = Image.new("RGBA", (W, H), bg + (255,))
        for y, row in enumerate(frame):
            for x, ch in enumerate(row):
                color = PIXEL.get(ch)
                if color:
                    img.paste(color + (255,), (x * scale, y * scale, (x + 1) * scale, (y + 1) * scale))
        frames.append(img.copy())
    buf = io.BytesIO()
    frames[0].save(buf, "GIF", save_all=True, append_images=frames[1:], duration=600, loop=0)
    return buf.getvalue()


def _cache_path(key: str, ext: str) -> str:
    h = hashlib.md5(key.encode()).hexdigest()[:8]
    return os.path.join(CACHE_DIR, f"{key}_{h}.{ext}")


def get_sprite(key: str, animate: bool = False) -> Optional[bytes]:
    """Return PNG bytes for sprite. None if PIL not available."""
    s = SPRITES.get(key)
    if not s:
        return None
    frames = s["frames"]
    scale = s.get("scale", 4)
    bg = s.get("bg", (20, 22, 28))
    try:
        from PIL import Image
    except Exception:
        return None
    if animate and len(frames) >= 2:
        path = _cache_path(f"{key}_ani", "gif")
        if not os.path.exists(path):
            data = _render_animated(frames[0], frames[1], scale, bg, key)
            if data:
                with open(path, "wb") as f:
                    f.write(data)
        if os.path.exists(path):
            with open(path, "rb") as f:
                return f.read()
    path = _cache_path(key, "png")
    if not os.path.exists(path):
        data = _render_sprite(frames[0], scale, bg)
        if data:
            with open(path, "wb") as f:
                f.write(data)
    if os.path.exists(path):
        with open(path, "rb") as f:
            return f.read()
    return None


def get_sprite_url(key: str) -> str:
    """Return local file:// path for send_document or send_photo."""
    s = SPRITES.get(key)
    if not s:
        return ""
    scale = s.get("scale", 4)
    frames = s["frames"]
    bg = s.get("bg", (20, 22, 28))
    try:
        from PIL import Image
    except Exception:
        return ""
    path = _cache_path(key, "png")
    if not os.path.exists(path):
        _render_sprite(frames[0], scale, bg)
    return path


def sprite_desc(key: str, lang: str) -> str:
    s = SPRITES.get(key, {})
    return s.get("desc_id", s.get("desc_en", "")) if lang == "id" else s.get("desc_en", s.get("desc_id", ""))