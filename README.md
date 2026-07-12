# Journey of the Hero ⚔️

Telegram idle RPG bot. **Full auto** adventure + Godville-style diary.
Branding: **Journey of the Hero**, bukan Godville.

## Highlights

- 🗡️ **Auto adventure** — jalan, battle, rest, loot, trade tiap ~40 detik
- 🎮 **Multi-step side jobs** (3–5 step naratif per job)
- ⚔️ **Multi-step PvP duel** (4 tahap: tantang → clash → balas → hasil)
- 🐾 **Pet drop + auto 3-day contract**
- 🏰 **Auto guild** dari 20 kerajaan fiksi (Auroria, Imperium Thalor, …)
- 🤝 **Auto friends** — ketemu random player di jalan, auto jadi temen
- 🗺️ **6 zona** (Plains → Void) auto unlock + wander
- 💎 **Diamond** dari musuh sulit (Troll, Naga, Slime Raja, dll)
- 🙏 **Blessing** — 5 jenis (ATK/DEF/Gold/EXP/Heal)
- ⭐ **Prestige** di Lv 20+ (bonus permanen)
- 🏅 **Achievements** — cuma yang sudah didapet, list
- 📚 **Wiki** — paragraf penjelasan 8 kategori
- 🎨 **Pixel art** first-time discovery (PNG sprite per monster/item/pet)
- 🇮🇩🇬🇧 **Bahasa ID/EN** penuh

## Stack

- Python 3.11+
- `python-telegram-bot` 22.x dengan `job-queue`
- SQLite lokal
- Pillow untuk pixel art
- Full **modular**: `modules/{config,data,db,combat,adventure,ui,handlers}.py`

## Setup

```bash
git clone https://github.com/aonagiworks/journey-of-the-hero
cd journey-of-the-hero
python3 -m venv venv
source venv/bin/activate
pip install "python-telegram-bot[job-queue]" Pillow
```

## Run

```bash
export BOT_TOKEN="token_dari_botfather"
./venv/bin/python3 main.py
```

## Deploy (systemd opsional)

Lihat `journey-of-the-hero.service` — ubah path dan token, lalu:
```bash
sudo cp journey-of-the-hero.service /etc/systemd/system/
sudo systemctl enable --now journey-of-the-hero
```

## File Structure

```
main.py                  # entry tipis (Application builder + handlers + tick job)
modules/
  config.py             # constants, BOT_TOKEN (env)
  data.py               # items, monsters, zones, sidejobs, pets, i18n, flavor
  db.py                 # SQLite + migrations + discoveries + lock
  combat.py             # battle, auto-equip, auto-potion, multi-step duel
  adventure.py          # tick engine, sidejob, duel_progress, blessing
  ui.py                 # keyboard, hero card, friends, achievements, prestige, wiki, pixel sprite gateway
  handlers.py           # telegram callbacks + text + adventure_job (auto tick)
pixel_art.py            # PIL-based sprite generator + cache
.pixel_cache/           # generated PNGs/GIFs (gitignored)
```

## Bahasa ID/EN

Semua teks lewat `tr(lang, key, **kw)`. Tambah bahasa = tambah baris di `modules/data.py` `TXT`.

## Gameplay

- Hero jalan sendiri. Pemain cuma pantau diary.
- Diamond = currency langka. Drop dari musuh sulit. Shop premium pakai diamond.
- Tiap tick: encounter / rest / loot / trade / sidejob / pet find + auto equip/potion.
- Tiap beberapa tick: guild auto join, friend auto-meet, foo bareng atau duel random di jalan.
- Lv 20+: bisa prestige via menu.
- Wiki = 8 kategori paragraf (👹 Musuh, 🗡️ Item, 🐾 Pet, 🗺️ Zona, 🛠 Side Job, 🙏 Blessing, 📜 Kontrak, ⭐ Prestige).

---

Made with ❤️ for Telegram idle RPG fans.
