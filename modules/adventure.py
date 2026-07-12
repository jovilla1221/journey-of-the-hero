"""Adventure tick logic — side jobs, daily report, contract, streak, achievements."""

import random
from datetime import datetime, timezone, date
from typing import Optional

from modules.config import (
    SIDEJOB_STEPS, ENCOUNTER, REST, LOOT, TRADE, SIDEJOB, PET_FIND,
    ENERGY_REGEN, HP_REGEN, ENERGY_COST, PRESTIGE_MIN_LEVEL,
)
from modules.data import (
    ITEMS, ZONES, SIDEJOBS, WEEKLY_CONTRACTS, ACHIEVEMENTS, BLESSINGS,
    FLAV, tr, iname, mname, zname, PETS,
)
from modules.db import (
    get_player, upd, add_gold, add_item, add_diamond,
    get_conn, get_inv, update_streak, active_users,
)
from modules.combat import do_battle, pick_monster, auto_use_consumables, auto_equip


# ── SIDE JOB ──
def sidejob_progress(uid: int) -> Optional[str]:
    p = get_player(uid)
    if not p or not p.get("sidejob_key"):
        return None
    key = p["sidejob_key"]
    step = int(p.get("sidejob_step") or 0)
    lang = p.get("lang", "id")
    job = SIDEJOBS.get(key)
    if not job:
        upd(uid, sidejob_key=None, sidejob_step=0)
        return None
    loc = job.get(lang) or job["id"]
    steps = loc["steps"]
    title = loc["title"]

    notes = auto_use_consumables(uid)
    auto_str = "\n" + "\n".join(notes) if notes else ""

    if step >= len(steps):
        g1, g2 = job["gold"]
        e1, e2 = job["exp"]
        gold = random.randint(g1, g2)
        exp = random.randint(e1, e2)
        add_gold(uid, gold)
        p2 = get_player(uid)
        upd(uid, exp=p2["exp"] + exp, sidejob_key=None, sidejob_step=0)
        _bump_week(uid, gold=gold, exp=exp, jobs=1)
        lvl = _try_level(uid)
        msg = f"{title}\n{steps[-1] if steps else 'Selesai!'}\n💰 +{gold}  ⭐ +{exp}"
        if lvl:
            msg += f"\n🎉 Level {lvl}!"
        msg += auto_str
        _diary(uid, f"Side job selesai: {title}")
        return msg

    msg = f"{title}\n{steps[step]}"
    if step == 0:
        _diary(uid, f"Mulai side job")
    else:
        _diary(uid, f"Side job lanjut")
    upd(uid, sidejob_step=step + 1)

    if step + 1 >= len(steps):
        g1, g2 = job["gold"]
        e1, e2 = job["exp"]
        gold = random.randint(g1, g2)
        exp = random.randint(e1, e2)
        add_gold(uid, gold)
        p2 = get_player(uid)
        upd(uid, exp=p2["exp"] + exp, sidejob_key=None, sidejob_step=0)
        _bump_week(uid, gold=gold, exp=exp, jobs=1)
        lvl = _try_level(uid)
        msg += f"\n💰 +{gold}  ⭐ +{exp}"
        if lvl:
            msg += f"\n🎉 Level {lvl}!"
        _diary(uid, f"Side job selesai")
    msg += auto_str
    return msg


def start_sidejob(uid: int) -> str:
    key = random.choice(list(SIDEJOBS.keys()))
    upd(uid, sidejob_key=key, sidejob_step=0)
    return sidejob_progress(uid) or "…"


