"""
Image generation for Journey of the Hero.
Primary: Google Gemini image models (API key AQ.*).
Fallback: local PIL pixel sprites (pixel_art.py).
"""

from __future__ import annotations

import base64
import io
import json
import os
import urllib.error
import urllib.request
from typing import Optional, Tuple

from modules.config import GOOGLE_API_KEY, IMAGE_MODEL, CACHE_DIR

# Ensure cache dir
os.makedirs(CACHE_DIR, exist_ok=True)

# Prompt templates — always force pixel style
_PROMPTS = {
    "monster": (
        "Pixel art game sprite of a {name}, 32x32 style, limited 16-color palette, "
        "retro 16-bit RPG enemy, clean silhouette, dark simple background, no text, no watermark."
    ),
    "boss": (
        "Epic pixel art boss monster {name}, 48x48 style, dramatic pose, "
        "retro 16-bit RPG boss, limited palette, dark vignette background, no text."
    ),
    "pet": (
        "Cute pixel art pet companion {name}, 32x32, chibi, retro game sprite, "
        "soft colors, transparent-looking dark background, no text."
    ),
    "item": (
        "Pixel art inventory item icon {name}, 32x32, centered, "
        "retro RPG item, clean edges, dark background, no text."
    ),
    "zone": (
        "Pixel art landscape of zone {name}, wide 16:9 feel but square crop, "
        "16-bit RPG overworld scene, limited palette, atmospheric, no text."
    ),
    "sidejob": (
        "Pixel art scene of side job {name}, 16-bit RPG work scene, "
        "hero doing the job, simple composition, no text."
    ),
    "achievement": (
        "Pixel art achievement badge for {name}, golden medal style, "
        "16-bit RPG trophy icon, centered, dark background, no text."
    ),
}


def _cache_path(key: str, dtype: str) -> str:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in f"{dtype}_{key}")
    return os.path.join(CACHE_DIR, f"{safe}.png")


def _read_cache(path: str) -> Optional[bytes]:
    if os.path.isfile(path) and os.path.getsize(path) > 50:
        with open(path, "rb") as f:
            return f.read()
    return None


def _write_cache(path: str, data: bytes) -> None:
    try:
        with open(path, "wb") as f:
            f.write(data)
    except Exception:
        pass


def _gemini_image(prompt: str) -> Optional[bytes]:
    """Call Gemini image-capable model. Returns PNG bytes or None."""
    key = GOOGLE_API_KEY
    if not key:
        return None
    model = IMAGE_MODEL or "gemini-2.5-flash-image"
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={key}"
    )
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
            "temperature": 0.4,
        },
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": key,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        # 429 quota / 404 model — silent fallback
        try:
            err = e.read().decode("utf-8")[:200]
        except Exception:
            err = str(e)
        # log-ish via print only in debug; keep quiet for bot
        return None
    except Exception:
        return None

    # Parse inline image data from candidates
    try:
        cands = data.get("candidates") or []
        for cand in cands:
            parts = ((cand.get("content") or {}).get("parts")) or []
            for part in parts:
                inline = part.get("inlineData") or part.get("inline_data")
                if not inline:
                    continue
                b64 = inline.get("data")
                mime = (inline.get("mimeType") or inline.get("mime_type") or "").lower()
                if b64 and ("image" in mime or not mime):
                    return base64.b64decode(b64)
    except Exception:
        return None
    return None


def _local_pixel(key: str, dtype: str, name: str) -> Optional[bytes]:
    """Fallback to hand-authored pixel sprites."""
    try:
        from pixel_art import get_sprite, SPRITES
    except Exception:
        return None
    # direct key match
    data = get_sprite(key)
    if data:
        return data
    # try aliases
    aliases = {
        "wild_boar": "orc",
        "bandit": "goblin",
        "wolf": "goblin",
        "ent": "troll",
        "forest_witch": "wraith",
        "bat": "spider",
        "golem": "troll",
        "harpy": "wraith",
        "yeti": "troll",
        "lich": "wraith",
        "void_spawn": "demon",
        "void_knight": "demon",
        "wolf_pup": "wolf_pet",
        "fox": "cat_pet",
        "owl": "fairy_pet",
        "slime_pet": "slime",
        "cat": "cat_pet",
        "phoenix": "phoenix_pet",
        "golden_pet": "dragon_pet",
        "plains": "slime",
        "forest": "goblin",
        "cave": "troll",
        "mountain": "dragon",
        "ruins": "skeleton",
        "void": "demon",
        "swamp": "slime",
        "desert": "orc",
        "crystal_caves": "slime_king",
        "sky_isles": "harpy" if "harpy" in SPRITES else "wraith",
        "abyss": "demon",
    }
    alt = aliases.get(key)
    if alt:
        data = get_sprite(alt)
        if data:
            return data
    # generic by type
    generic = {
        "monster": "slime",
        "boss": "dragon",
        "pet": "cat_pet",
        "item": "wooden_sword",
        "zone": "slime",
        "sidejob": "health_potion",
        "achievement": "legendary_sword",
    }
    return get_sprite(generic.get(dtype, "slime"))


def generate_image(key: str, dtype: str, name: str, force_local: bool = False) -> Optional[bytes]:
    """
    Generate (or load cached) PNG bytes for discovery event.
    dtype: monster|boss|pet|item|zone|sidejob|achievement
    """
    path = _cache_path(key, dtype)
    cached = _read_cache(path)
    if cached:
        return cached

    prompt_tpl = _PROMPTS.get(dtype) or _PROMPTS["monster"]
    prompt = prompt_tpl.format(name=name)

    img: Optional[bytes] = None
    if not force_local:
        img = _gemini_image(prompt)

    if not img:
        img = _local_pixel(key, dtype, name)

    if img:
        _write_cache(path, img)
    return img


def caption_for(dtype: str, name: str, lang: str = "id") -> str:
    if lang == "id":
        labels = {
            "monster": f"🆕 Musuh baru: *{name}*",
            "boss": f"👑 BOSS pertama: *{name}*",
            "pet": f"🐾 Pet baru: *{name}*",
            "item": f"🎁 Item baru: *{name}*",
            "zone": f"🗺️ Zona baru: *{name}*",
            "sidejob": f"🛠 Mulai kerja: *{name}*",
            "achievement": f"🏅 Achievement: *{name}*",
        }
    else:
        labels = {
            "monster": f"🆕 New foe: *{name}*",
            "boss": f"👑 First BOSS: *{name}*",
            "pet": f"🐾 New pet: *{name}*",
            "item": f"🎁 New item: *{name}*",
            "zone": f"🗺️ New zone: *{name}*",
            "sidejob": f"🛠 Job start: *{name}*",
            "achievement": f"🏅 Achievement: *{name}*",
        }
    return labels.get(dtype, f"✨ *{name}*")
