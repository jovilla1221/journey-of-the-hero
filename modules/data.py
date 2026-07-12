"""Game data: items, monsters, zones, sidejobs, pets, i18n, flavor."""

ITEMS = {
    "wooden_sword":    {"name": {"id": "🗡️ Pedang Kayu", "en": "🗡️ Wooden Sword"}, "type": "weapon", "atk": 5, "drop": True},
    "iron_sword":      {"name": {"id": "⚔️ Pedang Besi", "en": "⚔️ Iron Sword"}, "type": "weapon", "atk": 15, "drop": True},
    "steel_sword":     {"name": {"id": "⚔️ Pedang Baja", "en": "⚔️ Steel Sword"}, "type": "weapon", "atk": 30, "drop": True},
    "silver_blade":    {"name": {"id": "🗡️ Bilah Perak", "en": "🗡️ Silver Blade"}, "type": "weapon", "atk": 45, "drop": True},
    "shadow_dagger":   {"name": {"id": "🗡️ Belati Bayangan", "en": "🗡️ Shadow Dagger"}, "type": "weapon", "atk": 55, "drop": True},
    "legendary_sword": {"name": {"id": "⚔️ Pedang Legenda", "en": "⚔️ Legendary Sword"}, "type": "weapon", "atk": 100, "price_diamond": 5, "shop_only": True},
    "leather_armor":   {"name": {"id": "🛡️ Armor Kulit", "en": "🛡️ Leather Armor"}, "type": "armor", "def": 5, "drop": True},
    "iron_armor":      {"name": {"id": "🛡️ Armor Besi", "en": "🛡️ Iron Armor"}, "type": "armor", "def": 15, "drop": True},
    "steel_armor":     {"name": {"id": "🛡️ Armor Baja", "en": "🛡️ Steel Armor"}, "type": "armor", "def": 30, "drop": True},
    "scale_mail":      {"name": {"id": "🛡️ Zirah Sisik", "en": "🛡️ Scale Mail"}, "type": "armor", "def": 42, "drop": True},
    "dragon_armor":    {"name": {"id": "🛡️ Armor Naga", "en": "🛡️ Dragon Armor"}, "type": "armor", "def": 80, "price_diamond": 8, "shop_only": True},
    "health_potion":   {"name": {"id": "🧪 Ramuan HP", "en": "🧪 HP Potion"}, "type": "consumable", "heal": 30, "price_gold": 50, "drop": True},
    "big_potion":      {"name": {"id": "🧪 Ramuan HP+", "en": "🧪 Big HP Potion"}, "type": "consumable", "heal": 80, "price_gold": 150, "drop": True},
    "energy_potion":   {"name": {"id": "⚡ Ramuan Energi", "en": "⚡ Energy Potion"}, "type": "consumable", "energy": 25, "price_gold": 40, "drop": True},
    "energy_refill":   {"name": {"id": "⚡ Energi Penuh", "en": "⚡ Full Energy"}, "type": "consumable", "energy": 50, "price_diamond": 1, "shop_only": True},
    "exp_booster":     {"name": {"id": "✨ Booster EXP", "en": "✨ EXP Booster"}, "type": "buff", "exp_mult": 2.0, "duration_h": 24, "price_diamond": 2, "shop_only": True},
    "lucky_charm":     {"name": {"id": "🍀 Jimat Hoki", "en": "🍀 Lucky Charm"}, "type": "buff", "exp_mult": 1.0, "duration_h": 12, "price_diamond": 3, "shop_only": True},
    # ── FOOD & DRINK ───────────────────────────────────────────
    "bread":           {"name": {"id": "🍞 Roti", "en": "🍞 Bread"}, "type": "food", "heal": 15, "price_gold": 20, "drop": True},
    "meat":            {"name": {"id": "🍖 Daging", "en": "🍖 Meat"}, "type": "food", "heal": 40, "price_gold": 60, "drop": True},
    "fish":            {"name": {"id": "🐟 Ikan", "en": "🐟 Fish"}, "type": "food", "heal": 55, "price_gold": 100, "drop": True},
    "water":           {"name": {"id": "💧 Air", "en": "💧 Water"}, "type": "drink", "energy": 15, "price_gold": 15, "drop": True},
    "milk":            {"name": {"id": "🥛 Susu", "en": "🥛 Milk"}, "type": "drink", "energy": 30, "price_gold": 40, "drop": True},
    "ale":             {"name": {"id": "🍺 Bir", "en": "🍺 Ale"}, "type": "drink", "energy": 45, "price_gold": 80, "drop": True},
}

# pets: can drop on road or via contract
PETS = {
    "wolf_pup":   {"name": {"id": "🐺 Anak Serigala", "en": "🐺 Wolf Pup"}, "atk": 3, "gold_bonus": 0.1, "rarity": "common"},
    "fox":        {"name": {"id": "🦊 Rubah", "en": "🦊 Fox"}, "atk": 2, "gold_bonus": 0.15, "rarity": "common"},
    "owl":        {"name": {"id": "🦉 Burung Hantu", "en": "🦉 Owl"}, "atk": 1, "gold_bonus": 0.05, "exp_bonus": 0.1, "rarity": "uncommon"},
    "slime_pet":  {"name": {"id": "🟢 Slime Jinak", "en": "🟢 Pet Slime"}, "atk": 4, "gold_bonus": 0.12, "rarity": "uncommon"},
    "cat":        {"name": {"id": "🐱 Kucing Sihir", "en": "🐱 Magic Cat"}, "atk": 2, "gold_bonus": 0.2, "rarity": "rare"},
    "phoenix":    {"name": {"id": "🔥 Phoenix Mini", "en": "🔥 Mini Phoenix"}, "atk": 8, "gold_bonus": 0.25, "rarity": "epic"},
    "golden_pet": {"name": {"id": "🐉 Pet Emas", "en": "🐉 Golden Pet"}, "atk": 5, "gold_bonus": 0.5, "rarity": "legendary", "price_diamond": 10, "shop_only": True},
}

