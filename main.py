"""
main.py — نقطة الدخول الرئيسية
يشغّل بوت التليجرام + worker الأسعار في نفس الوقت
Railway بيشغّل ده من الـ Procfile
"""

import asyncio
import logging
import os
import sys
import threading

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


def run_bot():
    """يشغّل بوت التليجرام في thread منفصل"""
    import bot
    bot.main()


async def run_scraper():
    """يشغّل الـ worker في asyncio loop"""
    from scraper import run_worker
    await run_worker()


def main():
    token = os.environ.get("TELEGRAM_TOKEN", "")
    if not token:
        log.error("❌ TELEGRAM_TOKEN مش موجود — أضفه في Railway Variables")
        sys.exit(1)

    log.info("=== Price Tracker Platform بدأ ===")

    # شغّل البوت في thread خلفي
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    log.info("✅ Telegram Bot thread شغّال")

    # شغّل الـ scraper worker في الـ main loop
    log.info("✅ Price Scraper Worker بيبدأ...")
    asyncio.run(run_scraper())


if __name__ == "__main__":
    main()
