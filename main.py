#!/usr/bin/env python3
"""Journey of the Hero — modular Telegram idle RPG"""

import logging
import os
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters

# Load .env
_env = Path(__file__).resolve().parent / ".env"
if _env.exists():
    for line in _env.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

from modules.config import BOT_TOKEN, TICK_SEC
from modules.db import init_db, active_users
from modules.handlers import cmd_start, on_cb, on_text, adventure_job


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CallbackQueryHandler(on_cb))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    if app.job_queue:
        app.job_queue.run_repeating(adventure_job, interval=TICK_SEC, first=8)
        logging.info(f"Auto tick every {TICK_SEC}s")
    else:
        logging.warning("job_queue missing")

    print("Journey of the Hero (modular) running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