# register pets into ITEMS for equip system
for _k, _v in PETS.items():
    ITEMS[_k] = {
        "name": _v["name"], "type": "pet",
        "atk": _v.get("atk", 0), "gold_bonus": _v.get("gold_bonus", 0),
        "exp_bonus": _v.get("exp_bonus", 0),
        "price_diamond": _v.get("price_diamond", 0),
        "shop_only": _v.get("shop_only", False),
        "drop": not _v.get("shop_only", False),
        "rarity": _v.get("rarity", "common"),
    }

MONSTERS = {
    # plains
    "slime":       {"name": {"id": "🟢 Slime", "en": "🟢 Slime"}, "hp": 30, "atk": 5, "def": 2, "exp": 10, "gold": 15, "min_level": 1, "zone": "plains", "hard": False, "diamond_chance": 0},
    "goblin":      {"name": {"id": "👺 Goblin", "en": "👺 Goblin"}, "hp": 50, "atk": 10, "def": 5, "exp": 25, "gold": 40, "min_level": 1, "zone": "plains", "hard": False, "diamond_chance": 0},
    "wild_boar":   {"name": {"id": "🐗 Babi Hutan", "en": "🐗 Wild Boar"}, "hp": 60, "atk": 12, "def": 6, "exp": 28, "gold": 45, "min_level": 2, "zone": "plains", "hard": False, "diamond_chance": 0},
    "bandit":      {"name": {"id": "🗡️ Bandit", "en": "🗡️ Bandit"}, "hp": 70, "atk": 14, "def": 7, "exp": 35, "gold": 55, "min_level": 2, "zone": "plains", "hard": False, "diamond_chance": 0.02},
    # forest
    "wolf":        {"name": {"id": "🐺 Serigala", "en": "🐺 Wolf"}, "hp": 75, "atk": 16, "def": 8, "exp": 40, "gold": 60, "min_level": 3, "zone": "forest", "hard": False, "diamond_chance": 0.02},
    "orc":         {"name": {"id": "👹 Orc", "en": "👹 Orc"}, "hp": 90, "atk": 18, "def": 10, "exp": 55, "gold": 80, "min_level": 3, "zone": "forest", "hard": False, "diamond_chance": 0.04},
    "ent":         {"name": {"id": "🌳 Ent", "en": "🌳 Ent"}, "hp": 110, "atk": 15, "def": 18, "exp": 60, "gold": 70, "min_level": 4, "zone": "forest", "hard": False, "diamond_chance": 0.05},
    "forest_witch": {"name": {"id": "🧚 Iblis Hutan", "en": "🧚 Forest Fiend"}, "hp": 100, "atk": 20, "def": 12, "exp": 70, "gold": 90, "min_level": 5, "zone": "forest", "hard": True, "diamond_chance": 0.12},
    # cave
    "bat":         {"name": {"id": "🦇 Kelelawar", "en": "🦇 Cave Bat"}, "hp": 55, "atk": 14, "def": 4, "exp": 30, "gold": 40, "min_level": 4, "zone": "cave", "hard": False, "diamond_chance": 0.02},
    "troll":       {"name": {"id": "🧌 Troll", "en": "🧌 Troll"}, "hp": 130, "atk": 22, "def": 14, "exp": 85, "gold": 120, "min_level": 5, "zone": "cave", "hard": True, "diamond_chance": 0.15},
    "golem":       {"name": {"id": "🗿 Golem Batu", "en": "🗿 Stone Golem"}, "hp": 160, "atk": 18, "def": 25, "exp": 100, "gold": 110, "min_level": 6, "zone": "cave", "hard": True, "diamond_chance": 0.18},
    "slime_king":  {"name": {"id": "👑 Slime Raja", "en": "👑 Slime King"}, "hp": 180, "atk": 22, "def": 12, "exp": 150, "gold": 200, "min_level": 6, "zone": "cave", "hard": True, "diamond_chance": 0.22},
    # mountain
    "harpy":       {"name": {"id": "🦅 Harpy", "en": "🦅 Harpy"}, "hp": 120, "atk": 26, "def": 10, "exp": 110, "gold": 140, "min_level": 7, "zone": "mountain", "hard": True, "diamond_chance": 0.2},
    "yeti":        {"name": {"id": "❄️ Yeti", "en": "❄️ Yeti"}, "hp": 200, "atk": 28, "def": 18, "exp": 160, "gold": 180, "min_level": 8, "zone": "mountain", "hard": True, "diamond_chance": 0.25},
    "dragon":      {"name": {"id": "🐉 Naga", "en": "🐉 Dragon"}, "hp": 260, "atk": 35, "def": 22, "exp": 220, "gold": 320, "min_level": 8, "zone": "mountain", "hard": True, "diamond_chance": 0.35},
    # ruins
    "skeleton":    {"name": {"id": "💀 Skeleton", "en": "💀 Skeleton"}, "hp": 90, "atk": 20, "def": 12, "exp": 75, "gold": 90, "min_level": 6, "zone": "ruins", "hard": False, "diamond_chance": 0.08},
    "wraith":      {"name": {"id": "👻 Wraith", "en": "👻 Wraith"}, "hp": 140, "atk": 30, "def": 8, "exp": 130, "gold": 150, "min_level": 7, "zone": "ruins", "hard": True, "diamond_chance": 0.22},
    "lich":        {"name": {"id": "☠️ Lich", "en": "☠️ Lich"}, "hp": 220, "atk": 34, "def": 16, "exp": 200, "gold": 280, "min_level": 9, "zone": "ruins", "hard": True, "diamond_chance": 0.3},
    # void (high)
    "void_spawn":  {"name": {"id": "🌌 Void Spawn", "en": "🌌 Void Spawn"}, "hp": 280, "atk": 40, "def": 20, "exp": 260, "gold": 350, "min_level": 12, "zone": "void", "hard": True, "diamond_chance": 0.4},
    "void_knight": {"name": {"id": "🌑 Void Knight", "en": "🌑 Void Knight"}, "hp": 350, "atk": 48, "def": 28, "exp": 320, "gold": 420, "min_level": 15, "zone": "void", "hard": True, "diamond_chance": 0.5},
    # swamp
    "croc":        {"name": {"id": "🐊 Buaya Rawa", "en": "🐊 Swamp Croc"}, "hp": 95, "atk": 18, "def": 12, "exp": 55, "gold": 70, "min_level": 4, "zone": "swamp", "hard": False, "diamond_chance": 0.03},
    "leech":       {"name": {"id": "🪱 Lintah Raksasa", "en": "🪱 Giant Leech"}, "hp": 70, "atk": 22, "def": 6, "exp": 48, "gold": 55, "min_level": 5, "zone": "swamp", "hard": False, "diamond_chance": 0.04},
    "swamp_lord":  {"name": {"id": "🐸 Raja Rawa", "en": "🐸 Swamp Lord"}, "hp": 200, "atk": 28, "def": 16, "exp": 140, "gold": 180, "min_level": 7, "zone": "swamp", "hard": True, "diamond_chance": 0.2},
    # desert
    "scorpion":    {"name": {"id": "🦂 Kalajengking", "en": "🦂 Scorpion"}, "hp": 85, "atk": 20, "def": 10, "exp": 50, "gold": 65, "min_level": 5, "zone": "desert", "hard": False, "diamond_chance": 0.04},
    "mummy":       {"name": {"id": "🧟 Mumi", "en": "🧟 Mummy"}, "hp": 140, "atk": 18, "def": 20, "exp": 80, "gold": 100, "min_level": 6, "zone": "desert", "hard": False, "diamond_chance": 0.08},
    "sand_wyrm":   {"name": {"id": "🐍 Cacing Pasir", "en": "🐍 Sand Wyrm"}, "hp": 240, "atk": 32, "def": 18, "exp": 170, "gold": 220, "min_level": 9, "zone": "desert", "hard": True, "diamond_chance": 0.28},
    # crystal caves
    "crystal_bat": {"name": {"id": "💎 Kelelawar Kristal", "en": "💎 Crystal Bat"}, "hp": 100, "atk": 22, "def": 8, "exp": 70, "gold": 90, "min_level": 8, "zone": "crystal_caves", "hard": False, "diamond_chance": 0.1},
    "gem_golem":   {"name": {"id": "💠 Golem Permata", "en": "💠 Gem Golem"}, "hp": 260, "atk": 26, "def": 30, "exp": 180, "gold": 240, "min_level": 10, "zone": "crystal_caves", "hard": True, "diamond_chance": 0.32},
    # sky isles
    "cloud_spirit":{"name": {"id": "☁️ Roh Awan", "en": "☁️ Cloud Spirit"}, "hp": 120, "atk": 28, "def": 10, "exp": 95, "gold": 110, "min_level": 9, "zone": "sky_isles", "hard": False, "diamond_chance": 0.12},
    "sky_seraph":  {"name": {"id": "🪽 Seraph Langit", "en": "🪽 Sky Seraph"}, "hp": 300, "atk": 38, "def": 22, "exp": 240, "gold": 300, "min_level": 12, "zone": "sky_isles", "hard": True, "diamond_chance": 0.38},
    # abyss
    "abyss_worm":  {"name": {"id": "🪱 Cacing Abyss", "en": "🪱 Abyss Worm"}, "hp": 320, "atk": 42, "def": 24, "exp": 280, "gold": 360, "min_level": 14, "zone": "abyss", "hard": True, "diamond_chance": 0.42},
    "abyss_lord":  {"name": {"id": "👁️ Lord Abyss", "en": "👁️ Abyss Lord"}, "hp": 450, "atk": 55, "def": 32, "exp": 400, "gold": 500, "min_level": 18, "zone": "abyss", "hard": True, "diamond_chance": 0.55},
}

