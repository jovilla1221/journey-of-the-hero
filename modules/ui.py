"""UI helpers — keyboard, friends, achievements, prestige, wiki."""

from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

from modules.config import GAME_NAME, PRESTIGE_MIN_LEVEL
from modules.data import (
    ITEMS, MONSTERS, ZONES, SIDEJOBS, ACHIEVEMENTS, BLESSINGS,
    WEEKLY_CONTRACTS, PETS, tr, iname, zname, T,
)
from modules.combat import stats
from modules.db import get_conn


def kb(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton(tr(lang, "btn_hero")), KeyboardButton(tr(lang, "btn_diary"))],
            [KeyboardButton(tr(lang, "btn_inv")), KeyboardButton(tr(lang, "btn_shop"))],
            [KeyboardButton(tr(lang, "btn_friends")), KeyboardButton(tr(lang, "btn_ach"))],
            [KeyboardButton(tr(lang, "btn_rank")), KeyboardButton(tr(lang, "btn_wiki"))],
            [KeyboardButton(tr(lang, "btn_bless")), KeyboardButton(tr(lang, "btn_prestige"))],
            [KeyboardButton(tr(lang, "btn_lang"))],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


def nav_kb(prefix: str, index: int, total: int, lang: str, pick: bool = True) -> InlineKeyboardMarkup:
    rows = []
    mid = []
    if index > 0:
        mid.append(InlineKeyboardButton("◀️ Back", callback_data=f"{prefix}_nav_{index-1}"))
    if index < total - 1:
        mid.append(InlineKeyboardButton("Next ▶️", callback_data=f"{prefix}_nav_{index+1}"))
    if mid:
        rows.append(mid)
    if pick:
        rows.append([InlineKeyboardButton(
            "✅ Pilih" if lang == "id" else "✅ Select",
            callback_data=f"{prefix}_pick_{index}",
        )])
    return InlineKeyboardMarkup(rows)


def shop_items_list():
    return [(k, v) for k, v in ITEMS.items() if v.get("shop_only") and v.get("price_diamond", 0) > 0]


def shop_kb(lang: str) -> InlineKeyboardMarkup:
    rows = []
    for k, v in shop_items_list():
        rows.append([InlineKeyboardButton(
            f"{iname(k, lang)} — 💎{v['price_diamond']}",
            callback_data=f"buyd_{k}",
        )])
    return InlineKeyboardMarkup(rows or [[InlineKeyboardButton("—", callback_data="noop")]])


def shop_page(lang: str, index: int = 0):
    items = shop_items_list()
    if not items:
        return "Shop kosong.", InlineKeyboardMarkup([])
    index = max(0, min(index, len(items) - 1))
    key, it = items[index]
    text = (
        f"💎 *Shop* ({index+1}/{len(items)})\n"
        f"━━━━━━━━━━━━━━\n"
        f"{iname(key, lang)}\n"
        f"💎 {it['price_diamond']}\n\n"
        f"_Next/Back · Pilih untuk beli_"
        if lang == "id" else
        f"💎 *Shop* ({index+1}/{len(items)})\n"
        f"━━━━━━━━━━━━━━\n"
        f"{iname(key, lang)}\n"
        f"💎 {it['price_diamond']}\n\n"
        f"_Next/Back · Select to buy_"
    )
    return text, nav_kb("shop", index, len(items), lang, pick=True)


def bless_page(lang: str, index: int = 0):
    items = BLESSINGS
    index = max(0, min(index, len(items) - 1))
    b = items[index]
    name = (b.get("name") or {}).get(lang) or (b.get("name") or {}).get("id") or b["key"]
    if b.get("heal"):
        effect = "❤️ Full heal"
    else:
        parts = []
        if b.get("atk"):
            parts.append(f"⚔️ +{b['atk']}")
        if b.get("def"):
            parts.append(f"🛡️ +{b['def']}")
        if b.get("gold_bonus"):
            parts.append(f"💰 +{int(b['gold_bonus']*100)}%")
        if b.get("exp_bonus"):
            parts.append(f"⭐ +{int(b['exp_bonus']*100)}%")
        effect = " · ".join(parts) if parts else "—"
        effect += f"\n⏱ {b.get('hours', 6)}h"
    text = (
        f"🙏 *Blessing* ({index+1}/{len(items)})\n"
        f"━━━━━━━━━━━━━━\n"
        f"{name}\n{effect}\n\n"
        f"_Next/Back · Pilih untuk aktifkan_"
        if lang == "id" else
        f"🙏 *Blessing* ({index+1}/{len(items)})\n"
        f"━━━━━━━━━━━━━━\n"
        f"{name}\n{effect}\n\n"
        f"_Next/Back · Select to activate_"
    )
    return text, nav_kb("bless", index, len(items), lang, pick=True)


