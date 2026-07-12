"""Telegram handlers — friends list, achievements, prestige, wiki."""

import logging
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from modules.config import PRESTIGE_MIN_LEVEL
from modules.data import ITEMS, tr, iname, BLESSINGS, WEEKLY_CONTRACTS
from modules.db import (
    goc, get_player, upd, add_item, add_diamond, get_conn, get_inv, active_users,
)
from modules.combat import pvp_fight, auto_equip
from modules.adventure import tick, maybe_daily_report, activate_blessing, do_prestige
from modules.talk import process_talk, hero_reply
from modules.temple import temple_text, temple_build, temple_donate, temple_info
from modules.ui import (
    kb, shop_kb, hero_card, welcome, ranking_text,
    shop_page, bless_page, friends_page, achievements_page, friend_ach_page,
    prestige_page, wiki_menu, wiki_page,
)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    p = goc(u.id, u.username or "", u.full_name or "Hero")
    step = p.get("onboard_step") or "lang"

    if step == "lang" or not p.get("lang"):
        await update.message.reply_text(
            tr("id", "choose_lang"),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🇮🇩 Indonesia", callback_data="lang_id"),
                InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
            ]]),
        )
        return
    if step == "deity" or not p.get("deity_name"):
        await update.message.reply_text(tr(p.get("lang") or "id", "ask_deity"), parse_mode="Markdown")
        upd(u.id, onboard_step="deity")
        return
    if step == "hero":
        await update.message.reply_text(tr(p.get("lang") or "id", "ask_hero"), parse_mode="Markdown")
        return

    if not p.get("contract_key"):
        import random
        ctr = random.choice(WEEKLY_CONTRACTS)
        upd(u.id, contract_key=ctr["key"], contract_progress=0)

    await update.message.reply_text(
        welcome(p, False), parse_mode="Markdown", reply_markup=kb(p.get("lang") or "id"),
    )


