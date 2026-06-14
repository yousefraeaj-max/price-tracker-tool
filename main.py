"""
main.py — نقطة الدخول الرئيسية
يشغّل بوت التليجرام + worker الأسعار في نفس الوقت
"""

import asyncio
import logging
import os
import sys
import threading

# إعداد الـ Logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

def run_bot():
    """تشغيل البوت في event loop خاص ومستقل داخل الـ thread"""
    import bot
    # ننشئ loop جديد خاص بالبوت لضمان استقراره داخل الـ Thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        log.info("بدء تطبيق البوت...")
        bot.main()
    except Exception as e:
        log.error(f"خطأ في الـ bot thread: {e}")

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
    try:
        asyncio.run(run_scraper())
    except KeyboardInterrupt:
        log.info("تم إيقاف المنصة")

if __name__ == "__main__":
    main()