def friends_list(uid: int):
    c = get_conn()
    rows = c.execute(
        """SELECT f.friend_id, p.name, p.level, p.gold, p.diamond, p.streak, p.zone, p.prestige
           FROM friends f JOIN players p ON p.user_id=f.friend_id
           WHERE f.user_id=? AND f.status='accepted'
           ORDER BY p.level DESC""",
        (uid,),
    ).fetchall()
    c.close()
    return [dict(r) for r in rows]


def friends_page(uid: int, lang: str, index: int = 0):
    items = friends_list(uid)
    if not items:
        return tr(lang, "no_friends"), InlineKeyboardMarkup([])
    index = max(0, min(index, len(items) - 1))
    f = items[index]
    text = (
        f"👥 *Teman* ({index+1}/{len(items)})\n"
        f"━━━━━━━━━━━━━━\n"
        f"👤 *{f['name']}*\n"
        f"Lv {f['level']} · 💰 {f['gold']:,} · 💎 {f.get('diamond') or 0}\n"
        f"🔥 streak {f.get('streak') or 0}\n"
        f"🗺️ {zname(f.get('zone') or 'plains', lang)} · ⭐ prestige {f.get('prestige') or 0}"
    )
    rows = []
    mid = []
    if index > 0:
        mid.append(InlineKeyboardButton("◀️ Back", callback_data=f"friend_nav_{index-1}"))
    if index < len(items) - 1:
        mid.append(InlineKeyboardButton("Next ▶️", callback_data=f"friend_nav_{index+1}"))
    if mid:
        rows.append(mid)
    rows.append([InlineKeyboardButton(
        "🏅 " + ("Lihat Achievements" if lang == "id" else "View Achievements"),
        callback_data=f"friend_ach_{f['friend_id']}_0",
    )])
    rows.append([InlineKeyboardButton(
        "⚔️ " + ("Duel" if lang == "id" else "Duel"),
        callback_data=f"pvp_auto_{f['friend_id']}",
    )])
    return text, InlineKeyboardMarkup(rows)


def achievements_page(uid: int, lang: str, index: int = 0, owner_name: str = None):
    """List of unlocked achievements only (no locked ones, no pagination)."""
    c = get_conn()
    rows = c.execute(
        "SELECT ach_key FROM achievements WHERE user_id=? ORDER BY id",
        (uid,),
    ).fetchall()
    c.close()
    unlocked = [r["ach_key"] for r in rows]
    total = len(ACHIEVEMENTS)
    who = f" · {owner_name}" if owner_name else ""
    header = f"🏅 *Achievements*{who}\n━━━━━━━━━━━━━━\n{len(unlocked)}/{total}"
    if not unlocked:
        empty = (
            "Belum ada. Main terus, achievement turun sendiri!"
            if lang == "id"
            else "Nothing yet. Keep playing — achievements drop on their own!"
        )
        return f"{header}\n\n_{empty}_", InlineKeyboardMarkup([])
    lines = [header, ""]
    for k in unlocked:
        av = ACHIEVEMENTS.get(k, {})
        nm = (av.get("name") or {}).get(lang) or (av.get("name") or {}).get("id") or k
        ds = (av.get("desc") or {}).get(lang) or (av.get("desc") or {}).get("id") or ""
        rw = av.get("reward_diamond", 0)
        lines.append(f"✅ *{nm}* — {ds}  💎+{rw}")
    return "\n".join(lines), InlineKeyboardMarkup([])