ZONES = {
    "plains":        {"name": {"id": "🌾 Dataran", "en": "🌾 Plains"}, "min_level": 1, "unlock_prestige": 0},
    "forest":        {"name": {"id": "🌲 Hutan", "en": "🌲 Forest"}, "min_level": 3, "unlock_prestige": 0},
    "swamp":         {"name": {"id": "🐸 Rawa", "en": "🐸 Swamp"}, "min_level": 4, "unlock_prestige": 0},
    "cave":          {"name": {"id": "🕳️ Gua", "en": "🕳️ Cave"}, "min_level": 5, "unlock_prestige": 0},
    "desert":        {"name": {"id": "🏜️ Gurun", "en": "🏜️ Desert"}, "min_level": 5, "unlock_prestige": 0},
    "ruins":         {"name": {"id": "🏛️ Reruntuhan", "en": "🏛️ Ruins"}, "min_level": 6, "unlock_prestige": 0},
    "mountain":      {"name": {"id": "⛰️ Gunung", "en": "⛰️ Mountain"}, "min_level": 7, "unlock_prestige": 0},
    "crystal_caves": {"name": {"id": "💎 Gua Kristal", "en": "💎 Crystal Caves"}, "min_level": 8, "unlock_prestige": 0},
    "sky_isles":     {"name": {"id": "☁️ Kepulauan Langit", "en": "☁️ Sky Isles"}, "min_level": 9, "unlock_prestige": 0},
    "void":          {"name": {"id": "🌌 Void", "en": "🌌 Void"}, "min_level": 12, "unlock_prestige": 1},
    "abyss":         {"name": {"id": "🕳️ Abyss", "en": "🕳️ Abyss"}, "min_level": 14, "unlock_prestige": 2},
}

