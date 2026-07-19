"""
Image generation for Journey of the Hero.
Primary: Pollinations.ai (free, no key, decent quality) — runs async
Fallback: local PIL pixel sprites (instant, always works) — runs in sync
"""

from __future__ import annotations

import asyncio
import hashlib
import io
import os
import random
import threading
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional, Tuple, Dict

from modules.config import POLLINATIONS_API_URL, IMAGE_CACHE_DIR, IMAGE_TIMEOUT

CACHE_DIR = Path(IMAGE_CACHE_DIR)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

_CACHE: Dict[str, bytes] = {}


def _cache_key(prompt: str) -> str:
    return hashlib.sha256(prompt.encode()).hexdigest()[:20]


def _load_cache(key: str) -> Optional[bytes]:
    if key in _CACHE:
        return _CACHE[key]
    path = CACHE_DIR / f"{key}.png"
    if path.exists():
        data = path.read_bytes()
        _CACHE[key] = data
        return data
    return None


def _save_cache(key: str, data: bytes):
    _CACHE[key] = data
    try:
        (CACHE_DIR / f"{key}.png").write_bytes(data)
    except Exception:
        pass


# ─── POLLINATIONS (background) ────────────────────────────────
def _pollinations_fetch(prompt: str, size: Tuple[int, int]) -> Optional[bytes]:
    """Fetch from Pollinations.ai. Blocks. Call in thread."""
    seed = random.randint(1, 1_000_000)
    import urllib.parse
    url = (
        f"{POLLINATIONS_API_URL.rstrip('/')}/prompt/{urllib.parse.quote(prompt)}"
        f"?width={size[0]}&height={size[1]}&seed={seed}&nologo=true&private=true"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "JourneyOfHero/1.0"})
        with urllib.request.urlopen(req, timeout=IMAGE_TIMEOUT) as resp:
            if resp.status == 200:
                data = resp.read()
                if len(data) > 1000:
                    return data
    except Exception:
        pass
    return None


# ─── PIXEL FALLBACK (instant) ──────────────────────────────
def _pixel_fallback(prompt: str) -> Optional[bytes]:
    """Instant local pixel art. Always works."""
    try:
        import pixel_art
        prompt_lower = prompt.lower()
        key = None
        if "slime" in prompt_lower: key = "slime"
        elif "goblin" in prompt_lower: key = "goblin"
        elif "wolf" in prompt_lower: key = "wolf"
        elif "dragon" in prompt_lower: key = "dragon"
        elif "orc" in prompt_lower: key = "orc"
        elif "troll" in prompt_lower: key = "troll"
        elif "bat" in prompt_lower: key = "bat"
        elif "skeleton" in prompt_lower: key = "skeleton"
        elif "wraith" in prompt_lower: key = "wraith"
        elif "yeti" in prompt_lower: key = "yeti"
        elif "harpy" in prompt_lower: key = "harpy"
        elif "golem" in prompt_lower: key = "golem"
        elif "ent" in prompt_lower: key = "ent"
        elif "bandit" in prompt_lower: key = "bandit"
        elif "boar" in prompt_lower or "babi" in prompt_lower: key = "wild_boar"
        elif "swamp" in prompt_lower or "rawa" in prompt_lower: key = "swamp"
        elif "plains" in prompt_lower or "dataran" in prompt_lower: key = "plains"
        elif "forest" in prompt_lower or "hutan" in prompt_lower: key = "forest"
        elif "cave" in prompt_lower or "gua" in prompt_lower: key = "cave"
        elif "mountain" in prompt_lower or "gunung" in prompt_lower: key = "mountain"
        elif "ruins" in prompt_lower or "purba" in prompt_lower: key = "ruins"
        elif "desert" in prompt_lower or "gurun" in prompt_lower: key = "desert"
        elif "crystal" in prompt_lower or "kristal" in prompt_lower: key = "crystal_caves"
        elif "sky" in prompt_lower or "langit" in prompt_lower: key = "sky_isles"
        elif "void" in prompt_lower: key = "void"
        elif "abyss" in prompt_lower: key = "abyss"
        elif "boss" in prompt_lower: key = "dragon"
        elif "pet" in prompt_lower: key = "cat_pet"
        elif "achievement" in prompt_lower or "prestasi" in prompt_lower: key = "first_blood"
        elif "sidejob" in prompt_lower or "pekerjaan" in prompt_lower: key = "farmer"

        if key and key in pixel_art.SPRITES:
            data = pixel_art.get_sprite(key)
            if data:
                from PIL import Image
                img = Image.open(io.BytesIO(data))
                img = img.resize((512, 512), Image.NEAREST)
                out = io.BytesIO()
                img.save(out, format="PNG")
                return out.getvalue()
    except Exception:
        pass

    # ultimate fallback: solid color
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (512, 512), (25, 25, 35, 255))
    h = hashlib.md5(prompt.encode()).hexdigest()
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    draw = ImageDraw.Draw(img)
    draw.rectangle([10, 10, 502, 502], fill=(r, g, b, 200))
    out = io.BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()


def _get_cached_by_name(key: str, dtype: str = "") -> Optional[bytes]:
    """Check if named file exists in .pixel_cache directory (e.g. monster_slime.png, boss_dragon.png)."""
    candidates = []
    if dtype:
        candidates.append(CACHE_DIR / f"{dtype}_{key}.png")
    candidates.append(CACHE_DIR / f"{key}.png")

    for p in candidates:
        if p.exists() and p.is_file():
            data = p.read_bytes()
            if len(data) > 50:
                return data
    return None


def generate_image(key_or_prompt: str, dtype: str = "", name: str = "") -> Optional[bytes]:
    """
    Main image resolver. Checks named cache files first (e.g. monster_slime.png, boss_dragon.png),
    then prompt cache, then local pixel fallback.
    """
    if key_or_prompt:
        cached_named = _get_cached_by_name(key_or_prompt, dtype)
        if cached_named:
            return cached_named

    prompt = name or key_or_prompt
    ckey = _cache_key(prompt)
    cached_prompt = _load_cache(ckey)
    if cached_prompt:
        return cached_prompt

    pixel = _pixel_fallback(prompt)
    if pixel:
        _save_cache(ckey, pixel)
        return pixel

    return None


def generate_image_sync(prompt: str) -> Optional[bytes]:
    """Instant generation for sync callers (tick loop)."""
    return generate_image(prompt)


def caption_for(dtype: str, name: str, lang: str = "id") -> str:
    if lang == "id":
        return {
            "monster": f"👹 *{name}* pertama kali ditemukan!",
            "boss":    f"👹 *{name}* pertama kali ditemukan!",
            "pet":     f"🐾 *{name}* ikut petualangan!",
            "item":    f"✨ Dapat *{name}*!",
            "zone":    f"🗺️ Masuk *{name}*!",
            "sidejob": f"🛠 *{name}* dimulai!",
            "achievement": f"🏅 Achievement: *{name}*!",
        }.get(dtype, f"✨ *{name}*")
    return {
        "monster": f"👹 First encounter: *{name}*!",
        "boss":    f"👹 First encounter: *{name}*!",
        "pet":     f"🐾 *{name}* joins the party!",
        "item":    f"✨ Obtained *{name}*!",
        "zone":    f"🗺️ Entered *{name}*!",
        "sidejob": f"🛠 *{name}* started!",
        "achievement": f"🏅 Achievement unlocked: *{name}*!",
    }.get(dtype, f"✨ *{name}*")