def friend_ach_page(viewer_uid: int, friend_id: int, lang: str, index: int = 0):
    """Friend's unlocked achievements as a list."""
    c = get_conn()
    rows = c.execute(
        "SELECT ach_key FROM achievements WHERE user_id=? ORDER BY id",
        (friend_id,),
    ).fetchall()
    friend = c.execute("SELECT name FROM players WHERE user_id=?", (friend_id,)).fetchone()
    c.close()
    fname = friend["name"] if friend else str(friend_id)
    unlocked = [r["ach_key"] for r in rows]
    total = len(ACHIEVEMENTS)
    header = f"🏅 *{fname}* — Achievements\n━━━━━━━━━━━━━━\n{len(unlocked)}/{total}"
    if not unlocked:
        empty = "Belum ada achievement." if lang == "id" else "No achievements yet."
        text = f"{header}\n\n_{empty}_"
    else:
        lines = [header, ""]
        for k in unlocked:
            av = ACHIEVEMENTS.get(k, {})
            nm = (av.get("name") or {}).get(lang) or (av.get("name") or {}).get("id") or k
            ds = (av.get("desc") or {}).get(lang) or (av.get("desc") or {}).get("id") or ""
            rw = av.get("reward_diamond", 0)
            lines.append(f"✅ *{nm}* — {ds}  💎+{rw}")
        text = "\n".join(lines)
    return text, InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Teman" if lang == "id" else "🔙 Friends", callback_data="friend_nav_0")]
    ])


def prestige_page(uid: int, lang: str):
    c = get_conn()
    row = c.execute("SELECT * FROM players WHERE user_id=?", (uid,)).fetchone()
    c.close()
    if not row:
        return "—", InlineKeyboardMarkup([])
    p = dict(row)
    level = p.get("level", 1)
    prest = p.get("prestige") or 0
    batk = p.get("prestige_bonus_atk") or 0
    bdef = p.get("prestige_bonus_def") or 0
    text = tr(lang, "prestige_info", level=level, prestige=prest, batk=batk, bdef=bdef, need=PRESTIGE_MIN_LEVEL)
    rows = []
    if level >= PRESTIGE_MIN_LEVEL:
        rows.append([InlineKeyboardButton(tr(lang, "btn_prestige_go"), callback_data="prestige_go")])
    rows.append([InlineKeyboardButton(tr(lang, "btn_ach"), callback_data="menu_ach")])
    return text, InlineKeyboardMarkup(rows)


def hero_card(p: dict) -> str:
    lang = p.get("lang") or "id"
    atk, df = stats(p)
    w = iname(p["weapon"], lang) if p.get("weapon") else "—"
    a = iname(p["armor"], lang) if p.get("armor") else "—"
    pet = iname(p["pet"], lang) if p.get("pet") else "—"
    deity = p.get("deity_name") or "—"
    zone = zname(p.get("zone") or "plains", lang)
    streak = p.get("streak") or 0
    prestige = p.get("prestige") or 0

    guild_line = ""
    if p.get("guild_id"):
        c = get_conn()
        g = c.execute("SELECT name FROM guilds WHERE id=?", (p["guild_id"],)).fetchone()
        c.close()
        if g:
            guild_line = f"\n🏰 {g['name']}"

    sj = ""
    if p.get("sidejob_key"):
        job = SIDEJOBS.get(p["sidejob_key"], {})
        loc = job.get(lang) or job.get("id", {})
        title = loc.get("title", p["sidejob_key"]) if isinstance(loc, dict) else p["sidejob_key"]
        step = int(p.get("sidejob_step") or 0)
        total = len(loc.get("steps", [])) if isinstance(loc, dict) else 5
        sj = f"\n🛠 {title} ({min(step+1, total)}/{total})"

    status = "🟢 di jalan" if p.get("adventuring") else ("🟡 istirahat" if lang == "id" else "🟡 resting")
    prest_line = f"\n⭐ Prestige *{prestige}*" if prestige else ""
    return (
        f"*{GAME_NAME}*\n"
        f"━━━━━━━━━━━━━━\n"
        f"🦸 *{p['name']}*\n"
        f"⚡ Dewa: *{deity}*\n"
        f"🗺️ {zone}{guild_line}\n"
        f"{status}{sj}{prest_line}\n"
        f"🔥 Streak: *{streak}*\n"
        f"━━━━━━━━━━━━━━\n"
        f"❤️  `{p['hp']}/{p['max_hp']}`\n"
        f"⚔️  `{atk}`    🛡️  `{df}`\n"
        f"⚡  `{p['energy']}/{p['max_energy']}`\n"
        f"💰  `{p['gold']:,}`    💎  `{p.get('diamond', 0)}`\n"
        f"⭐  Lv *{p['level']}*  ·  EXP `{p['exp']}/{p['level']*100}`\n"
        f"━━━━━━━━━━━━━━\n"
        f"🗡️ {w}\n"
        f"🛡️ {a}\n"
        f"🐾 {pet}"
    )


