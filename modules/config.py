import os

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_IDS = [6247336698]
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "rpg_game.db")
GAME_NAME = "Journey of the Hero"

TICK_SEC = 40
ENERGY_COST = 1
ENERGY_REGEN = 3
HP_REGEN = 4
AUTO_POTION_HP = 0.35
AUTO_POTION_EN = 0.25

# event weights (sum < 1, rest = walk)
ENCOUNTER = 0.28
REST = 0.10
LOOT = 0.14
TRADE = 0.07
SIDEJOB = 0.10
PET_FIND = 0.04

SIDEJOB_STEPS = 3
CONTRACT_DAYS = 7
PRESTIGE_MIN_LEVEL = 20