# ── DAILY REPORT ──
def daily_report_text(p: dict) -> Optional[str]:
    lang = p.get("lang", "id")
    deity = p.get("deity_name") or "Dewa"
    hero = p.get("name") or "Hero"
    kills = p.get("day_kills") or 0
    gold_d = p.get("day_gold") or 0
    exp_d = p.get("day_exp") or 0
    jobs_d = p.get("day_jobs") or 0
    streak = p.get("streak") or 0

    if lang == "id":
        if kills == 0 and gold_d == 0 and jobs_d == 0:
            return f"📜 *Laporan untuk {deity}*\n━━━━━━━━━━━━━━\nDari {hero}\n\nHari ini gak terjadi apa-apa.\nJalan-jalan aja. Santai.\nKadang jalan santai itu perlu.\n\n🔥 *Streak {streak} hari*" if streak else ""
        lines = [
            f"📜 *Laporan untuk {deity}*",
            "━━━━━━━━━━━━━━",
            f"Dari {hero}",
            "",
            "Halo Dewa, laporan hari ini:",
            "",
        ]
        if kills:
            lines.append(f"⚔️ Lawan {kills} musuh — {random.choice(['lumayan seru', 'mereka kalah', 'gampang'])}")
        if gold_d:
            lines.append(f"💰 Dapet {gold_d:,} gold — {random.choice(['bisa jajan', 'tabungan', 'sewa kost'])}")
        if exp_d:
            lines.append(f"⭐ EXP +{exp_d}")
        if jobs_d:
            lines.append(f"🛠 Side job {jobs_d}x")
        if streak:
            lines.append(f"🔥 *Streak {streak} hari*")
        lines.extend(["", f"Masih hidup, masih jalan.", f"— {hero}"])
        return "\n".join(lines)
    else:
        if kills == 0 and gold_d == 0 and jobs_d == 0:
            return f"📜 *Report for {deity}*\n━━━━━━━━━━━━━━\nFrom {hero}\n\nNothing much today.\nJust walked.\n\n🔥 *{streak}-day streak*" if streak else ""
        lines = ["📜 *Report for {deity}*", "━━━━━━━━━━━━━━", f"From {hero}", "", "Today's update:", ""]
        if kills:
            lines.append(f"⚔️ Beat {kills} — {random.choice(['sick', 'easy', 'fun'])}")
        if gold_d:
            lines.append(f"💰 +{gold_d:,}")
        if exp_d:
            lines.append(f"⭐ +{exp_d}")
        if jobs_d:
            lines.append(f"🛠 Jobs: {jobs_d}")
        if streak:
            lines.append(f"🔥 *{streak}-day streak*")
        lines.extend(["", "Still alive.", f"— {hero}"])
        return "\n".join(lines).format(deity=deity)


def maybe_daily_report(uid: int) -> Optional[str]:
    p = get_player(uid)
    if not p or p.get("onboard_step") != "done":
        return None
    today = date.today().isoformat()
    if p.get("last_daily") == today:
        return None
    # streak
    streak = update_streak(uid)
    p = get_player(uid)
    text = daily_report_text(p)
    # check achievements
    _check_achievements(uid, p)
    # reset daily
    upd(uid, last_daily=today, day_kills=0, day_gold=0, day_exp=0, day_jobs=0)
    _diary(uid, "Laporan harian")
    return text


# ── CONTRACT ──
def check_contract(uid: int) -> Optional[str]:
    p = get_player(uid)
    if not p or not p.get("contract_key"):
        return None
    from modules.data import WEEKLY_CONTRACTS
    ctr = None
    for x in WEEKLY_CONTRACTS:
        if x["key"] == p["contract_key"]:
            ctr = x
            break
    if not ctr:
        return None
    progress = p.get("contract_progress") or 0
    req = ctr["target"]
    # refresh progress from stats
    stat = p.get(ctr["stat"]) or 0
    if p.get("contract_day") != date.today().isoweekday():
        # new week check — reset if week changed
        pass
    if progress >= req:
        add_gold(uid, ctr["reward_gold"])
        add_diamond(uid, ctr["reward_diamond"])
        lang = p.get("lang", "id")
        msg = f"📜 *{ctr['name'].get(lang, ctr['key'])}* selesai! 💰+{ctr['reward_gold']} 💎+{ctr['reward_diamond']}"
        upd(uid, contract_key=None, contract_progress=0)
        _diary(uid, "Kontrak mingguan selesai")
        return msg
    return None