SIDEJOBS = {
    "farmer": {
        "id": {"title": "🌾 Kerja di ladang", "steps": [
            "Mulai bantu panen. Tangan kotor, mood oke.",
            "Masih di ladang… jagungnya gak abis-abis.",
            "Istirahat sebentar di bawah pohon. Lanjut lagi.",
            "Angkut hasil panen ke gudang. Pegel tapi senyum.",
            "Panen selesai! Bayaran masuk. Capek tapi puas.",
        ]},
        "en": {"title": "🌾 Farm work", "steps": [
            "Helping harvest. Dirty hands, good mood.",
            "Still farming… endless corn.",
            "Short break under a tree. Back to work.",
            "Hauling harvest to storage. Sore but smiling.",
            "Done! Paid. Tired but happy.",
        ]},
        "gold": (50, 120), "exp": (15, 40),
    },
    "miner": {
        "id": {"title": "⛏️ Kerja di tambang", "steps": [
            "Masuk tambang. Gelap. \"Ini aman kan?\"",
            "Masih nambang… ketemu batu aneh. Dikantongin.",
            "Lentera hampir padam. Tetap maju pelan.",
            "Dengar suara aneh di lorong. Diabaikan… dulu.",
            "Keluar! Ada upah + debu di muka.",
        ]},
        "en": {"title": "⛏️ Mining", "steps": [
            "Enters the mine. Dark. \"Safe, right?\"",
            "Still mining… weird rock. Pockets it.",
            "Lantern almost dies. Moves carefully.",
            "Hears a weird sound in the tunnel. Ignores… for now.",
            "Out! Paid and dusty.",
        ]},
        "gold": (60, 140), "exp": (20, 50),
    },
    "courier": {
        "id": {"title": "📦 Kurir paket", "steps": [
            "Ambil paket. \"Jangan digoyang.\" Digoyang dikit.",
            "Masih antar… tersesat sebentar.",
            "Tanya arah ke orang lokal. Dijawab berbelit.",
            "Hampir nyampe. Hujan gerimis. Gas terus.",
            "Paket sampai! Dapat tip.",
        ]},
        "en": {"title": "📦 Courier", "steps": [
            "Picks up package. \"Don't shake.\" Shakes a little.",
            "Still delivering… gets lost briefly.",
            "Asks a local for directions. Confusing answer.",
            "Almost there. Light rain. Keep going.",
            "Delivered! Got a tip.",
        ]},
        "gold": (40, 100), "exp": (12, 35),
    },
    "guard": {
        "id": {"title": "🛡️ Jaga gudang", "steps": [
            "Shift jaga mulai. Menguap.",
            "Masih jaga… hampir ketiduran.",
            "Dengar bunyi mencurigakan. Ternyata tikus.",
            "Jalan keliling gudang sekali lagi.",
            "Shift selesai! Bayaran + kebanggaan palsu.",
        ]},
        "en": {"title": "🛡️ Guard", "steps": [
            "Guard shift starts. Yawn.",
            "Still guarding… almost naps.",
            "Suspicious noise. It's a rat.",
            "Walks around the warehouse again.",
            "Shift done! Paid + fake pride.",
        ]},
        "gold": (45, 110), "exp": (15, 40),
    },
    "fisher": {
        "id": {"title": "🎣 Mancing", "steps": [
            "Lempar kail. \"Ayo ikan…\"",
            "Masih nunggu… umpan dimakan angin.",
            "Ganti umpan. Lebih sabar kali ini.",
            "Ada tarikan! Hampir lepas.",
            "Dapet ikan! Dijual di pasar.",
        ]},
        "en": {"title": "🎣 Fishing", "steps": [
            "Casts the line. \"Come on fish…\"",
            "Still waiting… bait taken by wind.",
            "Changes bait. More patient this time.",
            "A bite! Almost loses it.",
            "Caught one! Sold at market.",
        ]},
        "gold": (35, 95), "exp": (10, 30),
    },
    "cook": {
        "id": {"title": "🍳 Bantu dapur", "steps": [
            "Iris bawang. Menangis. \"Ini normal.\"",
            "Masih masak… hampir gosong.",
            "Cicip kuah. \"Kurang garam.\"",
            "Sajikan di meja. Harum.",
            "Masakan jadi! Dapat bayaran + pujian.",
        ]},
        "en": {"title": "🍳 Kitchen help", "steps": [
            "Chopping onions. Crying. \"Normal.\"",
            "Still cooking… almost burned.",
            "Tastes the soup. \"Needs salt.\"",
            "Plates the food. Smells good.",
            "Food ready! Paid + compliments.",
        ]},
        "gold": (40, 105), "exp": (12, 32),
    },
    "scribe": {
        "id": {"title": "📜 Juru tulis", "steps": [
            "Salin naskah. Tangan pegal.",
            "Masih nulis… tinta tumpah dikit.",
            "Perbaiki goresan. Rapiin lagi.",
            "Halaman terakhir. Hampir selesai.",
            "Selesai! Bayaran dari pustakawan.",
        ]},
        "en": {"title": "📜 Scribe", "steps": [
            "Copying manuscripts. Hand cramps.",
            "Still writing… ink spill.",
            "Fixes a scratch. Tidies the page.",
            "Last page. Almost done.",
            "Done! Librarian pays.",
        ]},
        "gold": (55, 115), "exp": (25, 55),
    },
    "hunter": {
        "id": {"title": "🏹 Berburu", "steps": [
            "Masuk hutan. Lacak jejak.",
            "Hampir kena jebakan sendiri…",
            "Nunggu di semak. Sabar.",
            "Ada target! Panah lepas.",
            "Dapet buruan! Dijual di desa.",
        ]},
        "en": {"title": "🏹 Hunting", "steps": [
            "Enters forest. Tracks prey.",
            "Almost steps on own trap…",
            "Waits in bushes. Patient.",
            "Target spotted! Arrow flies.",
            "Got the hunt! Sold in village.",
        ]},
        "gold": (65, 150), "exp": (22, 48),
    },
}

