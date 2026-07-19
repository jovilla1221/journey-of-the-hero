"""Combat logic."""

import random
from datetime import datetime, timezone
from typing import Tuple, Optional

from modules.data import ITEMS, MONSTERS
from modules.db import get_player, upd, add_gold, add_diamond, add_item, get_conn, get_inv, use_item


def stats(p: dict) -> Tuple[int, int]:
    atk, df = p["atk"], p["def"]
    atk += (p.get("prestige_bonus_atk") or 0)
    df += (p.get("prestige_bonus_def") or 0)
    if p.get("weapon") in ITEMS:
        atk += ITEMS[p["weapon"]].get("atk", 0)
    if p.get("armor") in ITEMS:
        df += ITEMS[p["armor"]].get("def", 0)
    # pet atk bonus
    if p.get("pet") in ITEMS:
        atk += ITEMS[p["pet"]].get("atk", 0)
    return atk, df


def gear_score(key: str) -> int:
    it = ITEMS.get(key, {})
    return it.get("atk", 0) + it.get("def", 0) + int(it.get("gold_bonus", 0) * 100) + it.get("exp_bonus", 0) * 10


def auto_equip(uid: int, key: str) -> Optional[str]:
    it = ITEMS.get(key)
    if not it:
        return None
    field = {"weapon": "weapon", "armor": "armor", "pet": "pet"}.get(it["type"])
    if not field:
        return None
    p = get_player(uid)
    cur = p.get(field)
    if cur and gear_score(cur) >= gear_score(key):
        return None
    upd(uid, **{field: key})
    return f"🔧 Auto-equip: {it['name'].get(p.get('lang','id'), key)}"


def auto_use_consumables(uid: int) -> list:
    notes = []
    p = get_player(uid)
    if not p:
        return notes
    lang = p.get("lang", "id")
    inv = {i["item_key"]: i["quantity"] for i in get_inv(uid)}

    # ── HP low: eat food or drink potion ──
    if p["hp"] < p["max_hp"] * 0.35:
        # priority: best heal → potion
        for key, heal in [("fish", 55), ("meat", 40), ("bread", 15),
                          ("big_potion", 80), ("health_potion", 30)]:
            if inv.get(key, 0) > 0 and use_item(uid, key):
                p = get_player(uid)
                upd(uid, hp=min(p["max_hp"], p["hp"] + heal))
                notes.append(f"🍽️ {ITEMS[key]['name'].get(lang, key)} (+{heal} HP)")
                break

    # ── Energy low: drink ──
    p = get_player(uid)
    if p and p["energy"] < p["max_energy"] * 0.25:
        inv = {i["item_key"]: i["quantity"] for i in get_inv(uid)}
        for key, energy in [("ale", 45), ("milk", 30), ("water", 15),
                            ("energy_refill", 50), ("energy_potion", 25)]:
            if inv.get(key, 0) > 0 and use_item(uid, key):
                p = get_player(uid)
                upd(uid, energy=min(p["max_energy"], p["energy"] + energy))
                notes.append(f"🥤 {ITEMS[key]['name'].get(lang, key)} (+{energy} ⚡)")
                break

    # ── Auto-restock basic supplies (if gold allows) ──
    p = get_player(uid)
    if p and p.get("gold", 0) >= 200:
        inv = {i["item_key"]: i["quantity"] for i in get_inv(uid)}
        targets = {"bread": 3, "water": 3, "health_potion": 2, "energy_potion": 2}
        restocked = []
        for key, want in targets.items():
            have = inv.get(key, 0)
            if have < want and key in ITEMS:
                need = want - have
                price = ITEMS[key].get("price_gold", 0)
                total = price * need
                if p.get("gold", 0) >= total:
                    add_item(uid, key, need)
                    upd(uid, gold=p["gold"] - total)
                    restocked.append(f"{ITEMS[key]['name'].get(lang, key)} ×{need}")
                    p["gold"] -= total
        if restocked:
            notes.append(f"🛒 Auto-beli: {', '.join(restocked)}")

    return notes


def pick_monster(level: int, zone: str) -> Tuple[str, dict]:
    elig = [(k, m) for k, m in MONSTERS.items() if m["min_level"] <= level and m.get("zone") == zone]
    if not elig:
        elig = [(k, m) for k, m in MONSTERS.items() if m["min_level"] <= level]
    w = [max(1, 12 - abs(level - m["min_level"])) for _, m in elig]
    k, m = random.choices(elig, weights=w, k=1)[0]
    return k, dict(m)