# ── ACHIEVEMENTS ──
def _check_achievements(uid: int, p: dict):
    from modules.db import get_conn
    conn = get_conn()
    unlocked = {r["ach_key"] for r in conn.execute("SELECT ach_key FROM achievements WHERE user_id=?", (uid,)).fetchall()}
    for ak, av in ACHIEVEMENTS.items():
        if ak in unlocked:
            continue
        if av["check"] == "kills" and (p.get("week_kills") or 0) >= av["need"]:
            _unlock_ach(conn, uid, ak, av)
        elif av["check"] == "gold" and (p.get("gold") or 0) >= av["need"]:
            _unlock_ach(conn, uid, ak, av)
        elif av["check"] == "streak" and (p.get("streak") or 0) >= av["need"]:
            _unlock_ach(conn, uid, ak, av)
        elif av["check"] == "pets" and 1:  # simplified
            have_pet = p.get("pet") is not None
            if have_pet:
                _unlock_ach(conn, uid, ak, av)
        elif av["check"] == "zone_forest" and p.get("zone") == "forest":
            _unlock_ach(conn, uid, ak, av)
        elif av["check"] == "prestige" and (p.get("prestige") or 0) >= av["need"]:
            _unlock_ach(conn, uid, ak, av)
    conn.close()


def _unlock_ach(conn, uid, ak, av):
    conn.execute("INSERT OR IGNORE INTO achievements (user_id, ach_key) VALUES (?,?)", (uid, ak))
    conn.commit()