# Fictional kingdoms used as auto guild names
KINGDOMS = [
    "Kerajaan Auroria", "Imperium Thalor", "Kerajaan Nymoria", "Kekaisaran Draven",
    "Kerajaan Sylvara", "Dominion Kaelith", "Kerajaan Orinthal", "Republik Veyra",
    "Kerajaan Frosthelm", "Imperium Solmere", "Kerajaan Emberfall", "Duchy of Lirien",
    "Kerajaan Moonspire", "House of Valcrest", "Kerajaan Starfen", "Realm of Cindral",
    "Kerajaan Ashbourne", "Crown of Wyrmrest", "Kerajaan Silvermere", "Order of Dawnkeep",
]

WEEKLY_CONTRACTS = [
    {"key": "kill_20", "target": 20, "stat": "week_kills", "reward_gold": 500, "reward_diamond": 1,
     "name": {"id": "Bantai 20 musuh", "en": "Defeat 20 foes"}},
    {"key": "gold_1000", "target": 1000, "stat": "week_gold", "reward_gold": 300, "reward_diamond": 1,
     "name": {"id": "Kumpul 1000 gold", "en": "Earn 1000 gold"}},
    {"key": "jobs_5", "target": 5, "stat": "week_jobs", "reward_gold": 400, "reward_diamond": 1,
     "name": {"id": "Selesaiin 5 side job", "en": "Finish 5 side jobs"}},
    {"key": "hard_5", "target": 5, "stat": "week_hard", "reward_gold": 600, "reward_diamond": 2,
     "name": {"id": "Kalahkan 5 musuh sulit", "en": "Beat 5 hard foes"}},
    {"key": "pet_1", "target": 1, "stat": "week_pets", "reward_gold": 350, "reward_diamond": 2,
     "name": {"id": "Temukan 1 pet", "en": "Find 1 pet"}},
]

ACHIEVEMENTS = {
    "first_blood":  {"name": {"id": "🩸 First Blood", "en": "🩸 First Blood"}, "desc": {"id": "Kalahkan musuh pertama", "en": "Beat first foe"}, "check": "kills", "need": 1, "reward_diamond": 1},
    "slayer_10":    {"name": {"id": "⚔️ Slayer", "en": "⚔️ Slayer"}, "desc": {"id": "10 musuh", "en": "10 foes"}, "check": "kills", "need": 10, "reward_diamond": 1},
    "slayer_100":   {"name": {"id": "⚔️ Slayer II", "en": "⚔️ Slayer II"}, "desc": {"id": "100 musuh", "en": "100 foes"}, "check": "kills", "need": 100, "reward_diamond": 3},
    "rich_5k":      {"name": {"id": "💰 Kaya", "en": "💰 Rich"}, "desc": {"id": "Punya 5000 gold", "en": "Hold 5000 gold"}, "check": "gold", "need": 5000, "reward_diamond": 1},
    "streak_3":     {"name": {"id": "🔥 Streak 3", "en": "🔥 Streak 3"}, "desc": {"id": "Streak 3 hari", "en": "3-day streak"}, "check": "streak", "need": 3, "reward_diamond": 1},
    "streak_7":     {"name": {"id": "🔥 Streak 7", "en": "🔥 Streak 7"}, "desc": {"id": "Streak 7 hari", "en": "7-day streak"}, "check": "streak", "need": 7, "reward_diamond": 2},
    "pet_owner":    {"name": {"id": "🐾 Pet Owner", "en": "🐾 Pet Owner"}, "desc": {"id": "Punya pet", "en": "Own a pet"}, "check": "pets", "need": 1, "reward_diamond": 1},
    "zone_forest":  {"name": {"id": "🌲 Explorer", "en": "🌲 Explorer"}, "desc": {"id": "Masuk hutan", "en": "Enter forest"}, "check": "zone_forest", "need": 1, "reward_diamond": 1},
    "prestige_1":   {"name": {"id": "⭐ Prestige", "en": "⭐ Prestige"}, "desc": {"id": "Prestige 1x", "en": "Prestige once"}, "check": "prestige", "need": 1, "reward_diamond": 5},
}

