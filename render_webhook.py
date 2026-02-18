"""
render_webhook.py
AI Scalp Hunter - Professional Webhook Server for Render
Fixed: Event loop management for webhook requests
"""

import os
import asyncio
import logging
import threading
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from bot_runner import run_scalp_analysis
from config import TELEGRAM_TOKEN

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)

# Global bot application and event loop
telegram_app = None
bot_loop = None
bot_thread = None
user_locks = {}


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
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
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "hunt":
        await process_hunt(update, context)


async def process_hunt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process hunt request"""
    user_id = update.effective_user.id
    
    # Check if user already has analysis running
    if user_locks.get(user_id, False):
        await update.callback_query.answer("⚠️ التحليل جارٍ حالياً...", show_alert=True)
        return
    
    user_locks[user_id] = True
    progress_msg = None
    
    try:
        # Show initial progress
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
        
        # Run analysis
        async def progress_callback(stage: int):
            await update_progress(progress_msg, stage)
        
        signals = await run_scalp_analysis(progress_callback=progress_callback)
        
        # Send results
        if signals and len(signals) > 0:
            for signal in signals:
                chart_path = signal.get("chart_path")
                
                if chart_path and os.path.exists(chart_path):
                    with open(chart_path, "rb") as photo:
                        await context.bot.send_photo(
                            chat_id=update.effective_chat.id,
                            photo=photo,
                            caption=signal.get("message", "Signal"),
                            parse_mode="Markdown"
                        )
                else:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=signal.get("message", "Signal"),
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
        logger.exception("Error during analysis")
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
    """Update progress message"""
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


def run_bot_loop():
    """Run bot event loop in separate thread"""
    global bot_loop, telegram_app
    
    bot_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(bot_loop)
    
    async def init_and_run():
        global telegram_app
        
        # Build application
        telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # Add handlers
        telegram_app.add_handler(CommandHandler("start", start_command))
        telegram_app.add_handler(CallbackQueryHandler(button_callback))
        
        # Initialize
        await telegram_app.initialize()
        
        # Delete old webhook
        await telegram_app.bot.delete_webhook(drop_pending_updates=True)
        logger.info("Old webhook deleted")
        
        # Set new webhook
        webhook_url = f"https://ai-scalp-hunter.onrender.com/webhook"
        await telegram_app.bot.set_webhook(
            url=webhook_url,
            drop_pending_updates=True,
            allowed_updates=['message', 'callback_query']
        )
        logger.info(f"Webhook set to: {webhook_url}")
        logger.info("Bot initialized successfully")
        
        # Keep loop running
        while True:
            await asyncio.sleep(1)
    
    try:
        bot_loop.run_until_complete(init_and_run())
    except Exception as e:
        logger.error(f"Bot loop error: {e}")


def init_bot():
    """Initialize Telegram bot in separate thread"""
    global bot_thread
    
    if not TELEGRAM_TOKEN:
        raise ValueError("TELEGRAM_TOKEN is not set")
    
    logger.info("Starting bot thread...")
    bot_thread = threading.Thread(target=run_bot_loop, daemon=True)
    bot_thread.start()
    
    # Wait for bot to initialize
    import time
    for _ in range(10):
        if telegram_app is not None:
            break
        time.sleep(1)
    
    if telegram_app is None:
        raise RuntimeError("Bot failed to initialize")
    
    logger.info("Bot thread started successfully")


@app.route('/')
def home():
    """Home endpoint"""
    return jsonify({
        "status": "running",
        "mode": "webhook",
        "bot": "@Mohammedjadim119988_bot"
    })


@app.route('/health')
def health():
    """Health check for Render"""
    return jsonify({"status": "healthy"})


@app.route('/webhook', methods=['POST'])
def webhook():
    """Telegram webhook endpoint"""
    global telegram_app, bot_loop
    
    if telegram_app is None or bot_loop is None:
        return jsonify({"error": "Bot not initialized"}), 503
    
    try:
        # Get update JSON
        update_json = request.get_json(force=True)
        
        # Process update in bot's event loop
        async def process_update_async():
            update = Update.de_json(update_json, telegram_app.bot)
            await telegram_app.process_update(update)
        
        # Schedule in bot's event loop (don't create new loop!)
        future = asyncio.run_coroutine_threadsafe(process_update_async(), bot_loop)
        future.result(timeout=5)  # Wait max 5 seconds
        
        return jsonify({"ok": True})
    
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


if __name__ == "__main__":
    # Initialize bot
    init_bot()
    
    # Get port
    port = int(os.getenv("PORT", 10000))
    
    # Run Flask
    logger.info(f"Starting Flask server on port {port}...")
    app.run(host="0.0.0.0", port=port)
