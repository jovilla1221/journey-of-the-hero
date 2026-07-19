"""
Personality system — hero personality evolves based on journey events.

Traitsakeup
────────────
Each trait has points (0-100). Events add/remove points.
Top 3 traits become the hero's "personality".
Title is derived from dominant trait combination.

Triggers:
- Battle win/lose → bravery, resilience, aggression
- Boss kill → bravery, glory
- Pet found → compassion, bond
- Death (HP=0) → resilience, wisdom
- Gold earned → ambition
- Contract done → discipline, honor
- Temple built → devotion, wisdom
- Prestige → glory, wisdom
- Hard foe → bravery, resilience
- PvP duel → aggression, glory (win) / resilience (lose)
- Adventure discover → curiosity, wisdom
- Streak → discipline, resilience
- Low energy rest → patience
"""

import json
from datetime import datetime, timezone

# ── Trait definitions ──────────────────────────────────────────────
TRAIT_DEFS = {
    "bravery":      {"emoji": "⚔️", "desc": "Keberanian",     "title_parts": ["Pemberani", "Berani"]},
    "resilience":   {"emoji": "🛡️", "desc": "Ketangguhan",   "title_parts": ["Tangguh", "Baja"]},
    "aggression":   {"emoji": "🔥", "desc": "Agresi",         "title_parts": ["Garang", "Beringas"]},
    "compassion":   {"emoji": "💗", "desc": "Welas asih",     "title_parts": ["Penyayang", "Berhati Lembut"]},
    "wisdom":       {"emoji": "📚", "desc": "Kebijaksanaan", "title_parts": ["Bijaksana", "Cendekia"]},
    "ambition":     {"emoji": "💰", "desc": "Ambisi",         "title_parts": ["Berambisi", "Rajin"]},
    "discipline":   {"emoji": "📐", "desc": "Disiplin",       "title_parts": ["Disiplin", "Tekun"]},
    "honor":        {"emoji": "🎖️", "desc": "Kehormatan",     "title_parts": ["Terhormat", "Setia"]},
    "devotion":     {"emoji": "🙏", "desc": "Kesetiaan",      "title_parts": ["Setia", "Taat"]},
    "glory":        {"emoji": "👑", "desc": "Kemuliaan",       "title_parts": ["Glorius", "Jaya"]},
    "curiosity":    {"emoji": "🔍", "desc": "Rasa ingin tahu","title_parts": ["Penantas", "Pencari"]},
    "patience":     {"emoji": "⏳", "desc": "Kesabaran",      "title_parts": ["Sabar", "Tenang"]},
    "bond":         {"emoji": "🐾", "desc": "Ikatan",          "title_parts": ["Setia Kawan", "Bersahabat"]},
    "cunning":      {"emoji": "🦊", "desc": "Kelicikan",       "title_parts": ["Cerdik", "Licik"]},
}

# ── Event → trait point mapping ─────────────────────────────────────
EVENT_MAP = {
    "win":      {"bravery": 2, "aggression": 1},
    "lose":     {"resilience": 3, "patience": 1},
    "boss_kill":{"bravery": 5, "glory": 3, "aggression": 2},
    "hard_kill":{"bravery": 3, "resilience": 2},
    "death":    {"resilience": 4, "wisdom": 1},
    "pet_found":{"compassion": 3, "bond": 4, "curiosity": 1},
    "gold":     {"ambition": 1},
    "contract": {"discipline": 3, "honor": 2},
    "temple":   {"devotion": 5, "wisdom": 2},
    "prestige": {"glory": 5, "wisdom": 2, "honor": 2},
    "duel_win": {"aggression": 3, "glory": 2, "bravery": 1},
    "duel_lose":{"resilience": 3, "patience": 1},
    "discover": {"curiosity": 3, "wisdom": 1},
    "streak":   {"discipline": 2, "resilience": 1},
    "rest":     {"patience": 1},
    "flee":     {"cunning": 2, "patience": -1},
}