BLESSINGS = [
    {"key": "atk", "name": {"id": "⚔️ Berkah Kekuatan", "en": "⚔️ Blessing of Might"}, "atk": 5, "hours": 6},
    {"key": "def", "name": {"id": "🛡️ Berkah Perisai", "en": "🛡️ Blessing of Shield"}, "def": 5, "hours": 6},
    {"key": "gold", "name": {"id": "💰 Berkah Kekayaan", "en": "💰 Blessing of Wealth"}, "gold_bonus": 0.25, "hours": 6},
    {"key": "exp", "name": {"id": "✨ Berkah Bijak", "en": "✨ Blessing of Wisdom"}, "exp_bonus": 0.25, "hours": 6},
    {"key": "heal", "name": {"id": "❤️ Berkah Hidup", "en": "❤️ Blessing of Life"}, "heal": True, "hours": 0},
]

FLAV = {
    "walk": {
        "id": [
            "Jalan santai. Sambil mikir: \"Makan apa nanti ya?\"",
            "Hampir nabrak pohon. \"Pohonnya yang geser.\"",
            "Nyanyi lagu perang. Burung-burung: 🏃‍♂️",
            "Liat awan bentuk naga. \"Nanti aku lawan itu.\"",
            "Hitung gold di kepala. Hmm.",
            "Angin kenceng. Rambut berantakan. Gaya.",
            "Ketemu kucing. Salam. Kucingnya cuek.",
            "Jalan terus. \"Dewa, aku keren kan?\"",
        ],
        "en": [
            "Casual stroll. \"What should I eat later?\"",
            "Almost walks into a tree. \"Tree should move.\"",
            "Sings a war song. Birds flee.",
            "Cloud looks like a dragon. \"I'll fight that later.\"",
            "Counts gold in their head. Hmm.",
            "Windy. Messy hair. Style.",
            "Meets a cat. Says hi. Cat ignores.",
            "Keeps walking. \"Deity, I look cool, right?\"",
        ],
    },
    "rest": {
        "id": [
            "Istirahat di tepi jalan. \"5 menit doang…\" (bohong)",
            "Duduk di bawah pohon. Pohonnya: \"Lagi?\"",
            "Minum air sungai. \"Seger! Lanjut gas.\"",
            "Rebahan sebentar. Energi naik pelan-pelan.",
        ],
        "en": [
            "Rests by the road. \"Just 5 minutes…\" (lie)",
            "Sits under a tree. Tree: \"Again?\"",
            "Drinks river water. \"Fresh! Let's go.\"",
            "Lies down a bit. Energy creeps up.",
        ],
    },
    "loot": {
        "id": [
            "Nemu kantong koin di semak. \"Rezeki nomplok!\"",
            "Peti kecil di jalan. Dibuka… gold! 🎉",
            "Gali tanah iseng. Ketemu koin. Dunia aneh.",
            "Ada yang jatuh dari gerobak. \"Milikku sekarang.\"",
        ],
        "en": [
            "Finds coin pouch. \"Lucky day!\"",
            "Small chest. Gold! 🎉",
            "Digs for fun. Finds coins.",
            "Something falls off a cart. \"Mine now.\"",
        ],
    },
    "win": {
        "id": [
            "Menang! \"Gampang.\" (sebenarnya deg-degan)",
            "Musuh kabur. \"Iya iya, takut kan!\"",
            "Kemenangan manis. Pose 3 detik.",
            "\"Dewa, liat aku menang!\"",
        ],
        "en": [
            "Win! \"Easy.\" (heart racing)",
            "Enemy runs. \"Yeah you better!\"",
            "Sweet victory. 3-second pose.",
            "\"Deity, look at me win!\"",
        ],
    },
    "lose": {
        "id": [
            "Kalah… \"Itu strategi. Mundur dulu.\"",
            "Tumbang. Bangun. \"Rematch next time.\"",
            "Luka dikit. \"Masih hidup. Masih keren.\"",
            "\"Dewa… bantu dong.\" (dewa lagi offline?)",
        ],
        "en": [
            "Lost… \"Tactical retreat.\"",
            "Down. Up. \"Rematch later.\"",
            "A bit hurt. \"Still alive. Still cool.\"",
            "\"Deity… help?\" (maybe offline)",
        ],
    },
    "trade": {
        "id": [
            "Pedagang lewat. Deal! 🤝",
            "Jajan di pinggir jalan. Dompet menipis, hati senang.",
            "Tawar-menawar hebat. \"Jago juga aku.\"",
        ],
        "en": [
            "Trader passes. Deal! 🤝",
            "Snacks by the road. Wallet thinner, heart happier.",
            "Great bargaining. \"I'm good at this.\"",
        ],
    },
    "battle_start": {
        "id": ["Eh? Ada yang di semak…", "Langkah berhenti. Musuh muncul!", "\"Siapa di sana?!\" …ternyata lawan."],
        "en": ["Wait… something in the bushes…", "Steps stop. Enemy appears!", "\"Who's there?!\" …a foe."],
    },
    "pet_find": {
        "id": [
            "Ada yang ikut di belakang… pet baru?!",
            "Hewan kecil menatap. \"Mau bareng?\"",
            "Nemu makhluk imut. Langsung diadopsi.",
        ],
        "en": [
            "Something follows… a new pet?!",
            "A small creature stares. \"Wanna join?\"",
            "Finds a cute critter. Instant adopt.",
        ],
    },
}

