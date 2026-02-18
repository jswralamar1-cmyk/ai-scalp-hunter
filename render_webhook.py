"""
render_webhook.py
AI Scalp Hunter - Simplified Webhook Version
"""

import os
import logging
import asyncio
from flask import Flask, request, jsonify
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

from config import TELEGRAM_TOKEN
from bot_runner import run_scalp_analysis

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

app = Flask(__name__)

# متغيرات عامة
_bot_app = None
_bot_initialized = False
user_locks = {}

# ====================================================
# 🤖 دوال البوت
# ====================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🎯 اصطاد سكالبينغ", callback_data="hunt")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🔍 **AI Scalp Hunter**\n\n"
        "اضغط الزر لبدء التحليل الذكي.\n"
        "⏳ يستغرق التحليل 20–40 ثانية.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "hunt":
        await process_hunt(update, context)

async def process_hunt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_locks.get(user_id, False):
        await update.callback_query.answer("⚠️ التحليل جارٍ حالياً...", show_alert=True)
        return

    user_locks[user_id] = True
    progress_msg = None

    try:
        progress_msg = await update.callback_query.edit_message_text(
            "🔍 **AI Scalp Hunter**\n\n"
            "⏳ جاري التحليل...\n\n"
            "⚪ جلب البيانات\n"
            "⚪ حساب المؤشرات\n"
            "⚪ فلترة أفضل 15\n"
            "⚪ الذكاء الاصطناعي يحلل\n"
            "⚪ حساب الثقة\n"
            "⚪ التحقق من التكرار\n"
            "⚪ تجهيز النتائج",
            parse_mode="Markdown"
        )

        # تشغيل التحليل
        result = await run_scalp_analysis(
            progress_callback=lambda stage: update_progress(progress_msg, stage)
        )

        if result and len(result) > 0:
            for signal in result:
                if signal.get("chart_path") and os.path.exists(signal["chart_path"]):
                    with open(signal["chart_path"], "rb") as photo:
                        await context.bot.send_photo(
                            chat_id=update.effective_chat.id,
                            photo=photo,
                            caption=signal["message"],
                            parse_mode="Markdown"
                        )
                else:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=signal["message"],
                        parse_mode="Markdown"
                    )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=(
                    "🔍 **AI Scalp Hunter**\n\n"
                    "❌ لا توجد فرصة قوية حالياً (أقل من 65% ثقة).\n\n"
                    "⏳ انتظر 5–10 دقائق وحاول مجدداً."
                ),
                parse_mode="Markdown"
            )

    except Exception as e:
        logging.exception("Error during analysis")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"❌ حدث خطأ أثناء التحليل: {str(e)[:100]}"
        )
    finally:
        user_locks[user_id] = False
        if progress_msg:
            try:
                await progress_msg.delete()
            except:
                pass

async def update_progress(message, stage: int):
    stages = [
        "جلب البيانات",
        "حساب المؤشرات",
        "فلترة أفضل 15",
        "الذكاء الاصطناعي يحلل",
        "حساب الثقة",
        "التحقق من التكرار",
        "تجهيز النتائج"
    ]

    text = "🔍 **AI Scalp Hunter**\n\n⏳ جاري التحليل...\n\n"

    for i, s in enumerate(stages, 1):
        if i < stage:
            text += f"✅ {s}\n"
        elif i == stage:
            text += f"⏳ {s}\n"
        else:
            text += f"⚪ {s}\n"

    try:
        await message.edit_text(text, parse_mode="Markdown")
    except:
        pass

    await asyncio.sleep(0.4)

# ====================================================
# 🚀 إعداد البوت
# ====================================================
def init_bot_sync():
    """تهيئة البوت بشكل متزامن (تُستدعى مرة واحدة عند بدء التشغيل)"""
    global _bot_app, _bot_initialized

    if _bot_initialized:
        return _bot_app

    async def init_async():
        global _bot_app
        # بناء التطبيق
        _bot_app = Application.builder().token(TELEGRAM_TOKEN).build()
        _bot_app.add_handler(CommandHandler("start", start))
        _bot_app.add_handler(CallbackQueryHandler(button_callback))
        await _bot_app.initialize()

        # حذف أي webhook سابق
        await _bot_app.bot.delete_webhook(drop_pending_updates=True)
        logging.info("✅ Webhook القديم تم حذفه")

        # تعيين webhook جديد
        webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'ai-scalp-hunter.onrender.com')}/webhook"
        await _bot_app.bot.set_webhook(
            url=webhook_url,
            drop_pending_updates=True,
            allowed_updates=['message', 'callback_query']
        )
        logging.info(f"✅ Webhook جديد تم تعيينه: {webhook_url}")

    # تشغيل الدالة غير المتزامنة
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(init_async())
    finally:
        loop.close()

    _bot_initialized = True
    return _bot_app

# ====================================================
# 🚀 Flask Routes
# ====================================================
@app.route('/')
def home():
    return jsonify({
        "status": "running",
        "mode": "webhook",
        "bot": "@Mohammedjadim119988_bot",
        "message": "AI Scalp Hunter is alive!"
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/webhook', methods=['POST'])
def webhook():
    """استقبال التحديثات من تيليغرام"""
    global _bot_app

    if _bot_app is None:
        return jsonify({"error": "Bot not initialized"}), 503

    try:
        # تحويل الطلب إلى تحديث
        update_json = request.get_json(force=True)

        # معالجة التحديث بشكل متزامن
        async def process_update_async():
            update = Update.de_json(update_json, _bot_app.bot)
            await _bot_app.process_update(update)

        # استخدام asyncio.run() - آمن ويدير الـ loop بنفسه
        asyncio.run(process_update_async())

        return jsonify({"status": "ok"}), 200
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        return jsonify({"error": str(e)}), 500

# ====================================================
# 🏁 تشغيل التطبيق
# ====================================================
if __name__ == "__main__":
    # تهيئة البوت مرة واحدة فقط
    logging.info("🚀 Initializing bot...")
    init_bot_sync()

    # تشغيل Flask
    port = int(os.environ.get("PORT", 10000))
    logging.info(f"🚀 Starting Flask server on port {port}...")
    app.run(host="0.0.0.0", port=port)