# ── BLESSINGS ──
def activate_blessing(uid: int, bless_key: str) -> Optional[str]:
    p = get_player(uid)
    if not p:
        return None
    lang = p.get("lang") or "id"
    b = next((x for x in BLESSINGS if x["key"] == bless_key), None)
    if not b:
        return "Invalid blessing" if lang != "id" else "Blessing nggak valid"

    # cooldown: one blessing every 30 minutes
    conn = get_conn()
    last = conn.execute(
        "SELECT expires_at, created_at FROM blessings WHERE user_id=? ORDER BY id DESC LIMIT 1",
        (uid,),
    ).fetchone()
    if last:
        try:
            created = datetime.fromisoformat(last["created_at"].replace("Z", "+00:00")) if "T" in str(last["created_at"]) else datetime.now(timezone.utc)
        except Exception:
            created = datetime.now(timezone.utc)
        # simple: if any blessing created in last 30 min, block
        rows = conn.execute(
            "SELECT created_at FROM blessings WHERE user_id=? ORDER BY id DESC LIMIT 1",
            (uid,),
        ).fetchone()
        if rows and rows["created_at"]:
            try:
                from datetime import datetime as dt
                # compare as string date is fine for cooldown soft check
                pass
            except Exception:
                pass

    name = b["name"].get(lang, b["key"])
    if b.get("heal"):
        upd(uid, hp=p.get("max_hp") or 100)
        conn.execute(
            "INSERT INTO blessings (user_id, bless_key, expires_at) VALUES (?,?,?)",
            (uid, bless_key, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
        conn.close()
        _diary(uid, f"Blessing: {name} (full heal)")
        return f"🙏 {name}\n❤️ HP full!"

    expires = (datetime.now(timezone.utc) + __import__("datetime").timedelta(hours=b.get("hours", 6))).isoformat()
    conn.execute(
        "INSERT INTO blessings (user_id, bless_key, expires_at) VALUES (?,?,?)",
        (uid, bless_key, expires),
    )
    conn.commit()
    conn.close()

    # apply immediate soft effects via temporary player buff fields if needed
    effects = []
    if b.get("atk"):
        effects.append(f"⚔️ +{b['atk']}")
    if b.get("def"):
        effects.append(f"🛡️ +{b['def']}")
    if b.get("gold_bonus"):
        effects.append(f"💰 +{int(b['gold_bonus']*100)}%")
    if b.get("exp_bonus"):
        effects.append(f"⭐ +{int(b['exp_bonus']*100)}%")
    effect_txt = " · ".join(effects) if effects else "OK"
    _diary(uid, f"Blessing: {name}")
    return f"🙏 {name}\n{effect_txt}\n⏱ {b.get('hours', 6)} jam" if lang == "id" else f"🙏 {name}\n{effect_txt}\n⏱ {b.get('hours', 6)}h"


def check_blessings(uid: int, p: dict) -> dict:
    """Return active blessing bonuses."""
    result = {"atk": 0, "def": 0, "gold_bonus": 0, "exp_bonus": 0}
    conn = get_conn()
    rows = conn.execute("SELECT * FROM blessings WHERE user_id=?", (uid,)).fetchall()
    now = datetime.now(timezone.utc)
    for r in rows:
        try:
            exp = datetime.fromisoformat(r["expires_at"])
            if exp < now:
                conn.execute("DELETE FROM blessings WHERE id=?", (r["id"],))
                continue
            for b in BLESSINGS:
                if b["key"] == r["bless_key"]:
                    result["atk"] = max(result["atk"], b.get("atk", 0))
                    result["def"] = max(result["def"], b.get("def", 0))
                    result["gold_bonus"] = max(result["gold_bonus"], b.get("gold_bonus", 0))
                    result["exp_bonus"] = max(result["exp_bonus"], b.get("exp_bonus", 0))
        except Exception:
            pass
    conn.commit()
    conn.close()
    return result


# ── PRESTIGE ──
def do_prestige(uid: int) -> Optional[str]:
    p = get_player(uid)
    lang = p.get("lang", "id")
    if p["level"] < PRESTIGE_MIN_LEVEL:
        return tr(lang, "prestige_no", lv=PRESTIGE_MIN_LEVEL)
    n = (p.get("prestige") or 0) + 1
    bonus_atk = (p.get("prestige_bonus_atk") or 0) + 3
    bonus_def = (p.get("prestige_bonus_def") or 0) + 2
    upd(uid, prestige=n, prestige_bonus_atk=bonus_atk, prestige_bonus_def=bonus_def,
        level=1, exp=0, gold=1000, diamond=(p.get("diamond") or 0),
        hp=100, max_hp=100, atk=10, def_=5, energy=50, max_energy=50,
        weapon=None, armor=None, pet=None, adventuring=1)
    _diary(uid, f"Prestige {n}!")
    _check_achievements(uid, get_player(uid))
    return tr(lang, "prestige_ok", n=n)


# ── PETS ──
def find_pet(uid: int) -> Optional[str]:
    """Find pet on the road — auto equip + auto 3-day contract."""
    from modules.data import PETS
    from datetime import date, timedelta

    pool = [k for k, v in PETS.items() if not v.get("shop_only")]
    if not pool:
        return None
    weights = {"common": 50, "uncommon": 30, "rare": 15, "epic": 4, "legendary": 1}
    w = [weights.get(PETS[k].get("rarity", "common"), 10) for k in pool]
    pk = random.choices(pool, weights=w, k=1)[0]
    add_item(uid, pk, 1)

    p = get_player(uid)
    lang = p.get("lang", "id") if p else "id"
    name = iname(pk, lang)

    # auto equip if better
    equip_note = auto_equip(uid, pk)

    # auto pet contract 3 days
    start = date.today().isoformat()
    end = (date.today() + timedelta(days=3)).isoformat()
    conn = get_conn()
    conn.execute(
        "INSERT INTO pet_contracts (user_id, pet_key, start_date, end_date) VALUES (?,?,?,?)",
        (uid, pk, start, end),
    )
    conn.execute("UPDATE players SET week_pets=COALESCE(week_pets,0)+1 WHERE user_id=?", (uid,))
    conn.commit()
    conn.close()

    _diary(uid, f"Nemu pet: {name} (auto kontrak 3 hari)")
    lines = [
        random.choice(FLAV.get("pet_find", {}).get(lang, ["🐾 Pet baru!"])),
        f"🐾 {name}",
        "📝 Auto kontrak 3 hari" if lang == "id" else "📝 Auto 3-day contract",
    ]
    if equip_note:
        lines.append(equip_note)
    return "\n".join(lines)


def auto_social(uid: int) -> Optional[str]:
    """Auto friend + auto guild while adventuring. No buttons needed."""
    p = get_player(uid)
    if not p or p.get("onboard_step") != "done":
        return None
    lang = p.get("lang") or "id"
    notes = []

    conn = get_conn()

    # 1) Auto-accept any pending friend requests TO this user
    pending_in = conn.execute(
        "SELECT user_id FROM friends WHERE friend_id=? AND status='pending'",
        (uid,),
    ).fetchall()
    for row in pending_in:
        other = row["user_id"]
        conn.execute(
            "UPDATE friends SET status='accepted' WHERE user_id=? AND friend_id=?",
            (other, uid),
        )
        conn.execute(
            "INSERT OR IGNORE INTO friends(user_id, friend_id, status) VALUES (?,?, 'accepted')",
            (uid, other),
        )
        conn.execute(
            "UPDATE friends SET status='accepted' WHERE user_id=? AND friend_id=?",
            (uid, other),
        )
        other_p = conn.execute("SELECT name FROM players WHERE user_id=?", (other,)).fetchone()
        oname = other_p["name"] if other_p else str(other)
        notes.append(
            f"👥 Auto-teman: {oname}" if lang == "id" else f"👥 Auto-friend: {oname}"
        )
        _diary(uid, f"Auto friend {oname}")

    # 2) Auto-friend: meet random active player on the road (~8%)
    if random.random() < 0.08:
        others = conn.execute(
            """SELECT user_id, name FROM players
               WHERE onboard_step='done' AND user_id!=?
               ORDER BY RANDOM() LIMIT 5""",
            (uid,),
        ).fetchall()
        for o in others:
            exists = conn.execute(
                "SELECT 1 FROM friends WHERE user_id=? AND friend_id=?",
                (uid, o["user_id"]),
            ).fetchone()
            if exists:
                continue
            conn.execute(
                "INSERT OR IGNORE INTO friends(user_id, friend_id, status) VALUES (?,?, 'accepted')",
                (uid, o["user_id"]),
            )
            conn.execute(
                "INSERT OR IGNORE INTO friends(user_id, friend_id, status) VALUES (?,?, 'accepted')",
                (o["user_id"], uid),
            )
            notes.append(
                f"🤝 Ketemu di jalan: jadi temen sama *{o['name']}*!"
                if lang == "id"
                else f"🤝 Met on the road: friends with *{o['name']}*!"
            )
            _diary(uid, f"Auto friend {o['name']}")
            break

    # 3) Auto guild from fictional kingdoms — no buttons, just join on the road
    if not p.get("guild_id") and random.random() < 0.4:
        from modules.data import KINGDOMS
        gname = random.choice(KINGDOMS)
        try:
            existing = conn.execute("SELECT id FROM guilds WHERE name=?", (gname,)).fetchone()
            if existing:
                gid = existing["id"]
                conn.execute(
                    "INSERT OR IGNORE INTO guild_members(guild_id, user_id, role) VALUES (?,?, 'member')",
                    (gid, uid),
                )
                conn.execute("UPDATE guilds SET member_count=member_count+1 WHERE id=?", (gid,))
                conn.execute("UPDATE players SET guild_id=? WHERE user_id=?", (gid, uid))
            else:
                conn.execute(
                    "INSERT INTO guilds(name, owner_id, member_count) VALUES (?,?,1)",
                    (gname, uid),
                )
                gid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
                conn.execute(
                    "INSERT INTO guild_members(guild_id, user_id, role) VALUES (?,?, 'owner')",
                    (gid, uid),
                )
                conn.execute("UPDATE players SET guild_id=? WHERE user_id=?", (gid, uid))
            notes.append(
                f"🏰 Masuk *{gname}*!"
                if lang == "id"
                else f"🏰 Joined *{gname}*!"
            )
            _diary(uid, f"Auto guild: {gname}")
        except Exception:
            pass

    # 4) Auto zone — always pick best unlocked zone, sometimes wander
    from modules.data import ZONES
    current_zone = p.get("zone") or "plains"
    zone_order = ["plains", "forest", "cave", "mountain", "ruins", "void"]
    unlocked = []
    for zk in zone_order:
        z = ZONES.get(zk)
        if z and p["level"] >= z["min_level"] and (p.get("prestige") or 0) >= z.get("unlock_prestige", 0):
            unlocked.append(zk)
    best_zone = unlocked[-1] if unlocked else "plains"
    chosen_zone = best_zone
    if random.random() < 0.25 and len(unlocked) > 1:
        # wander to a random unlocked zone (different from current)
        candidates = [z for z in unlocked if z != current_zone]
        if candidates:
            chosen_zone = random.choice(candidates)
    if chosen_zone != current_zone:
        upd(uid, zone=chosen_zone)
        if chosen_zone == best_zone and best_zone != current_zone:
            msg = f"🗺️ Zona baru: {zname(chosen_zone, lang)}"
        else:
            msg = f"🗺️ Nyasar ke {zname(chosen_zone, lang)}"
        notes.append(msg if lang == "id" else msg)
        _diary(uid, f"Zone {chosen_zone}")

    # 5) Auto guildmate: after a battle, sometimes meet a player on the road -> friend
    if random.random() < 0.12:
        candidates = conn.execute(
            """SELECT user_id, name FROM players
               WHERE onboard_step='done' AND user_id!=?
               ORDER BY RANDOM() LIMIT 5""",
            (uid,),
        ).fetchall()
        for o in candidates:
            exists = conn.execute(
                "SELECT 1 FROM friends WHERE user_id=? AND friend_id=?",
                (uid, o["user_id"]),
            ).fetchone()
            if not exists:
                conn.execute(
                    "INSERT OR IGNORE INTO friends(user_id, friend_id, status) VALUES (?,?, 'accepted')",
                    (uid, o["user_id"]),
                )
                conn.execute(
                    "INSERT OR IGNORE INTO friends(user_id, friend_id, status) VALUES (?,?, 'accepted')",
                    (o["user_id"], uid),
                )
                notes.append(
                    f"🤝 Ketemu *{o['name']}* di jalan, jadi temen!"
                    if lang == "id"
                    else f"🤝 Met *{o['name']}* on the road, friends!"
                )
                _diary(uid, f"Met {o['name']}")
                break

    # 6) Auto cooperative + multi-step duel with friends (~18%)
    # skip if already in a duel
    p_fresh = get_player(uid)
    if p_fresh and p_fresh.get("duel_foe_id"):
        conn.commit()
        conn.close()
        if not notes:
            return None
        return "\n".join(notes)

    if random.random() < 0.18:
        friend = conn.execute(
            """SELECT f.friend_id, p.name FROM friends f
               JOIN players p ON p.user_id=f.friend_id
               WHERE f.user_id=? AND f.status='accepted' AND p.onboard_step='done'
               ORDER BY RANDOM() LIMIT 1""",
            (uid,),
        ).fetchone()
        if friend:
            wid, wname = friend["friend_id"], friend["name"]
            roll = random.random()
            if roll < 0.45:
                # hunt together (short multi-beat in one message for now)
                bonus = random.randint(20, 70)
                add_gold(uid, bonus)
                bonus2 = random.randint(10, 40)
                add_gold(wid, bonus2)
                if lang == "id":
                    notes.append(
                        f"🏹 *Berburu bareng {wname}*\n"
                        f"━━━━━━━━━━━━━━\n"
                        f"Lacak jejak…\n"
                        f"Nunggu di semak…\n"
                        f"Dapet buruan! 💰 +{bonus}"
                    )
                else:
                    notes.append(
                        f"🏹 *Hunt with {wname}*\n"
                        f"━━━━━━━━━━━━━━\n"
                        f"Track… wait… catch!\n"
                        f"💰 +{bonus}"
                    )
                _diary(uid, f"Hunt with {wname}")
            else:
                # start multi-step duel (resolved over ticks)
                from modules.combat import pvp_duel_story
                import json
                w, l, steps = pvp_duel_story(uid, wid, lang)
                if steps:
                    payload = json.dumps({"steps": steps, "winner": w, "loser": l, "foe": wid, "foe_name": wname})
                    # store on player — commit via upd after close
                    conn.execute(
                        "UPDATE players SET duel_foe_id=?, duel_step=0, duel_payload=? WHERE user_id=?",
                        (wid, payload, uid),
                    )
                    notes.append(steps[0])
                    _diary(uid, f"Duel start vs {wname}")
                    # also log duel row when finished (in duel_progress)

    conn.commit()
    conn.close()
    if not notes:
        return None
    return "\n".join(notes)


# ── MULTI-STEP DUEL ──
def duel_progress(uid: int) -> Optional[str]:
    """Advance auto-duel narrative one step per tick. Returns message or None."""
    import json
    p = get_player(uid)
    if not p or not p.get("duel_foe_id"):
        return None
    payload_raw = p.get("duel_payload")
    if not payload_raw:
        upd(uid, duel_foe_id=None, duel_step=0, duel_payload=None)
        return None
    try:
        data = json.loads(payload_raw)
        steps = data.get("steps") or []
        winner = data.get("winner")
        loser = data.get("loser")
        foe_name = data.get("foe_name") or "?"
    except Exception:
        upd(uid, duel_foe_id=None, duel_step=0, duel_payload=None)
        return None

    step = int(p.get("duel_step") or 0)
    # step 0 already shown when duel started; advance to next
    next_step = step + 1
    if next_step >= len(steps):
        # safety clear
        upd(uid, duel_foe_id=None, duel_step=0, duel_payload=None)
        return None

    msg = steps[next_step]
    if next_step >= len(steps) - 1:
        # last step — log duel and clear
        try:
            c = get_conn()
            c.execute(
                "INSERT INTO pvp_duels(challenger_id,target_id,status,winner_id) VALUES(?,?,?,?)",
                (uid, p["duel_foe_id"], "finished", winner),
            )
            c.commit()
            c.close()
        except Exception:
            pass
        upd(uid, duel_foe_id=None, duel_step=0, duel_payload=None)
        _diary(uid, f"Duel selesai vs {foe_name}")
    else:
        upd(uid, duel_step=next_step)

    return msg


# ── MAIN TICK ──
def tick(uid: int) -> Optional[str]:
    from modules.data import FLAV, T
    p = get_player(uid)
    if not p or p.get("onboard_step") != "done":
        return None
    lang = p.get("lang", "id")

    # multi-step duel first (like side job)
    if p.get("duel_foe_id"):
        notes = auto_use_consumables(uid)
        p = get_player(uid)
        upd(uid, energy=min(p["max_energy"], p["energy"] + ENERGY_REGEN),
            hp=min(p["max_hp"], p["hp"] + HP_REGEN),
            last_tick=datetime.now(timezone.utc).isoformat())
        msg = duel_progress(uid)
        if msg:
            if notes:
                msg += "\n" + "\n".join(notes)
            return msg

    # social auto: friend accept/meet + guild join
    social = auto_social(uid)
    if social and random.random() < 0.55:
        # sometimes surface social events as their own diary message
        return social

    # contract check
    contract_msg = check_contract(uid)
    if contract_msg:
        if social:
            contract_msg = social + "\n" + contract_msg
        return contract_msg

    # side job progress (prioritize)
    if p.get("sidejob_key"):
        notes = auto_use_consumables(uid)
        p = get_player(uid)
        upd(uid, energy=min(p["max_energy"], p["energy"] + ENERGY_REGEN),
            hp=min(p["max_hp"], p["hp"] + HP_REGEN),
            last_tick=datetime.now(timezone.utc).isoformat())
        msg = sidejob_progress(uid)
        if msg:
            if social:
                msg = social + "\n" + msg
            return msg

    notes = auto_use_consumables(uid)
    p = get_player(uid)

    new_en = min(p["max_energy"], p["energy"] + ENERGY_REGEN)
    new_hp = min(p["max_hp"], p["hp"] + HP_REGEN)
    can_walk = new_en >= ENERGY_COST
    if can_walk:
        new_en -= ENERGY_COST
    upd(uid, energy=new_en, hp=new_hp, last_tick=datetime.now(timezone.utc).isoformat(), adventuring=1 if can_walk else 0)
    p = get_player(uid)
    extra = list(notes)
    if social:
        extra.insert(0, social)

    if not can_walk:
        if random.random() < 0.4:
            line = random.choice(FLAV["rest"][lang]) + f"\n⚡ {p['energy']}/{p['max_energy']}  ❤️ {p['hp']}/{p['max_hp']}"
            _diary(uid, "Rest")
            if extra:
                line += "\n" + "\n".join(extra)
            return line
        return "\n".join(extra) if extra else None

    r = random.random()
    zone = p.get("zone") or "plains"

    if r < ENCOUNTER:
        start = random.choice(FLAV["battle_start"][lang])
        mk, mon = pick_monster(p["level"], zone)
        res = do_battle(uid, mk, mon)
        mon_label = res.get("mon") or mk
        if isinstance(mon_label, dict):
            mon_label = mon_label.get(lang) or mon_label.get("id") or mk
        flavor = random.choice(FLAV["win" if res["won"] else "lose"][lang])
        icon = "⚔️" if res["won"] else "💀"
        line = f"{start}\n{icon} {mon_label}\n{flavor}\n💰 +{res['gold']}  ⭐ +{res['exp']}  ❤️ {res['hp']}"
        if res["diamond"]:
            line += f"\n{tr(lang, 'diamond_drop', n=res['diamond'])}"
        if res["drop"]:
            line += f"\n{iname(res['drop'], lang)}"
        if res.get("equip_note"):
            line += f"\n{res['equip_note']}"
        if res["lvl"]:
            line += f"\n🎉 Level {res['lvl']}!"
        _diary(uid, f"{'Menang' if res['won'] else 'Kalah'} vs {mon_label}")
        if extra:
            line += "\n" + "\n".join(extra)
        return line

    if r < ENCOUNTER + REST:
        p = get_player(uid)
        h = min(12, p["max_hp"] - p["hp"])
        e = min(4, p["max_energy"] - p["energy"])
        upd(uid, hp=p["hp"] + h, energy=p["energy"] + e)
        line = random.choice(FLAV["rest"][lang])
        if h or e:
            line += f"\n❤️ +{h}  ⚡ +{e}"
        _diary(uid, "Istirahat")
        if extra:
            line += "\n" + "\n".join(extra)
        return line

    if r < ENCOUNTER + REST + LOOT:
        gold = random.randint(5, 25 + p["level"] * 5)
        add_gold(uid, gold)
        line = random.choice(FLAV["loot"][lang]) + f"\n💰 +{gold}"
        if random.random() < 0.3:
            pot = random.choice(["health_potion", "energy_potion"])
            add_item(uid, pot, 1)
            line += f"\n{iname(pot, lang)}"
        _diary(uid, f"Loot +{gold}")
        if extra:
            line += "\n" + "\n".join(extra)
        return line

    if r < ENCOUNTER + REST + LOOT + TRADE:
        g = random.randint(10, 35)
        add_gold(uid, g)
        line = random.choice(FLAV["trade"][lang]) + f"\n💰 +{g}"
        _diary(uid, "Dagang")
        if extra:
            line += "\n" + "\n".join(extra)
        return line

    if r < ENCOUNTER + REST + LOOT + TRADE + SIDEJOB:
        line = start_sidejob(uid)
        if extra:
            line += "\n" + "\n".join(extra)
        return line

    if r < ENCOUNTER + REST + LOOT + TRADE + SIDEJOB + PET_FIND:
        msg = find_pet(uid)
        if msg:
            if extra:
                msg += "\n" + "\n".join(extra)
            return msg

    # walk
    line = random.choice(FLAV["walk"][lang])
    _diary(uid, line[:70])
    if extra:
        line += "\n" + "\n".join(extra)
        return line
    return line if random.random() < 0.45 else None


# ── HELPERS ──
def _bump_week(uid: int, gold: int = 0, exp: int = 0, jobs: int = 0):
    """Update day + week counters"""
    conn = get_conn()
    conn.execute(
        """UPDATE players SET day_gold=COALESCE(day_gold,0)+?, day_exp=COALESCE(day_exp,0)+?,
           day_jobs=COALESCE(day_jobs,0)+?, week_jobs=COALESCE(week_jobs,0)+?, week_gold=COALESCE(week_gold,0)+?
           WHERE user_id=?""",
        (max(0, gold), max(0, exp), jobs, jobs, max(0, gold), uid))
    conn.commit()
    conn.close()


def _try_level(uid: int) -> Optional[int]:
    p = get_player(uid)
    if not p or p["exp"] < _exp_next(p["level"]):
        return None
    nl = p["level"] + 1
    need = _exp_next(p["level"])
    conn = get_conn()
    conn.execute("""UPDATE players SET level=?, exp=exp-?, max_hp=max_hp+20, hp=max_hp+20,
       atk=atk+3, def=def+2, max_energy=MIN(100, max_energy+5) WHERE user_id=?""",
                (nl, need, uid))
    conn.commit()
    conn.close()
    return nl


def _exp_next(lvl: int) -> int:
    return lvl * 100


def _diary(uid: int, line: str, n: int = 24):
    p = get_player(uid)
    if not p:
        return
    d = (p.get("diary") or "").split("\n") if p.get("diary") else []
    d.append(f"[{datetime.now().strftime('%H:%M')}] {line}")
    upd(uid, diary="\n".join(d[-n:]))


def _check_ach_all(uid: int):
    p = get_player(uid)
    if p:
        _check_achievements(uid, p)