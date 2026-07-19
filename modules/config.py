import os

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
# Image generation settings
# Pollinations.ai - free, no key, decent quality (10-30s)
POLLINATIONS_API_URL = os.environ.get("POLLINATIONS_API_URL", "https://image.pollinations.ai")
# Fallback to local PIL pixel sprites if Pollinations fails/slow
IMAGE_CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".pixel_cache")
IMAGE_TIMEOUT = int(os.environ.get("IMAGE_TIMEOUT", "25"))  # seconds
# Google Generative Language API key (Gemini). Image models may hit free-tier 429;
# image_gen falls back to local PIL pixel sprites automatically.
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
IMAGE_MODEL = os.environ.get("IMAGE_MODEL", "gemini-2.5-flash-image")
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "rpg_game.db")
CACHE_DIR = os.path.join(BASE_DIR, ".pixel_cache")
GAME_NAME = "Journey of the Hero"
ADMIN_IDS = [6247336698]

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