def welcome(p: dict, first: bool) -> str:
    lang = p.get("lang") or "id"
    deity = p.get("deity_name") or "Dewa"
    hero = p.get("name") or "Hero"
    if first:
        if lang == "id":
            return (
                f"⚡ *Suatu dewa baru muncul di cakrawala…*\n\n"
                f"Nama-Mu: *{deity}*.\n"
                f"Pahlawan-Mu *{hero}* baru bangun di tepi jalan berdebu "
                f"dengan 1.000 gold, pedang imajiner, dan nol rencana.\n\n"
                f"📖 _\"…siapa yang manggil? Aku cuma mau tidur. "
                f"Oke. Aku bertarung. Jangan berharap banyak.\"_\n\n"
                f"🎁 *Bekal:* 💰1000 Gold | 💎0 Diamond | ❤️100 | ⚔️10 | 🛡️5 | ⚡50\n\n"
                f"*{hero}* udah melangkah sendiri.\n"
                f"Semua otomatis: lawan, loot, pet, temen, guild, zona.\n"
                f"Cek *🏅 Achievements*, *⭐ Prestige*, *📚 Wiki* di keyboard.\n\n"
                f"_Kamu dewa-nya. Santai aja._"
            )
        return (
            f"⚡ *A new deity appears…*\n\n"
            f"Your name: *{deity}*.\n"
            f"Hero *{hero}* woke up on a dusty road with 1,000 gold and zero plans.\n\n"
            f"📖 _\"…who called me? I just wanted sleep. Okay. I'll fight.\"_\n\n"
            f"🎁 *Starter:* 💰1000 | 💎0 | ❤️100 | ⚔️10 | 🛡️5 | ⚡50\n\n"
            f"*{hero}* is already walking.\n"
            f"Everything is automatic: fights, loot, pets, friends, guilds, zones.\n"
            f"Check *🏅 Achievements*, *⭐ Prestige*, *📚 Wiki* on the keyboard.\n\n"
            f"_You're the deity. Relax._"
        )
    return f"{hero_card(p)}\n\n" + (
        f"_Hai Dewa {deity}. {hero} masih di jalan._" if lang == "id"
        else f"_Hey Deity {deity}. {hero} is still on the road._"
    )


def ranking_text(uid: int, lang: str) -> str:
    c = get_conn()
    rows = c.execute(
        "SELECT user_id, name, level, gold, diamond, prestige FROM players "
        "WHERE onboard_step='done' ORDER BY prestige DESC, level DESC, gold DESC LIMIT 15"
    ).fetchall()
    c.close()
    medals = ["🥇", "🥈", "🥉"]
    lines = ["🏆 *Ranking*", "━━━━━━━━━━━━━━"]
    my_rank = None
    for i, r in enumerate(rows):
        m = medals[i] if i < 3 else f"{i+1}."
        prest = f" ⭐{r['prestige']}" if r["prestige"] else ""
        mark = ""
        if r["user_id"] == uid:
            my_rank = i + 1
            mark = "  ← kamu" if lang == "id" else "  ← you"
        lines.append(f"{m} *{r['name']}* · Lv.{r['level']}{prest} · 💰{r['gold']:,} · 💎{r['diamond'] or 0}{mark}")
    if my_rank is None:
        c = get_conn()
        allr = c.execute(
            "SELECT user_id FROM players WHERE onboard_step='done' "
            "ORDER BY prestige DESC, level DESC, gold DESC"
        ).fetchall()
        c.close()
        for i, r in enumerate(allr):
            if r["user_id"] == uid:
                my_rank = i + 1
                break
    if my_rank:
        lines.append("")
        lines.append(f"📍 Posisi kamu: *#{my_rank}*" if lang == "id" else f"📍 Your rank: *#{my_rank}*")
    return "\n".join(lines)


