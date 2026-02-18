"""
render_webhook.py
AI Scalp Hunter - Webhook Mode for Render
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

# ====================================================
# 🔥 إيقاف Polling نهائياً
# ====================================================
async def force_delete_webhook():
    """فرض حذف webhook وإيقاف أي polling عالق"""
    try:
        bot = Bot(token=TELEGRAM_TOKEN)
        await bot.delete_webhook(drop_pending_updates=True)
        logging.info("✅ Webhook deleted, polling stopped")
    except Exception as e:
        logging.warning(f"⚠️ Could not delete webhook: {e}")

# تنفيذ فوراً قبل بدء Flask
try:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(force_delete_webhook())
    loop.close()
except Exception as e:
    logging.warning(f"⚠️ force_delete_webhook failed: {e}")

# Flask app
app = Flask(__name__)

# متغيرات عامة
application = None
user_locks = {}

# ====================================================
# 🚀 أوامر البوت
# ====================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رسالة الترحيب مع الزر"""
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
    """معالجة ضغط الزر"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "hunt":
        await process_hunt(update, context)

# ====================================================
# 🎯 معالجة التحليل
# ====================================================
async def process_hunt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تنفيذ عملية الصيد"""
    user_id = update.effective_user.id
    
    # منع double-click
    if user_locks.get(user_id, False):
        await update.callback_query.answer("⚠️ التحليل جارٍ حالياً...", show_alert=True)
        return
    
    user_locks[user_id] = True
    progress_msg = None
    
    try:
        # رسالة التقدم
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
        
        # تعريف دالة تحديث التقدم
        async def update_progress(stage: int):
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
                await progress_msg.edit_text(text, parse_mode="Markdown")
            except:
                pass
            
            await asyncio.sleep(0.4)
        
        # تشغيل التحليل
        result = await run_scalp_analysis(
            progress_callback=update_progress
        )
        
        # إرسال النتائج
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
            text="❌ حدث خطأ أثناء التحليل.\nحاول مجدداً بعد قليل."
        )
    finally:
        user_locks[user_id] = False
        if progress_msg:
            try:
                await progress_msg.delete()
            except:
                pass

# ====================================================
# 🌐 Webhook Setup
# ====================================================
async def setup_webhook():
    """إعداد webhook للبوت"""
    global application
    
    # بناء التطبيق بدون updater
    application = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .updater(None)
        .build()
    )
    
    # إضافة handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # تهيئة التطبيق
    await application.initialize()
    
    # تعيين webhook
    render_url = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
    if not render_url:
        # للاختبار المحلي
        webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'ai-scalp-hunter.onrender.com')}/webhook"
    else:
        webhook_url = f"https://{render_url}/webhook"
    
    await application.bot.set_webhook(
        url=webhook_url,
        drop_pending_updates=True,
        allowed_updates=['message', 'callback_query']
    )
    
    logging.info(f"✅ Webhook set to {webhook_url}")
    return application

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
    global application
    
    if application is None:
        return jsonify({"error": "Bot not initialized"}), 503
    
    try:
        # تحويل الطلب إلى تحديث
        update_json = request.get_json(force=True)
        update = Update.de_json(update_json, application.bot)
        
        # معالجة التحديث
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(application.process_update(update))
        loop.close()
        
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        return jsonify({"error": str(e)}), 500

# ====================================================
# 🏁 تشغيل التطبيق
# ====================================================
if __name__ == "__main__":
    # إعداد webhook
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        application = loop.run_until_complete(setup_webhook())
        logging.info("🚀 Starting Flask server...")
        port = int(os.environ.get("PORT", 10000))
        app.run(host="0.0.0.0", port=port)
    except KeyboardInterrupt:
        pass
    finally:
        if application:
            loop.run_until_complete(application.shutdown())
        loop.close()
