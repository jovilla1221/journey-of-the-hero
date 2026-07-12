"""Database module — single shared connection + lock (no lock storms)."""

import sqlite3
import threading
from datetime import datetime, timezone, date
from typing import Optional, List, Dict, Any

from modules.config import DB_PATH

_LOCK = threading.RLock()
_CONN: Optional[sqlite3.Connection] = None


class _SharedConn:
    """Wrapper: close() is no-op so callers that close don't kill the pool."""

    def __init__(self, conn: sqlite3.Connection):
        object.__setattr__(self, "_conn", conn)

    def close(self):
        return None

    def __getattr__(self, name):
        return getattr(object.__getattribute__(self, "_conn"), name)


def get_conn() -> sqlite3.Connection:
    """Process-wide single connection. Always use under _LOCK for writes."""
    global _CONN
    with _LOCK:
        if _CONN is None:
            c = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
            c.row_factory = sqlite3.Row
            c.execute("PRAGMA journal_mode=WAL")
            c.execute("PRAGMA busy_timeout=5000")
            c.execute("PRAGMA foreign_keys=ON")
            c.execute("PRAGMA synchronous=NORMAL")
            _CONN = c
        return _SharedConn(_CONN)


def init_db():
    with _LOCK:
        c = get_conn()
        c.executescript("""
        CREATE TABLE IF NOT EXISTS players (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            name TEXT DEFAULT 'Hero',
            deity_name TEXT,
            lang TEXT DEFAULT 'id',
            gold INTEGER DEFAULT 1000,
            diamond INTEGER DEFAULT 0,
            hp INTEGER DEFAULT 100,
            max_hp INTEGER DEFAULT 100,
            atk INTEGER DEFAULT 10,
            def INTEGER DEFAULT 5,
            energy INTEGER DEFAULT 50,
            max_energy INTEGER DEFAULT 50,
            level INTEGER DEFAULT 1,
            exp INTEGER DEFAULT 0,
            weapon TEXT,
            armor TEXT,
            pet TEXT,
            buff_exp_until TEXT,
            diary TEXT,
            adventuring INTEGER DEFAULT 1,
            last_tick TEXT,
            onboard_step TEXT DEFAULT 'lang',
            zone TEXT DEFAULT 'plains',
            sidejob_key TEXT,
            sidejob_step INTEGER DEFAULT 0,
            streak INTEGER DEFAULT 0,
            last_streak TEXT,
            last_daily TEXT,
            day_kills INTEGER DEFAULT 0,
            day_gold INTEGER DEFAULT 0,
            day_exp INTEGER DEFAULT 0,
            day_jobs INTEGER DEFAULT 0,
            week_kills INTEGER DEFAULT 0,
            week_gold INTEGER DEFAULT 0,
            week_jobs INTEGER DEFAULT 0,
            week_hard INTEGER DEFAULT 0,
            week_pets INTEGER DEFAULT 0,
            contract_day INTEGER DEFAULT 0,
            contract_key TEXT,
            contract_progress INTEGER DEFAULT 0,
            prestige INTEGER DEFAULT 0,
            prestige_bonus_atk INTEGER DEFAULT 0,
            prestige_bonus_def INTEGER DEFAULT 0,
            guild_id INTEGER,
            duel_foe_id INTEGER,
            duel_step INTEGER DEFAULT 0,
            duel_payload TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            item_key TEXT NOT NULL,
            quantity INTEGER DEFAULT 1,
            UNIQUE(user_id, item_key)
        );
        CREATE TABLE IF NOT EXISTS battles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            monster TEXT,
            result TEXT,
            exp_gained INTEGER DEFAULT 0,
            gold_earned INTEGER DEFAULT 0,
            diamond_earned INTEGER DEFAULT 0,
            zone TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS friends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            friend_id INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, friend_id)
        );
        CREATE TABLE IF NOT EXISTS pvp_duels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            challenger_id INTEGER NOT NULL,
            target_id INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            winner_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS guilds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            owner_id INTEGER NOT NULL,
            member_count INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS guild_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            role TEXT DEFAULT 'member',
            join_code TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(guild_id, user_id)
        );
        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            ach_key TEXT NOT NULL,
            claimed INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, ach_key)
        );
        CREATE TABLE IF NOT EXISTS pet_contracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            pet_key TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS blessings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            bless_key TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS discoveries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            discovery_key TEXT NOT NULL,
            discovery_type TEXT NOT NULL,
            discovered_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, discovery_key)
        );
        """)
        cols = {r["name"] for r in c.execute("PRAGMA table_info(players)").fetchall()}
        _migrations = {
            "zone": "ALTER TABLE players ADD COLUMN zone TEXT DEFAULT 'plains'",
            "sidejob_key": "ALTER TABLE players ADD COLUMN sidejob_key TEXT",
            "sidejob_step": "ALTER TABLE players ADD COLUMN sidejob_step INTEGER DEFAULT 0",
            "streak": "ALTER TABLE players ADD COLUMN streak INTEGER DEFAULT 0",
            "last_streak": "ALTER TABLE players ADD COLUMN last_streak TEXT",
            "last_daily": "ALTER TABLE players ADD COLUMN last_daily TEXT",
            "day_kills": "ALTER TABLE players ADD COLUMN day_kills INTEGER DEFAULT 0",
            "day_gold": "ALTER TABLE players ADD COLUMN day_gold INTEGER DEFAULT 0",
            "day_exp": "ALTER TABLE players ADD COLUMN day_exp INTEGER DEFAULT 0",
            "day_jobs": "ALTER TABLE players ADD COLUMN day_jobs INTEGER DEFAULT 0",
            "week_kills": "ALTER TABLE players ADD COLUMN week_kills INTEGER DEFAULT 0",
            "week_gold": "ALTER TABLE players ADD COLUMN week_gold INTEGER DEFAULT 0",
            "week_jobs": "ALTER TABLE players ADD COLUMN week_jobs INTEGER DEFAULT 0",
            "week_hard": "ALTER TABLE players ADD COLUMN week_hard INTEGER DEFAULT 0",
            "week_pets": "ALTER TABLE players ADD COLUMN week_pets INTEGER DEFAULT 0",
            "contract_day": "ALTER TABLE players ADD COLUMN contract_day INTEGER DEFAULT 0",
            "contract_key": "ALTER TABLE players ADD COLUMN contract_key TEXT",
            "contract_progress": "ALTER TABLE players ADD COLUMN contract_progress INTEGER DEFAULT 0",
            "prestige": "ALTER TABLE players ADD COLUMN prestige INTEGER DEFAULT 0",
            "prestige_bonus_atk": "ALTER TABLE players ADD COLUMN prestige_bonus_atk INTEGER DEFAULT 0",
            "prestige_bonus_def": "ALTER TABLE players ADD COLUMN prestige_bonus_def INTEGER DEFAULT 0",
            "guild_id": "ALTER TABLE players ADD COLUMN guild_id INTEGER",
            "buff_exp_until": "ALTER TABLE players ADD COLUMN buff_exp_until TEXT",
            "duel_foe_id": "ALTER TABLE players ADD COLUMN duel_foe_id INTEGER",
            "duel_step": "ALTER TABLE players ADD COLUMN duel_step INTEGER DEFAULT 0",
            "duel_payload": "ALTER TABLE players ADD COLUMN duel_payload TEXT",
            "deity_name": "ALTER TABLE players ADD COLUMN deity_name TEXT",
            "lang": "ALTER TABLE players ADD COLUMN lang TEXT DEFAULT 'id'",
            "diary": "ALTER TABLE players ADD COLUMN diary TEXT",
            "adventuring": "ALTER TABLE players ADD COLUMN adventuring INTEGER DEFAULT 1",
            "last_tick": "ALTER TABLE players ADD COLUMN last_tick TEXT",
            "onboard_step": "ALTER TABLE players ADD COLUMN onboard_step TEXT DEFAULT 'lang'",
            "diamond": "ALTER TABLE players ADD COLUMN diamond INTEGER DEFAULT 0",
        }
        for col, sql in _migrations.items():
            if col not in cols:
                try:
                    c.execute(sql)
                except Exception:
                    pass
        bcols = {r["name"] for r in c.execute("PRAGMA table_info(battles)").fetchall()}
        if "diamond_earned" not in bcols:
            try:
                c.execute("ALTER TABLE battles ADD COLUMN diamond_earned INTEGER DEFAULT 0")
            except Exception:
                pass
        if "zone" not in bcols:
            try:
                c.execute("ALTER TABLE battles ADD COLUMN zone TEXT")
            except Exception:
                pass
        c.commit()