async def on_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    data = q.data
    p = goc(uid, q.from_user.username or "", q.from_user.full_name or "Hero")
    lang = p.get("lang") or "id"

    # Language
    if data.startswith("lang_"):
        lng = data.split("_", 1)[1]
        if p.get("onboard_step") == "done":
            upd(uid, lang=lng)
            await q.edit_message_text("✅")
            await q.message.reply_text(
                welcome(get_player(uid), False), parse_mode="Markdown", reply_markup=kb(lng)
            )
            return
        upd(uid, lang=lng, onboard_step="deity")
        await q.edit_message_text(tr(lng, "ask_deity"), parse_mode="Markdown")
        return

    # Shop buy flat
    if data.startswith("buyd_"):
        key = data[5:]
        it = ITEMS.get(key)
        if not it or not it.get("shop_only") or it.get("price_diamond", 0) <= 0:
            return
        if (p.get("diamond") or 0) < it["price_diamond"]:
            await q.answer(tr(lang, "not_enough_d"), show_alert=True)
            return
        add_diamond(uid, -it["price_diamond"])
        add_item(uid, key, 1)
        note = auto_equip(uid, key)
        msg = tr(lang, "bought", item=iname(key, lang))
        if note:
            msg += f" · {note}"
        await q.answer(msg[:180], show_alert=True)
        p = get_player(uid)
        await q.edit_message_text(
            tr(lang, "shop_title", diamond=p.get("diamond", 0)),
            parse_mode="Markdown",
            reply_markup=shop_kb(lang),
        )
        return

    # Shop browse next/back/pick
    if data.startswith("shop_nav_"):
        try:
            idx = int(data.split("_")[2])
        except Exception:
            idx = 0
        text, markup = shop_page(lang, idx)
        await q.edit_message_text(text, parse_mode="Markdown", reply_markup=markup)
        return

    if data.startswith("shop_pick_"):
        try:
            idx = int(data.split("_")[2])
        except Exception:
            return
        items = [(k, v) for k, v in ITEMS.items() if v.get("shop_only") and v.get("price_diamond", 0) > 0]
        if not items or idx < 0 or idx >= len(items):
            return
        key, it = items[idx]
        if (p.get("diamond") or 0) < it["price_diamond"]:
            await q.answer(tr(lang, "not_enough_d"), show_alert=True)
            return
        add_diamond(uid, -it["price_diamond"])
        add_item(uid, key, 1)
        note = auto_equip(uid, key)
        msg = tr(lang, "bought", item=iname(key, lang))
        if note:
            msg += f" · {note}"
        await q.answer(msg[:180], show_alert=True)
        text, markup = shop_page(lang, idx)
        await q.edit_message_text(text, parse_mode="Markdown", reply_markup=markup)
        return

    # Blessing browse
    if data.startswith("bless_nav_"):
        try:
            idx = int(data.split("_")[2])
        except Exception:
            idx = 0
        text, markup = bless_page(lang, idx)
        await q.edit_message_text(text, parse_mode="Markdown", reply_markup=markup)
        return

    if data.startswith("bless_pick_"):
        try:
            idx = int(data.split("_")[2])
        except Exception:
            return
        if idx < 0 or idx >= len(BLESSINGS):
            return
        bk = BLESSINGS[idx]["key"]
        msg = activate_blessing(uid, bk)
        await q.answer(msg or "OK", show_alert=True)
        text, markup = bless_page(lang, idx)
        result = f"\n\n✅ {msg}" if msg else ""
        try:
            await q.edit_message_text(text + result, parse_mode="Markdown", reply_markup=markup)
        except Exception:
            pass
        return

    if data.startswith("bless_") and not data.startswith("bless_nav_") and not data.startswith("bless_pick_"):
        bk = data[6:]
        msg = activate_blessing(uid, bk)
        await q.answer(msg or "OK", show_alert=True)
        try:
            await q.edit_message_text(
                f"{msg}\n\n{hero_card(get_player(uid))}",
                parse_mode="Markdown",
            )
        except Exception:
            pass
        return

    # Friends browse
    if data.startswith("friend_nav_"):
        try:
            idx = int(data.split("_")[2])
        except Exception:
            idx = 0
        text, markup = friends_page(uid, lang, idx)
        await q.edit_message_text(text, parse_mode="Markdown", reply_markup=markup)
        return

    # Friend achievements (list view, idx ignored)
    if data.startswith("friend_ach_"):
        parts = data.split("_")
        try:
            fid = int(parts[2])
        except Exception:
            return
        text, markup = friend_ach_page(uid, fid, lang)
        await q.edit_message_text(text, parse_mode="Markdown", reply_markup=markup)
        return

    # Own achievements (list view)
    if data == "menu_ach":
        text, markup = achievements_page(uid, lang)
        await q.edit_message_text(text, parse_mode="Markdown", reply_markup=markup)
        return

    # Prestige
    if data == "menu_prestige" or data == "prestige_go":
        if data == "prestige_go":
            msg = do_prestige(uid)
            await q.answer((msg or "OK")[:180], show_alert=True)
            p = get_player(uid)
            await q.message.reply_text(
                welcome(p, False), parse_mode="Markdown", reply_markup=kb(lang)
            )
            return
        text, markup = prestige_page(uid, lang)
        await q.edit_message_text(text, parse_mode="Markdown", reply_markup=markup)
        return

    if data == "menu_ach":
        text, markup = achievements_page(uid, lang, 0)
        await q.edit_message_text(text, parse_mode="Markdown", reply_markup=markup)
        return

    # Wiki
    if data == "menu_wiki":
        text, markup = wiki_menu(lang)
        await q.edit_message_text(text, parse_mode="Markdown", reply_markup=markup)
        return

    if data.startswith("wiki_"):
        # wiki_{cat}_{index}
        parts = data.split("_")
        if len(parts) < 3:
            return
        cat = parts[1]
        try:
            idx = int(parts[2])
        except Exception:
            idx = 0
        text, markup = wiki_page(cat, lang, idx)
        await q.edit_message_text(text, parse_mode="Markdown", reply_markup=markup)
        return

    # Friend accept
    if data.startswith("fr_accept_"):
        fid = int(data.split("_")[2])
        c = get_conn()
        c.execute("UPDATE friends SET status='accepted' WHERE user_id=? AND friend_id=?", (uid, fid))
        c.execute("INSERT OR IGNORE INTO friends(user_id,friend_id,status) VALUES(?,?,'accepted')", (fid, uid))
        c.execute("UPDATE friends SET status='accepted' WHERE user_id=? AND friend_id=?", (fid, uid))
        c.commit()
        c.close()
        await q.answer("✅")
        return

    # Auto duel — multi-step narrative (same as road duel)
    if data.startswith("pvp_auto_"):
        import json
        from modules.combat import pvp_duel_story
        tid = int(data.split("_")[2])
        if p.get("duel_foe_id"):
            await q.answer(
                "Masih duel!" if lang == "id" else "Already dueling!",
                show_alert=True,
            )
            return
        foe = get_player(tid)
        if not foe:
            await q.answer("?", show_alert=True)
            return
        w, l, steps = pvp_duel_story(uid, tid, lang)
        if not steps:
            await q.answer("Gagal" if lang == "id" else "Failed", show_alert=True)
            return
        payload = json.dumps({
            "steps": steps, "winner": w, "loser": l,
            "foe": tid, "foe_name": foe.get("name") or "?",
        })
        upd(uid, duel_foe_id=tid, duel_step=0, duel_payload=payload)
        await q.answer("Duel!" if lang == "id" else "Duel!", show_alert=False)
        await q.message.reply_text(steps[0], parse_mode="Markdown", reply_markup=kb(lang))
        # foe gets tease that duel started
        try:
            foe_lang = foe.get("lang") or "id"
            tease = (
                f"⚔️ *{p.get('name') or 'Hero'}* nantangin duel di jalan…\n_Hasilnya nanti._"
                if foe_lang == "id"
                else f"⚔️ *{p.get('name') or 'Hero'}* started a road duel…\n_Results soon._"
            )
            await context.bot.send_message(
                tid, tease, parse_mode="Markdown",
                reply_markup=kb(foe_lang),
            )
        except Exception:
            pass
        return

    if data.startswith("pvp_ok_"):
        # accepted challenge → start multi-step duel for accepter
        import json
        from modules.combat import pvp_duel_story
        chal = int(data.split("_")[2])
        if p.get("duel_foe_id"):
            await q.answer("Masih duel!" if lang == "id" else "Already dueling!", show_alert=True)
            return
        challenger = get_player(chal)
        if not challenger:
            await q.answer("?", show_alert=True)
            return
        w, l, steps = pvp_duel_story(uid, chal, lang)
        if not steps:
            await q.answer("Gagal" if lang == "id" else "Failed", show_alert=True)
            return
        payload = json.dumps({
            "steps": steps, "winner": w, "loser": l,
            "foe": chal, "foe_name": challenger.get("name") or "?",
        })
        upd(uid, duel_foe_id=chal, duel_step=0, duel_payload=payload)
        c = get_conn()
        c.execute(
            "UPDATE pvp_duels SET status='accepted' WHERE challenger_id=? AND target_id=? AND status='pending'",
            (chal, uid),
        )
        c.commit()
        c.close()
        await q.answer("Duel!" if lang == "id" else "Duel!")
        await q.message.reply_text(steps[0], parse_mode="Markdown", reply_markup=kb(lang))
        try:
            await context.bot.send_message(
                chal,
                f"⚔️ *{p.get('name') or 'Hero'}* nerima duel!\n_Lihat diary…_"
                if (challenger.get("lang") or "id") == "id"
                else f"⚔️ *{p.get('name') or 'Hero'}* accepted!\n_Check diary…_",
                parse_mode="Markdown",
            )
        except Exception:
            pass
        return

    if data.startswith("pvp_no_"):
        chal = int(data.split("_")[2])
        c = get_conn()
        c.execute(
            "UPDATE pvp_duels SET status='declined' WHERE challenger_id=? AND target_id=? AND status='pending'",
            (chal, uid),
        )
        c.commit()
        c.close()
        await q.answer("OK")
        return

    if data == "back" or data == "menu":
        try:
            await q.edit_message_text(
                welcome(get_player(uid), False),
                parse_mode="Markdown",
            )
        except Exception:
            pass
        return

    # Temple actions
    if data in ("temple_build", "temple_donate", "temple_close"):
        if data == "temple_build":
            text_t = temple_build(uid, lang)
        elif data == "temple_donate":
            text_t = temple_donate(uid, lang)
        else:
            text_t = temple_text(uid, lang)
        # rebuild inline menu
        p2 = get_player(uid)
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        rows = []
        if not p2.get("temple_built"):
            if p2.get("gold", 0) >= 1000:
                rows.append([InlineKeyboardButton(
                    "🛠 Bangun Candi (💰1000)" if lang == "id" else "🛠 Build (💰1000)",
                    callback_data="temple_build",
                )])
        else:
            if p2.get("gold", 0) >= 500:
                rows.append([InlineKeyboardButton(
                    "🙏 Sumbang gold" if lang == "id" else "🙏 Donate gold",
                    callback_data="temple_donate",
                )])
        rows.append([InlineKeyboardButton("🔙 Tutup" if lang == "id" else "🔙 Close", callback_data="temple_close")])
        try:
            await q.edit_message_text(text_t, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(rows))
        except Exception:
            await q.answer(_("done" if lang == "id" else "done"), show_alert=False)
        return


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.text:
        return
    text = msg.text.strip()
    u = update.effective_user
    uid = u.id
    p = goc(uid, u.username or "", u.full_name or "Hero")
    lang = p.get("lang") or "id"
    step = p.get("onboard_step") or "lang"

    if step == "lang" or not p.get("lang"):
        await msg.reply_text(
            tr("id", "choose_lang"),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🇮🇩 Indonesia", callback_data="lang_id"),
                InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
            ]]),
        )
        return

    if step == "deity" or (not p.get("deity_name") and step != "done"):
        name = text[:32]
        upd(uid, deity_name=name, onboard_step="hero")
        await msg.reply_text(tr(lang, "saved_deity", name=name), parse_mode="Markdown")
        return

    if step == "hero":
        import random
        name = text[:32]
        ctr = random.choice(WEEKLY_CONTRACTS)
        upd(
            uid, name=name, onboard_step="done", adventuring=1, zone="plains",
            contract_key=ctr["key"], contract_progress=0,
            contract_day=datetime.now().isocalendar()[1],
        )
        p = get_player(uid)
        await msg.reply_text(welcome(p, True), parse_mode="Markdown", reply_markup=kb(lang))
        return

    # Buttons
    if text in (tr(lang, "btn_hero"), "🦸 Hero", "Hero"):
        await msg.reply_text(hero_card(p), parse_mode="Markdown", reply_markup=kb(lang))
        return

    if text in (tr(lang, "btn_diary"), "📖 Diary", "Diary"):
        d = p.get("diary") or tr(lang, "diary_empty")
        await msg.reply_text(
            f"📖 *Diary*\n━━━━━━━━━━━━━━\n{d}",
            parse_mode="Markdown", reply_markup=kb(lang),
        )
        return

    if text in (tr(lang, "btn_inv"), "🎒 Inventory", "Inventory"):
        inv = get_inv(uid)
        if not inv:
            await msg.reply_text(tr(lang, "inv_empty"), reply_markup=kb(lang))
            return
        lines = ["🎒 *Inventory*", "━━━━━━━━━━━━━━"]
        for it in inv:
            lines.append(f"• {iname(it['item_key'], lang)} ×{it['quantity']}")
        lines.append("\n_Equip & potion otomatis._" if lang == "id" else "\n_Auto equip & potions._")
        await msg.reply_text("\n".join(lines), parse_mode="Markdown", reply_markup=kb(lang))
        return

    if text in (tr(lang, "btn_shop"), "💎 Shop", "Shop"):
        text_s, markup = shop_page(lang, 0)
        await msg.reply_text(text_s, parse_mode="Markdown", reply_markup=markup)
        return

    if text in (tr(lang, "btn_rank"), "🏆 Ranking", "Ranking"):
        await msg.reply_text(ranking_text(uid, lang), parse_mode="Markdown", reply_markup=kb(lang))
        return

    if text in (tr(lang, "btn_bless"), "🙏 Blessing", "Blessing"):
        text_b, markup = bless_page(lang, 0)
        await msg.reply_text(text_b, parse_mode="Markdown", reply_markup=markup)
        return

    if text in (tr(lang, "btn_friends"), "👥 Teman", "👥 Friends", "Friends"):
        text_f, markup = friends_page(uid, lang, 0)
        await msg.reply_text(text_f, parse_mode="Markdown", reply_markup=markup)
        return

    if text in (tr(lang, "btn_ach"), "🏅 Achievements", "Achievements"):
        text_a, markup = achievements_page(uid, lang, 0)
        await msg.reply_text(text_a, parse_mode="Markdown", reply_markup=markup)
        return

    if text in (tr(lang, "btn_prestige"), "⭐ Prestige", "Prestige"):
        text_p, markup = prestige_page(uid, lang)
        await msg.reply_text(text_p, parse_mode="Markdown", reply_markup=markup)
        return

    if text in (tr(lang, "btn_wiki"), "📚 Wiki", "Wiki"):
        text_w, markup = wiki_menu(lang)
        await msg.reply_text(text_w, parse_mode="Markdown", reply_markup=markup)
        return

    if text in (tr(lang, "btn_temple"), "🏛️ Candi", "🏛️ Temple", "Temple"):
        text_t, markup = temple_menu(uid, lang)
        await msg.reply_text(text_t, parse_mode="Markdown", reply_markup=markup)
        return

    if text in (tr(lang, "btn_lang"), "🌐 Bahasa", "🌐 Language", "Language"):
        await msg.reply_text(
            tr(lang, "choose_lang"),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🇮🇩 Indonesia", callback_data="lang_id"),
                InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
            ]]),
        )
        return

    # Talk to hero
    if text in (tr(lang, "btn_talk"), "💬 Ngobrol", "💬 Talk", "Talk"):
        context.user_data["await_talk"] = True
        await msg.reply_text(
            tr(lang, "talk_intro"),
            parse_mode="Markdown",
            reply_markup=kb(lang),
        )
        return

    if context.user_data.get("await_talk"):
        context.user_data["await_talk"] = False
        if text.lower() in ("batal", "cancel", "exit", "keluar"):
            await msg.reply_text(
                "Ngobrol selesai." if lang == "id" else "Chat ended.",
                reply_markup=kb(lang),
            )
            return
        out = process_talk(uid, text, lang)
        await msg.reply_text(
            out,
            parse_mode="Markdown",
            reply_markup=kb(lang),
        )
        return

    await msg.reply_text(tr(lang, "unknown"), reply_markup=kb(lang))


