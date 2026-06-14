"""
bot.py — بوت التليجرام
مسؤول عن: تأكيد الهوية + إرسال تنبيهات الأسعار
شغّله بشكل مستقل: python bot.py
"""

import asyncio
import logging
import os
import sys

from telegram import (
    Bot, Update,
    KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove,
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes,
)

import database as db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
BOT_USERNAME   = os.environ.get("BOT_USERNAME", "MyPriceTracker11Bot")


# ─── /start ───────────────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    args = ctx.args  # قد يحتوي على link_token

    if args:
        token = args[0]
        user = db.get_user_by_token(token)

        if not user:
            await update.message.reply_text(
                "❌ رابط التفعيل غير صالح أو منتهي الصلاحية.\n"
                "ارجع للموقع واضغط زر التفعيل مرة ثانية."
            )
            return

        if user["is_verified"]:
            await update.message.reply_text(
                f"✅ حسابك مفعّل بالفعل يا {user['name']}!\n"
                "هتوصلك تنبيهات الأسعار هنا تلقائياً."
            )
            return

        # احتفظ بالـ token في session للخطوة الجاية
        ctx.user_data["link_token"] = token
        ctx.user_data["user_name"]  = user["name"]

        # اطلب مشاركة جهة الاتصال
        contact_btn = KeyboardButton("📱 مشاركة رقمي لتفعيل الحساب", request_contact=True)
        markup = ReplyKeyboardMarkup([[contact_btn]], resize_keyboard=True, one_time_keyboard=True)

        await update.message.reply_text(
            f"أهلاً {user['name']}! 👋\n\n"
            "لتفعيل حسابك وحمايته من التزوير،\n"
            "اضغط الزر أدناه لمشاركة رقم هاتفك مرة واحدة فقط ✅",
            reply_markup=markup,
        )

    else:
        await update.message.reply_text(
            "👋 أهلاً بك في Price Tracker Bot!\n\n"
            "للتفعيل، سجّل حساباً على موقعنا أولاً\n"
            "ثم اضغط زر «تفعيل الحساب» من لوحة التحكم."
        )


# ─── استقبال جهة الاتصال ─────────────────────────────────────

async def handle_contact(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    token   = ctx.user_data.get("link_token")

    if not token or not contact:
        await update.message.reply_text(
            "❌ انتهت الجلسة. ارجع للموقع واضغط زر التفعيل مرة ثانية.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    user = db.get_user_by_token(token)
    if not user:
        await update.message.reply_text(
            "❌ رابط غير صالح. ارجع للموقع واضغط زر التفعيل مرة ثانية.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    chat_id = str(update.effective_chat.id)
    phone   = contact.phone_number

    db.verify_user(user["id"], chat_id, phone)
    ctx.user_data.clear()

    await update.message.reply_text(
        f"🎉 تم تفعيل حسابك بنجاح يا {user['name']}!\n\n"
        f"📱 رقمك: {phone}\n"
        "✅ هتوصلك تنبيهات فور ما يتغير أي سعر هنا مباشرةً.",
        reply_markup=ReplyKeyboardRemove(),
    )

    log.info("✅ تم ربط المستخدم %s — chat_id: %s", user["email"], chat_id)


# ─── /status ──────────────────────────────────────────────────

async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    with db.get_conn() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE telegram_chat_id=?", (chat_id,)
        ).fetchone()

    if not user:
        await update.message.reply_text("مش مسجّل — افتح الموقع وفعّل حسابك.")
        return

    urls = db.get_urls_for_user(user["id"])
    my_count  = sum(1 for u in urls if u["category"] == "my_store")
    comp_count = sum(1 for u in urls if u["category"] == "competitor")

    await update.message.reply_text(
        f"👤 {user['name']}\n"
        f"📦 منتجات متجرك: {my_count}\n"
        f"🔍 مراقبة منافسين: {comp_count}\n"
        "✅ البوت شغّال ومتابع كل الأسعار."
    )


# ─── SEND ALERT (دالة خارجية يستخدمها الـ scraper) ──────────

async def send_alert(chat_id: str, message: str):
    if not TELEGRAM_TOKEN:
        log.warning("TELEGRAM_TOKEN مش متعمل")
        return
    try:
        bot = Bot(token=TELEGRAM_TOKEN)
        await bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode="Markdown",
        )
    except Exception as e:
        log.error("خطأ في إرسال التنبيه لـ %s: %s", chat_id, e)


def send_alert_sync(chat_id: str, message: str):
    """نسخة sync لاستخدامها من داخل asyncio.run()"""
    asyncio.run(send_alert(chat_id, message))


# ─── MAIN ─────────────────────────────────────────────────────

def main():
    if not TELEGRAM_TOKEN:
        log.error("TELEGRAM_TOKEN مش موجود في الـ environment!")
        sys.exit(1)

    app = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .build()
    )

    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))

    log.info("=== Telegram Bot شغّال ===")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