def get_player(uid: int) -> Optional[dict]:
    with _LOCK:
        c = get_conn()
        r = c.execute("SELECT * FROM players WHERE user_id=?", (uid,)).fetchone()
        return dict(r) if r else None


def create_player(uid: int, username: str, name: str) -> dict:
    with _LOCK:
        c = get_conn()
        c.execute(
            "INSERT OR IGNORE INTO players (user_id, username, name, onboard_step, adventuring) VALUES (?,?,?,?,1)",
            (uid, username or "", name or "Hero", "lang"),
        )
        c.commit()
    return get_player(uid)


def goc(uid: int, username: str = "", name: str = "") -> dict:
    return get_player(uid) or create_player(uid, username, name)


def upd(uid: int, **kw):
    if not kw:
        return
    if "def_" in kw:
        kw["def"] = kw.pop("def_")
    sets = ", ".join(f'"{k}"=?' for k in kw)
    with _LOCK:
        c = get_conn()
        c.execute(f"UPDATE players SET {sets} WHERE user_id=?", list(kw.values()) + [uid])
        c.commit()


def add_gold(uid: int, n: int):
    with _LOCK:
        c = get_conn()
        c.execute(
            "UPDATE players SET gold=gold+?, day_gold=COALESCE(day_gold,0)+?, week_gold=COALESCE(week_gold,0)+? WHERE user_id=?",
            (n, max(0, n), max(0, n), uid),
        )
        c.commit()