# ── Title combinations ──────────────────────────────────────────────
TITLE_COMBOS = {
    ("bravery", "glory"):     "Sang Jaya",
    ("bravery", "aggression"):"Beringas",
    ("bravery", "resilience"):"Baja Berani",
    ("resilience", "patience"):"Benteng Tabah",
    ("compassion", "bond"):   "Sahabat Sejati",
    ("wisdom", "curiosity"):  "Pencari Pengetahuan",
    ("ambition", "discipline"):"Pemburu Impian",
    ("devotion", "honor"):    "Abdi Setia",
    ("glory", "honor"):       "Ksatria Mulia",
    ("cunning", "wisdom"):    "Rubah Cendekia",
    ("aggression", "cunning"):"Predator Licik",
    ("bond", "devotion"):     "Pelihara Jiwa",
}

DEFAULT_TITLE = "Pengembara"
DEFAULT_TRAITS = ["bravery", "curiosity"]


def get_points(player: dict) -> dict:
    """Parse personality_points JSON from player dict."""
    raw = player.get("personality_points", "{}")
    if isinstance(raw, dict):
        return dict(raw)
    try:
        return json.loads(raw) if raw else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def get_traits(player: dict) -> list:
    """Parse personality_traits JSON."""
    raw = player.get("personality_traits", "[]")
    if isinstance(raw, list):
        return list(raw)
    try:
        return json.loads(raw) if raw else []
    except (json.JSONDecodeError, TypeError):
        return []


def apply_event(player: dict, event: str, multiplier: float = 1.0) -> dict | None:
    """
    Apply a journey event to player personality.
    Returns updated dict: {trait: new_points} or None if event unknown.

    Does NOT write to DB — caller must persist.
    Returns the new personality state for saving.
    """
    mapping = EVENT_MAP.get(event)
    if not mapping:
        return None

    points = get_points(player)
    for trait, delta in mapping.items():
        cur = points.get(trait, 0)
        points[trait] = max(0, min(100, cur + int(delta * multiplier)))

    # Recompute top traits
    sorted_traits = sorted(points.items(), key=lambda x: x[1], reverse=True)
    top_traits = [t for t, p in sorted_traits if p > 0][:3]
    if not top_traits:
        top_traits = list(DEFAULT_TRAITS)

    # Compute title
    title = _compute_title(top_traits, points)

    return {
        "personality_points": json.dumps(points),
        "personality_traits": json.dumps(top_traits),
        "personality_title": title,
        "personality_updated_at": datetime.now(timezone.utc).isoformat(),
    }


def _compute_title(traits: list, points: dict) -> str:
    """Derive title from trait combo."""
    if len(traits) < 2:
        return DEFAULT_TITLE

    # Check exact combo
    pair = tuple(sorted(traits[:2]))
    for (t1, t2), title in TITLE_COMBOS.items():
        if (t1, t2) == pair or (t2, t1) == pair:
            return title

    # Single dominant trait title
    top = traits[0]
    if top in TRAIT_DEFS:
        parts = TRAIT_DEFS[top]["title_parts"]
        # Use high point title if very dominant
        if points.get(top, 0) >= 50:
            return parts[0]
        return f"{parts[-1]}"

    return DEFAULT_TITLE


def personality_text(player: dict) -> str:
    """Format personality for hero card / profile display."""
    traits = get_traits(player)
    points = get_points(player)
    title = player.get("personality_title") or DEFAULT_TITLE

    if not points:
        return f"{title}\n_Belum ada jejak kepribadian yang menonjol._"

    lines = [f"{title}\n"]
    for t in traits:
        p = points.get(t, 0)
        if t in TRAIT_DEFS:
            emoji = TRAIT_DEFS[t]["emoji"]
            desc = TRAIT_DEFS[t]["desc"]
            bar_len = min(10, p // 10)
            bar = "█" * bar_len + "░" * (10 - bar_len)
            lines.append(f"  {emoji} {desc} `{bar} {p}`")

    return "\n".join(lines)


def personality_summary(player: dict) -> str:
    """Short one-line summary for daily report / hero card inline."""
    traits = get_traits(player)
    title = player.get("personality_title") or DEFAULT_TITLE
    if not traits:
        return title

    emojis = []
    names = []
    for t in traits[:3]:
        if t in TRAIT_DEFS:
            emojis.append(TRAIT_DEFS[t]["emoji"])
            names.append(TRAIT_DEFS[t]["desc"])
    return f"{title} — {' '.join(emojis)} {' / '.join(names)}"