def do_battle(uid: int, mkey: str, mon: dict) -> dict:
    p = get_player(uid)
    lang = p.get("lang") or "id"
    atk, df = stats(p)
    # bonuses from items
    gm = 1.0
    if p.get("pet") in ITEMS:
        gm += ITEMS[p["pet"]].get("gold_bonus", 0)
    em = 1.0
    if p.get("buff_exp_until"):
        try:
            from datetime import datetime, timezone
            if datetime.fromisoformat(p["buff_exp_until"]) > datetime.now(timezone.utc):
                em = 2.0
        except Exception:
            pass
    if p.get("pet") in ITEMS:
        em += ITEMS[p["pet"]].get("exp_bonus", 0)

    php, mhp = p["hp"], mon["hp"]
    while php > 0 and mhp > 0:
        mhp -= max(1, atk - mon["def"] // 2 + random.randint(-2, 2))
        if mhp <= 0:
            break
        php -= max(1, mon["atk"] - df // 2 + random.randint(-2, 2))

    won = mhp <= 0
    exp_g = int(mon["exp"] * em) if won else max(1, mon["exp"] // 5)
    gold_g = int(mon["gold"] * gm) if won else 0
    dia = 0
    if won and mon.get("hard") and random.random() < mon.get("diamond_chance", 0):
        dia = 1 if mon["min_level"] < 8 else random.randint(1, 2)
        if mon["min_level"] >= 12:
            dia = random.randint(1, 3)

    new_hp = max(1, php) if won else max(1, p["hp"] // 4)
    upd(uid, hp=new_hp, exp=p["exp"] + exp_g, gold=p["gold"] + gold_g)
    if dia:
        add_diamond(uid, dia)
    # update week counters
    c = get_conn()
    c.execute(
        "UPDATE players SET week_kills=COALESCE(week_kills,0)+1, day_kills=COALESCE(day_kills,0)+1, day_gold=COALESCE(day_gold,0)+?, day_exp=COALESCE(day_exp,0)+? WHERE user_id=?",
        (gold_g, exp_g, uid),
    )
    if mon.get("hard"):
        c.execute("UPDATE players SET week_hard=COALESCE(week_hard,0)+1 WHERE user_id=?", (uid,))
    c.commit()
    c.close()

    # → Personality: battle event
    try:
        from modules.personality import apply_event
        event = "hard_kill" if mon.get("hard") else "win"
        pe = apply_event(p, event)
        if pe:
            udb = get_conn()
            for k, v in pe.items():
                udb.execute(f"UPDATE players SET {k}=? WHERE user_id=?", (v, uid))
            udb.commit()
            udb.close()
    except Exception:
        pass

    # → Personality: lose event (hero defeated)
    if not won:
        try:
            from modules.personality import apply_event
            pe = apply_event(p, "lose")
            if pe:
                udb = get_conn()
                for k, v in pe.items():
                    udb.execute(f"UPDATE players SET {k}=? WHERE user_id=?", (v, uid))
                udb.commit()
                udb.close()
        except Exception:
            pass

    lvl = _try_level(uid) if won else None

    # log battle
    c2 = get_conn()
    c2.execute(
        "INSERT INTO battles (user_id, monster, result, exp_gained, gold_earned, diamond_earned, zone) VALUES (?,?,?,?,?,?,?)",
        (uid, mkey, "win" if won else "lose", exp_g, gold_g, dia, p.get("zone")),
    )
    c2.commit()
    c2.close()

    drop = equip_note = None
    new_item = new_pet = None
    if won and random.random() < 0.20:
        pool = [k for k, v in ITEMS.items() if v.get("drop")]
        if pool:
            weights = [3 if ITEMS[k]["type"] == "consumable" else 1 for k in pool]
            drop = random.choices(pool, weights=weights, k=1)[0]
            add_item(uid, drop, 1)
            if ITEMS[drop]["type"] in ("weapon", "armor", "pet"):
                equip_note = auto_equip(uid, drop)
            # discovery for item/pet
            try:
                from modules.db import discover
                if ITEMS[drop]["type"] == "pet":
                    new_pet = discover(uid, drop, "pet")
                else:
                    new_item = discover(uid, drop, "item")
            except Exception:
                pass

    # track monster discovery
    new_mon = None
    if won:
        try:
            from modules.db import discover
            dtype = "boss" if mon.get("hard") else "monster"
            new_mon = discover(uid, mkey, dtype)
        except Exception:
            pass

    mon_label = mon.get("name", mkey)
    if isinstance(mon_label, dict):
        mon_label = mon_label.get(lang) or mon_label.get("id") or mkey

    return {
        "won": won, "exp": exp_g, "gold": gold_g, "diamond": dia,
        "hp": new_hp, "lvl": lvl, "mon": mon_label, "mkey": mkey,
        "drop": drop, "equip_note": equip_note, "hard": mon.get("hard", False),
        "new_discovery": new_mon or new_item or new_pet,
        "discovery_key": mkey if new_mon else (drop if new_item or new_pet else None),
    }


def pvp_fight(a: int, b: int) -> Tuple[int, int]:
    pa, pb = get_player(a), get_player(b)
    if not pa or not pb:
        return (a, b)
    aa, da = stats(pa)
    ab, db = stats(pb)
    ha, hb = pa["hp"], pb["hp"]
    while ha > 0 and hb > 0:
        hb -= max(1, aa - db // 2 + random.randint(-2, 2))
        if hb <= 0:
            break
        ha -= max(1, ab - da // 2 + random.randint(-2, 2))
    return (a, b) if ha > 0 else (b, a)


# Flavor steps for auto-duel narrative (multi-step like side job)
DUEL_OPEN_ID = [
    "Ketemu *{foe}* di jalan. Tatapan saling tantang.",
    "*{foe}* lewat sambil cengengesan. \"Duel yuk.\"",
    "Di persimpangan, *{foe}* bilang: \"Coba lawan aku.\"",
    "Hero sama *{foe}* saling liat… udah jelas mau gelut.",
]
DUEL_OPEN_EN = [
    "Bumps into *{foe}* on the road. Staredown.",
    "*{foe}* grins. \"Duel?\"",
    "At a crossroad, *{foe}* says: \"Try me.\"",
    "Hero and *{foe}* lock eyes… fight time.",
]
DUEL_MID_ID = [
    "Serang duluan! Pedang beradu, debu beterbangan.",
    "Saling sikut. *{foe}* nyaris jatuh, tapi masih berdiri.",
    "Mundur selangkah, maju dua. Napas pendek.",
    "\"Aduh!\" — kena, tapi balas lagi. Masih imbang.",
    "Lompat ke samping, ayunan nyaris ngena. Ketegangan naik.",
]
DUEL_MID_EN = [
    "First strike! Blades clash, dust flies.",
    "Shoving. *{foe}* almost falls, still standing.",
    "Step back, two steps in. Short of breath.",
    "\"Ow!\" — hit, then hit back. Still even.",
    "Sidestep — swing almost lands. Tension rises.",
]
DUEL_END_WIN_ID = [
    "Akhirnya *{winner}* unggul. *{loser}* angkat tangan. \"Oke, lu menang.\"",
    "Pukulan penutup! *{winner}* menang. *{loser}* ketawa lelah. \"Rematch nanti.\"",
    "Habis. *{winner}* berdiri, *{loser}* duduk di debu. Tetep temenan.",
]
DUEL_END_WIN_EN = [
    "*{winner}* takes it. *{loser}* raises hands. \"Fine, you win.\"",
    "Finishing blow! *{winner}* wins. *{loser}* laughs, tired. \"Rematch later.\"",
    "Done. *{winner}* stands, *{loser}* sits in dust. Still friends.",
]


def pvp_duel_story(a: int, b: int, lang: str = "id") -> Tuple[int, int, list]:
    pa, pb = get_player(a), get_player(b)
    if not pa or not pb:
        return a, b, []
    an = pa.get("name") or "Hero"
    bn = pb.get("name") or "Rival"
    w, l = pvp_fight(a, b)
    wn = (get_player(w) or {}).get("name") or "?"
    ln = (get_player(l) or {}).get("name") or "?"

    if lang == "id":
        open_ = random.choice(DUEL_OPEN_ID).format(foe=bn)
        mid1 = random.choice(DUEL_MID_ID).format(foe=bn)
        mid2 = random.choice(DUEL_MID_ID).format(foe=bn)
        if mid2 == mid1:
            mid2 = random.choice(DUEL_MID_ID).format(foe=bn)
        end = random.choice(DUEL_END_WIN_ID).format(winner=wn, loser=ln)
        header = f"⚔️ *Duel vs {bn}*"
    else:
        open_ = random.choice(DUEL_OPEN_EN).format(foe=bn)
        mid1 = random.choice(DUEL_MID_EN).format(foe=bn)
        mid2 = random.choice(DUEL_MID_EN).format(foe=bn)
        if mid2 == mid1:
            mid2 = random.choice(DUEL_MID_EN).format(foe=bn)
        end = random.choice(DUEL_END_WIN_EN).format(winner=wn, loser=ln)
        header = f"⚔️ *Duel vs {bn}*"

    steps = [
        f"{header}\n━━━━━━━━━━━━━━\n{open_}",
        f"{header}\n━━━━━━━━━━━━━━\n{mid1}",
        f"{header}\n━━━━━━━━━━━━━━\n{mid2}",
        f"{header}\n━━━━━━━━━━━━━━\n{end}\n🏆 *{wn}* menang!",
    ]
    return w, l, steps


def _try_level(uid: int) -> Optional[int]:
    p = get_player(uid)
    if not p or p["exp"] < _exp_next(p["level"]):
        return None
    nl = p["level"] + 1
    need = _exp_next(p["level"])
    c = get_conn()
    c.execute(
        """UPDATE players SET level=?, exp=exp-?, max_hp=max_hp+20, hp=max_hp+20,
           atk=atk+3, def=def+2, max_energy=MIN(100, max_energy+5) WHERE user_id=?""",
        (nl, need, uid),
    )
    # level-up reward: diamond or auto blessing
    import random as _r
    if nl % 5 == 0:
        c.execute("UPDATE players SET diamond=diamond+1 WHERE user_id=?", (uid,))
        reward = "diamond"
    else:
        reward = "blessing"
    c.commit()
    c.close()
    if reward == "blessing":
        try:
            from modules.adventure import activate_blessing
            from modules.data import BLESSINGS
            bk = _r.choice(BLESSINGS)["key"]
            activate_blessing(uid, bk)
        except Exception:
            pass
    return nl


def _exp_next(lvl: int) -> int:
    return lvl * 100