T = {
    "choose_lang": {"id": "🌐 Pilih bahasa dulu yuk:", "en": "🌐 Pick a language first:"},
    "ask_deity": {"id": "✨ Nama *Dewa* kamu siapa?", "en": "✨ What's your *Deity* name?"},
    "ask_hero": {"id": "🦸 Nama *Hero* kamu siapa?", "en": "🦸 What's your *Hero* name?"},
    "saved_deity": {"id": "✅ Dewa: *{name}*\n\nSekarang nama hero-nya:", "en": "✅ Deity: *{name}*\n\nNow the hero's name:"},
    "btn_hero": {"id": "🦸 Hero", "en": "🦸 Hero"},
    "btn_diary": {"id": "📖 Diary", "en": "📖 Diary"},
    "btn_inv": {"id": "🎒 Inventory", "en": "🎒 Inventory"},
    "btn_shop": {"id": "💎 Shop", "en": "💎 Shop"},
    "btn_rank": {"id": "🏆 Ranking", "en": "🏆 Ranking"},
    "btn_bless": {"id": "🙏 Blessing", "en": "🙏 Blessing"},
    "btn_friends": {"id": "👥 Teman", "en": "👥 Friends"},
    "btn_ach": {"id": "🏅 Achievements", "en": "🏅 Achievements"},
    "btn_prestige": {"id": "⭐ Prestige", "en": "⭐ Prestige"},
    "btn_wiki": {"id": "📚 Wiki", "en": "📚 Wiki"},
    "btn_lang": {"id": "🌐 Bahasa", "en": "🌐 Language"},
    "btn_talk": {"id": "💬 Ngobrol", "en": "💬 Talk"},
    "btn_next": {"id": "Next ▶️", "en": "Next ▶️"},
    "btn_back": {"id": "◀️ Back", "en": "◀️ Back"},
    "btn_select": {"id": "✅ Pilih", "en": "✅ Select"},
    "btn_view_ach": {"id": "🏅 Lihat Achievements", "en": "🏅 View Achievements"},
    "btn_prestige_go": {"id": "⭐ Prestige Sekarang", "en": "⭐ Prestige Now"},
    "talk_intro": {
        "id": (
            "💬 *Ngobrol sama Hero*\n"
            "━━━━━━━━━━━━━━\n"
            "Dewa bisa ngomong langsung, hero bales.\n"
            "Tulis pesan di bawah, atau ketik `batal` buat keluar.\n\n"
            "_Pesanmu masuk ke diary hero juga._"
        ),
        "en": (
            "💬 *Talk to Hero*\n"
            "━━━━━━━━━━━━━━\n"
            "Deity speaks, hero replies.\n"
            "Type below, or `cancel` to exit.\n\n"
            "_Your message goes to hero's diary too._"
        ),
    },
    "no_friends": {"id": "Belum ada temen. Ketemu orang di jalan dulu!", "en": "No friends yet. Meet people on the road!"},
    "friend_header": {"id": "👥 *Teman* ({n})", "en": "👥 *Friends* ({n})"},
    "friend_detail": {
        "id": "👤 *{name}*\nLv {level} · 💰 {gold:,} · 💎 {diamond} · 🔥 streak {streak}\n🗺️ {zone} · ⭐ prestige {prestige}",
        "en": "👤 *{name}*\nLv {level} · 💰 {gold:,} · 💎 {diamond} · 🔥 streak {streak}\n🗺️ {zone} · ⭐ prestige {prestige}",
    },
    "ach_header": {"id": "🏅 *Achievements* ({done}/{total})", "en": "🏅 *Achievements* ({done}/{total})"},
    "prestige_info": {
        "id": "⭐ *Prestige*\n━━━━━━━━━━━━━━\nLevel sekarang: *{level}*\nPrestige: *{prestige}*\nBonus permanen: ⚔️+{batk} 🛡️+{bdef}\n\nButuh Lv *{need}+*\nPrestige = reset level/stats, bonus permanen naik, diamond + zona void lebih gampang.",
        "en": "⭐ *Prestige*\n━━━━━━━━━━━━━━\nCurrent level: *{level}*\nPrestige: *{prestige}*\nPermanent bonus: ⚔️+{batk} 🛡️+{bdef}\n\nNeed Lv *{need}+*\nPrestige resets level/stats, permanent bonus up, easier void access.",
    },
    "wiki_header": {"id": "📚 *Wiki*", "en": "📚 *Wiki*"},
    "wiki_cats": {
        "id": ["👹 Musuh", "🗡️ Item", "🐾 Pet", "🗺️ Zona", "🛠 Side Job", "🙏 Blessing", "📜 Kontrak", "⭐ Prestige"],
        "en": ["👹 Monsters", "🗡️ Items", "🐾 Pets", "🗺️ Zones", "🛠 Side Jobs", "🙏 Blessings", "📜 Contracts", "⭐ Prestige"],
    },
    "diary_empty": {"id": "_Belum ada catatan. Hero baru mulai jalan._", "en": "_No entries yet._"},
    "inv_empty": {"id": "🎒 Masih kosong.", "en": "🎒 Empty."},
    "shop_title": {
        "id": "💎 *Shop Langka*\n💎 Diamond: *{diamond}*\n\nBarang susah. Beli kalau mau cepat.\n💎 dari musuh sulit.",
        "en": "💎 *Rare Shop*\n💎 Diamonds: *{diamond}*\n\nHard-to-get stuff.\n💎 from hard foes.",
    },
    "not_enough_d": {"id": "❌ Diamond kurang", "en": "❌ Not enough diamonds"},
    "bought": {"id": "✅ {item}", "en": "✅ {item}"},
    "unknown": {"id": "Pakai tombol di bawah aja ya 👇", "en": "Use the buttons below 👇"},
    "friend_prompt": {"id": "Ketik username (tanpa @) atau user_id:", "en": "Type username (no @) or user_id:"},
    "friend_sent": {"id": "✅ Request ke *{name}* terkirim!", "en": "✅ Request sent to *{name}*!"},
    "friend_nf": {"id": "User nggak ketemu 😅", "en": "User not found 😅"},
    "friend_self": {"id": "Nggak bisa add diri sendiri 😂", "en": "Can't add yourself 😂"},
    "pvp_ch": {"id": "⚔️ *{a}* nantang duel!", "en": "⚔️ *{a}* challenges you!"},
    "pvp_win": {"id": "🏆 *{w}* menang lawan *{l}*!", "en": "🏆 *{w}* wins vs *{l}*!"},
    "pvp_lose": {"id": "💀 *{l}* kalah lawan *{w}*", "en": "💀 *{l}* loses to *{w}*"},
    "auto_equip": {"id": "🔧 Auto-equip: {item}", "en": "🔧 Auto-equipped: {item}"},
    "auto_use": {"id": "🧪 Auto-pakai: {item}", "en": "🧪 Auto-used: {item}"},
    "drop": {"id": "🎁 {item}", "en": "🎁 {item}"},
    "diamond_drop": {"id": "💎 +{n} Diamond!", "en": "💎 +{n} Diamond!"},
    "streak": {"id": "🔥 Streak *{n}* hari!", "en": "🔥 *{n}*-day streak!"},
    "bless_ok": {"id": "🙏 Blessing aktif: {name}", "en": "🙏 Blessing active: {name}"},
    "zone_set": {"id": "🗺️ Zona: {name}", "en": "🗺️ Zone: {name}"},
    "zone_lock": {"id": "🔒 Belum terbuka (Lv {lv})", "en": "🔒 Locked (Lv {lv})"},
    "contract_done": {"id": "📜 Kontrak selesai! 💰+{g} 💎+{d}", "en": "📜 Contract done! 💰+{g} 💎+{d}"},
    "ach_unlock": {"id": "🏅 Achievement: {name}!", "en": "🏅 Achievement: {name}!"},
    "prestige_ok": {"id": "⭐ Prestige *{n}*! Stats di-reset, bonus permanen naik.", "en": "⭐ Prestige *{n}*! Stats reset, permanent bonus up."},
    "prestige_no": {"id": "Butuh level {lv}+ buat prestige.", "en": "Need level {lv}+ for prestige."},
    "guild_create": {"id": "🏰 Guild *{name}* dibuat!", "en": "🏰 Guild *{name}* created!"},
    "guild_join": {"id": "🏰 Join guild *{name}*!", "en": "🏰 Joined guild *{name}*!"},
    "guild_prompt": {"id": "Ketik nama guild baru / kode join:", "en": "Type new guild name / join code:"},
    "pet_contract": {"id": "📝 Kontrak pet *{name}* 3 hari dimulai!", "en": "📝 Pet contract *{name}* for 3 days started!"},
    "pet_found": {"id": "🐾 Nemu pet: *{name}*!", "en": "🐾 Found pet: *{name}*!"},
}


def tr(lang: str, key: str, **kw) -> str:
    s = T.get(key, {}).get(lang) or T.get(key, {}).get("id") or key
    try:
        return s.format(**kw)
    except Exception:
        return s


def iname(key: str, lang: str) -> str:
    n = ITEMS.get(key, {}).get("name", {})
    return n.get(lang) or n.get("id") or key if isinstance(n, dict) else str(n or key)


def mname(key: str, lang: str) -> str:
    n = MONSTERS.get(key, {}).get("name", {})
    return n.get(lang) or n.get("id") or key if isinstance(n, dict) else str(n or key)


def zname(key: str, lang: str) -> str:
    n = ZONES.get(key, {}).get("name", {})
    return n.get(lang) or n.get("id") or key if isinstance(n, dict) else str(n or key)