# ── WIKI ──
WIKI_KEYS = ["monsters", "items", "pets", "zones", "sidejobs", "blessings", "contracts", "prestige"]
WIKI_LABELS = {
    "id": ["👹 Musuh", "🗡️ Item", "🐾 Pet", "🗺️ Zona", "🛠 Side Job", "🙏 Blessing", "📜 Kontrak", "⭐ Prestige"],
    "en": ["👹 Monsters", "🗡️ Items", "🐾 Pets", "🗺️ Zones", "🛠 Side Jobs", "🙏 Blessings", "📜 Contracts", "⭐ Prestige"],
}


def wiki_menu(lang: str) -> tuple:
    labels = WIKI_LABELS.get(lang) or WIKI_LABELS["id"]
    text = tr(lang, "wiki_header") + "\n━━━━━━━━━━━━━━\n" + (
        "Pilih kategori:" if lang == "id" else "Pick a category:"
    )
    rows = []
    for i in range(0, len(labels), 2):
        row = []
        for j, label in enumerate(labels[i:i + 2]):
            key = WIKI_KEYS[i + j]
            row.append(InlineKeyboardButton(label, callback_data=f"wiki_{key}_0"))
        rows.append(row)
    return text, InlineKeyboardMarkup(rows)


def wiki_page(cat: str, lang: str, index: int = 0) -> tuple:
    if cat == "monsters":
        keys = list(MONSTERS.keys())
        if not keys:
            return "—", InlineKeyboardMarkup([])
        index = max(0, min(index, len(keys) - 1))
        k = keys[index]
        m = MONSTERS[k]
        nm = (m.get("name") or {}).get(lang) or (m.get("name") or {}).get("id") or k
        hard = ("musuh sulit" if m.get("hard") else "musuh biasa") if lang == "id" else ("hard foe" if m.get("hard") else "common foe")
        if lang == "id":
            para = (
                f"👹 *{nm}*\n━━━━━━━━━━━━━━\n"
                f"{hard} yang muncul di {zname(m.get('zone') or 'plains', lang)} mulai level {m['min_level']}. "
                f"HP {m['hp']}, ATK {m['atk']}, DEF {m['def']}. "
                f"Kalau menang dapet ⭐{m['exp']} EXP, 💰{m['gold']} gold."
            )
            if m.get("diamond_chance"):
                para += f"\n\n_punya *{int(m['diamond_chance']*100)}%* jebol 💎!_"
        else:
            para = (
                f"👹 *{nm}*\n━━━━━━━━━━━━━━\n"
                f"A {hard} found in {zname(m.get('zone') or 'plains', lang)} at Lv {m['min_level']}+. "
                f"HP {m['hp']}, ATK {m['atk']}, DEF {m['def']}. "
                f"Rewards ⭐{m['exp']} EXP, 💰{m['gold']} gold."
            )
            if m.get("diamond_chance"):
                para += f"\n\n_{int(m['diamond_chance']*100)}% diamond chance!_"
        return para, _wiki_nav("monsters", index, len(keys))

    if cat == "items":
        keys = list(ITEMS.keys())
        index = max(0, min(index, len(keys) - 1))
        k = keys[index]
        it = ITEMS[k]
        nm = iname(k, lang)
        parts = []
        if it.get("atk"):
            parts.append(f"⚔️+{it['atk']}")
        if it.get("def"):
            parts.append(f"🛡️+{it['def']}")
        if it.get("heal"):
            parts.append(f"❤️+{it['heal']}")
        if it.get("energy"):
            parts.append(f"⚡+{it['energy']}")
        if it.get("gold_bonus"):
            parts.append(f"💰+{int(it['gold_bonus']*100)}%")
        if it.get("exp_bonus"):
            parts.append(f"⭐+{int(it['exp_bonus']*100)}%")
        bonus_txt = ", ".join(parts) if parts else "—"
        if it.get("shop_only"):
            src = "cuma bisa dibeli di Shop (💎" + str(it.get("price_diamond")) + ")" if lang == "id" else "shop-only (💎" + str(it.get("price_diamond")) + ")"
        else:
            src = "dapet dari jalan, loot, battle" if lang == "id" else "found on the road, loot, battle"
        if lang == "id":
            para = (
                f"🗡️ *{nm}* ({index+1}/{len(keys)})\n━━━━━━━━━━━━━━\n"
                f"Tipe *{it.get('type', '—')}*. Bonus: {bonus_txt}.\n\n"
                f"Asal: {src}."
            )
        else:
            para = (
                f"🗡️ *{nm}* ({index+1}/{len(keys)})\n━━━━━━━━━━━━━━\n"
                f"Type *{it.get('type', '—')}*. Bonus: {bonus_txt}.\n\n"
                f"Source: {src}."
            )
        return para, _wiki_nav("items", index, len(keys))

    if cat == "pets":
        keys = list(PETS.keys())
        index = max(0, min(index, len(keys) - 1))
        k = keys[index]
        pet = PETS[k]
        nm = iname(k, lang)
        rar = pet.get("rarity", "common")
        parts = []
        if pet.get("atk"):
            parts.append(f"⚔️+{pet['atk']}")
        if pet.get("gold_bonus"):
            parts.append(f"💰+{int(pet['gold_bonus']*100)}%")
        if pet.get("exp_bonus"):
            parts.append(f"⭐+{int(pet['exp_bonus']*100)}%")
        bonus_txt = ", ".join(parts) if parts else "—"
        if pet.get("shop_only"):
            src = "cuma di shop" if lang == "id" else "shop-only"
        else:
            src = "ketemu di jalan + kontrak otomatis 3 hari" if lang == "id" else "found on road + auto 3-day contract"
        if lang == "id":
            para = (
                f"🐾 *{nm}* ({index+1}/{len(keys)})\n━━━━━━━━━━━━━━\n"
                f"Pet rarity *{rar}*. Bonus: {bonus_txt}.\n\n"
                f"Dapet: {src}.\n\n"
                f"_Auto equip + auto kontrak 3 hari waktu dijalan._"
            )
        else:
            para = (
                f"🐾 *{nm}* ({index+1}/{len(keys)})\n━━━━━━━━━━━━━━\n"
                f"Pet rarity *{rar}*. Bonus: {bonus_txt}.\n\n"
                f"Acquired: {src}.\n\n"
                f"_Auto equipped + auto 3-day contract on the road._"
            )
        return para, _wiki_nav("pets", index, len(keys))

    if cat == "zones":
        keys = list(ZONES.keys())
        index = max(0, min(index, len(keys) - 1))
        zk = keys[index]
        z = ZONES[zk]
        nm = zname(zk, lang)
        if lang == "id":
            para = (
                f"🗺️ *{nm}*\n━━━━━━━━━━━━━━\n"
                f"Zona yang kebuka dari level {z['min_level']} dengan prestige minimal {z.get('unlock_prestige', 0)}. "
                f"Musuh di {nm} makin kuat makin dalem."
                f"\n\n_Hero ganti zona otomatis naik level, kadang nyasar random._"
            )
        else:
            para = (
                f"🗺️ *{nm}*\n━━━━━━━━━━━━━━\n"
                f"Zone unlocked at level {z['min_level']}, prestige {z.get('unlock_prestige', 0)}. "
                f"Enemies get tougher the deeper you go."
                f"\n\n_Hero auto-switches zones as levels progress, sometimes wanders randomly._"
            )
        return para, _wiki_nav("zones", index, len(keys))

    if cat == "sidejobs":
        keys = list(SIDEJOBS.keys())
        index = max(0, min(index, len(keys) - 1))
        k = keys[index]
        job = SIDEJOBS[k]
        loc = job.get(lang) or job.get("id", {})
        title = loc.get("title", k) if isinstance(loc, dict) else k
        steps = loc.get("steps", []) if isinstance(loc, dict) else []
        g1, g2 = job.get("gold", (0, 0))
        e1, e2 = job.get("exp", (0, 0))
        if lang == "id":
            para = (
                f"🛠 *{title}* ({index+1}/{len(keys)})\n━━━━━━━━━━━━━━\n"
                f"Side job {len(steps)} langkah. "
                f"💰 {g1}-{g2} · ⭐ {e1}-{e2}.\n\n"
                f"Langkah:\n" + "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps))
            )
        else:
            para = (
                f"🛠 *{title}* ({index+1}/{len(keys)})\n━━━━━━━━━━━━━━\n"
                f"Side job with {len(steps)} steps. "
                f"💰 {g1}-{g2} · ⭐ {e1}-{e2}.\n\n"
                f"Steps:\n" + "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps))
            )
        return para, _wiki_nav("sidejobs", index, len(keys))

    if cat == "blessings":
        items = BLESSINGS
        index = max(0, min(index, len(items) - 1))
        b = items[index]
        name = (b.get("name") or {}).get(lang) or (b.get("name") or {}).get("id") or b["key"]
        if b.get("heal"):
            eff = "❤️ Full heal langsung" if lang == "id" else "❤️ Instant full heal"
        else:
            parts = []
            if b.get("atk"):
                parts.append(f"⚔️+{b['atk']}")
            if b.get("def"):
                parts.append(f"🛡️+{b['def']}")
            if b.get("gold_bonus"):
                parts.append(f"💰+{int(b['gold_bonus']*100)}%")
            if b.get("exp_bonus"):
                parts.append(f"⭐+{int(b['exp_bonus']*100)}%")
            eff = " · ".join(parts) if parts else "—" if lang == "id" else (" · ".join(parts) if parts else "—")
            eff += f" ⏱ {b.get('hours', 6)}h"
        if lang == "id":
            para = (
                f"🙏 *{name}*\n━━━━━━━━━━━━━━\n"
                f"Berkah dari dewa. Efek: {eff}.\n\n"
                f"_Pencet tombol Blessing, pilih salah satu → langsung aktif!_\n"
                f"Cooldown tiap pake ~15 menit."
            )
        else:
            para = (
                f"🙏 *{name}*\n━━━━━━━━━━━━━━\n"
                f"Blessing from your deity. Effect: {eff}.\n\n"
                f"_Hit Blessing button, pick one → activates immediately!_\n"
                f"Cooldown ~15 min per use."
            )
        return para, _wiki_nav("blessings", index, len(items))

    if cat == "contracts":
        items = WEEKLY_CONTRACTS
        index = max(0, min(index, len(items) - 1))
        c = items[index]
        name = (c.get("name") or {}).get(lang) or (c.get("name") or {}).get("id") or c.get("key", "?")
        if lang == "id":
            para = (
                f"📜 *{name}*\n━━━━━━━━━━━━━━\n"
                f"Mingguan: capai target *{c['target']}*." if c.get("target") else ""
                f"Hadiah: 💰{c['reward_gold']} + 💎{c['reward_diamond']}.\n\n"
                f"_Kontrak baru tiap minggu. Dicek otomatis waktu perjalanan._"
            )
        else:
            para = (
                f"📜 *{name}*\n━━━━━━━━━━━━━━\n"
                f"Weekly: reach target *{c['target']}*." if c.get("target") else ""
                f"Reward: 💰{c['reward_gold']} + 💎{c['reward_diamond']}.\n\n"
                f"_New contract every week. Auto-checked while adventuring._"
            )
        return para, _wiki_nav("contracts", index, len(items))

    if cat == "prestige":
        if lang == "id":
            para = (
                "⭐ *Prestige*\n━━━━━━━━━━━━━━\n"
                "Begitu hero mencapai level 20+, dewa bisa mutusin buat prestige. "
                "Hero di-reset ke level 1, tapi dapet bonus ATK +3 DEF +2 permanen "
                "tiap prestige. Diamond, achievement, temen, dan guild aman. "
                "Zona Void juga makin gampang dibuka.\n\n"
                "_Kamu dewa, kamu yang mutusin kapan waktunya prestige._"
            )
        else:
            para = (
                "⭐ *Prestige*\n━━━━━━━━━━━━━━\n"
                "When your hero reaches level 20+, you can prestige. "
                "Hero resets to level 1 but gets permanent +3 ATK, +2 DEF per prestige. "
                "Diamonds, achievements, friends, guilds carry over. "
                "Void zone becomes easier to unlock.\n\n"
                "_You're the deity — you decide when it's time._"
            )
        return para, InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Wiki", callback_data="menu_wiki")]])

    return "—", InlineKeyboardMarkup([])


def _wiki_nav(cat: str, index: int, total: int) -> InlineKeyboardMarkup:
    rows = []
    mid = []
    if index > 0:
        mid.append(InlineKeyboardButton("◀️", callback_data=f"wiki_{cat}_{index-1}"))
    if index < total - 1:
        mid.append(InlineKeyboardButton("▶️", callback_data=f"wiki_{cat}_{index+1}"))
    if mid:
        rows.append(mid)
    rows.append([InlineKeyboardButton("🔙 Wiki", callback_data="menu_wiki")])
    return InlineKeyboardMarkup(rows)