def add_diamond(uid: int, n: int):
    with _LOCK:
        c = get_conn()
        c.execute("UPDATE players SET diamond=COALESCE(diamond,0)+? WHERE user_id=?", (n, uid))
        c.commit()


def add_item(uid: int, key: str, qty: int = 1):
    with _LOCK:
        c = get_conn()
        c.execute(
            """INSERT INTO inventory (user_id, item_key, quantity) VALUES (?,?,?)
                 ON CONFLICT(user_id, item_key) DO UPDATE SET quantity=quantity+?""",
            (uid, key, qty, qty),
        )
        c.commit()


def get_inv(uid: int) -> List[dict]:
    with _LOCK:
        c = get_conn()
        rows = c.execute("SELECT * FROM inventory WHERE user_id=? AND quantity>0", (uid,)).fetchall()
        return [dict(r) for r in rows]


def use_item(uid: int, key: str) -> bool:
    with _LOCK:
        c = get_conn()
        r = c.execute(
            "SELECT quantity FROM inventory WHERE user_id=? AND item_key=?",
            (uid, key),
        ).fetchone()
        if not r or r["quantity"] <= 0:
            return False
        c.execute(
            "UPDATE inventory SET quantity=quantity-1 WHERE user_id=? AND item_key=?",
            (uid, key),
        )
        c.commit()
        return True


def update_streak(uid: int) -> int:
    with _LOCK:
        c = get_conn()
        p = c.execute("SELECT streak, last_streak FROM players WHERE user_id=?", (uid,)).fetchone()
        if not p:
            return 0
        today = date.today().isoformat()
        if p["last_streak"] == today:
            return p["streak"] or 0
        try:
            yesterday = (date.today() - __import__("datetime").timedelta(days=1)).isoformat()
        except Exception:
            yesterday = ""
        new_streak = (p["streak"] + 1) if (p["last_streak"] == yesterday or not p["last_streak"]) else 1
        c.execute(
            "UPDATE players SET streak=?, last_streak=? WHERE user_id=?",
            (new_streak, today, uid),
        )
        c.commit()
        return new_streak


def active_users() -> List[int]:
    with _LOCK:
        c = get_conn()
        rows = c.execute("SELECT user_id FROM players WHERE onboard_step='done'").fetchall()
        return [r["user_id"] for r in rows]


def is_discovered(uid: int, key: str) -> bool:
    with _LOCK:
        c = get_conn()
        row = c.execute(
            "SELECT 1 FROM discoveries WHERE user_id=? AND discovery_key=?",
            (uid, key),
        ).fetchone()
        return row is not None


def discover(uid: int, key: str, dtype: str) -> bool:
    """Mark discovery. Returns True if first time."""
    with _LOCK:
        c = get_conn()
        try:
            c.execute(
                "INSERT INTO discoveries(user_id, discovery_key, discovery_type) VALUES(?,?,?)",
                (uid, key, dtype),
            )
            c.commit()
            return True
        except Exception:
            return False