async def adventure_job(context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    for uid in active_users():
        try:
            daily = maybe_daily_report(uid)
            if daily:
                p = get_player(uid)
                lang = (p.get("lang") or "id") if p else "id"
                await bot.send_message(
                    chat_id=uid, text=daily, parse_mode="Markdown",
                    reply_markup=kb(lang),
                )
                continue
            line = tick(uid)
            if not line:
                continue
            p = get_player(uid)
            lang = (p.get("lang") or "id") if p else "id"
            await _send_discovery_pixels(bot, uid, p or {})
            await bot.send_message(
                chat_id=uid, text=line, parse_mode="Markdown",
                reply_markup=kb(lang),
            )
        except Exception as e:
            logging.warning(f"tick {uid}: {e}")


async def _send_discovery_pixels(bot, uid: int, p: dict):
    """Send pixel art for any new discoveries this tick (one image per event)."""
    from modules.image_gen import generate_image, caption_for
    from modules.data import iname, zname
    lang = p.get("lang") or "id"
    c = get_conn()
    rows = c.execute(
        """SELECT discovery_key, discovery_type, discovered_at FROM discoveries
           WHERE user_id=? AND discovered_at > datetime('now', '-3 minutes')
           ORDER BY discovered_at ASC LIMIT 6""",
        (uid,),
    ).fetchall()
    seen = set()
    fresh = []
    for row in rows:
        sig = (row["discovery_type"], row["discovery_key"])
        if sig in seen:
            continue
        seen.add(sig)
        fresh.append(row)
    c.close()

    for row in fresh:
        key = row["discovery_key"]
        dtype = row["discovery_type"]
        # pretty name
        if dtype == "monster":
            from modules.data import MONSTERS
            nm = (MONSTERS.get(key, {}).get("name") or {}).get(lang) \
                or (MONSTERS.get(key, {}).get("name") or {}).get("id") or key
        elif dtype == "boss":
            from modules.data import MONSTERS
            nm = (MONSTERS.get(key, {}).get("name") or {}).get(lang) or key
        elif dtype == "pet":
            nm = iname(key, lang)
        elif dtype == "item":
            nm = iname(key, lang)
        elif dtype == "zone":
            nm = zname(key, lang)
        elif dtype == "sidejob":
            from modules.data import SIDEJOBS
            job = SIDEJOBS.get(key, {})
            loc = job.get(lang) or job.get("id", {})
            nm = (loc or {}).get("title", key)
        elif dtype == "achievement":
            from modules.data import ACHIEVEMENTS
            av = ACHIEVEMENTS.get(key, {})
            nm = (av.get("name") or {}).get(lang) or (av.get("name") or {}).get("id") or key
        else:
            nm = key

        img = generate_image(key, dtype, nm)
        if img:
            caption = caption_for(dtype, nm, lang)
            try:
                await bot.send_photo(
                    chat_id=uid,
                    photo=img,
                    caption=caption,
                    parse_mode="Markdown",
                    reply_markup=kb(lang),
                )
            except Exception:
                pass


async def temple_menu(uid: int, lang: str) -> tuple:
    """Show temple status + action buttons (build/donate)."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    info = temple_info(uid, lang)
    rows = []
    p = get_player(uid)
    if not info or not info["built"]:
        text = temple_build(uid, lang)
        if p and p.get("gold", 0) >= 1000:
            rows.append([InlineKeyboardButton(
                "🛠 Bangun Candi (💰1000)" if lang == "id" else "🛠 Build Temple (💰1000)",
                callback_data="temple_build",
            )])
        rows.append([InlineKeyboardButton("▶️ Sumbang Lagi" if lang == "id" else "▶️ Donate More", callback_data="temple_donate")])
        rows.append([InlineKeyboardButton("🔙 Tutup" if lang == "id" else "🔙 Close", callback_data="temple_close")])
    else:
        text = temple_text(uid, lang)
        if p and p.get("gold", 0) >= 500:
            rows.append([InlineKeyboardButton(
                f"🙏 Sumbang gold" if lang == "id" else f"🙏 Donate gold",
                callback_data="temple_donate",
            )])
        rows.append([InlineKeyboardButton("🔙 Tutup" if lang == "id" else "🔙 Close", callback_data="temple_close")])
    return text, InlineKeyboardMarkup(rows)
