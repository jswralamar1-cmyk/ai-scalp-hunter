"""
telegram_ui.py
AI Scalp Hunter - Clean Polling-Only Telegram Interface
No Flask, No Webhook, No Threading - Pure Async Polling
"""

import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from bot_runner import run_scalp_analysis
from config import TELEGRAM_TOKEN

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class TelegramUI:
    """Clean Telegram UI with Polling only"""
    
    def __init__(self):
        """Initialize bot application"""
        self.app = Application.builder().token(TELEGRAM_TOKEN).build()
        self._setup_handlers()
        logger.info("TelegramUI initialized (Polling mode)")
    
    def _setup_handlers(self):
        """Register command and message handlers"""
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        logger.info("Handlers registered")
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        keyboard = [["🎯 اصطاد سكالبينغ"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        welcome_text = (
            "🤖 *AI Scalp Hunter*\n\n"
            "مرحباً! أنا بوت تحليل الفوركس الذكي.\n\n"
            "📊 أحلل 25 زوج عملة\n"
            "🎯 أختار أفضل فرصتين\n"
            "📈 أرسل لك إشارات دقيقة مع الرسوم البيانية\n\n"
            "اضغط الزر أدناه للبدء 👇"
        )
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        logger.info(f"User {update.effective_user.id} started bot")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button presses and messages"""
        text = update.message.text
        user_id = update.effective_user.id
        
        if text == "🎯 اصطاد سكالبينغ":
            await self._handle_hunt_request(update, context)
        else:
            await update.message.reply_text("استخدم الزر أدناه للبدء 👇")
    
    async def _handle_hunt_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle scalping hunt request"""
        user_id = update.effective_user.id
        logger.info(f"User {user_id} requested scalp hunt")
        
        # Send progress message
        progress_msg = await update.message.reply_text(
            "🔍 جاري تحليل الأسواق...\n"
            "⏳ قد يستغرق 30-60 ثانية"
        )
        
        try:
            # Progress callback
            async def update_progress(step: int):
                steps = {
                    1: "🔧 تهيئة المحركات...",
                    2: "📊 تحليل 25 زوج عملة...",
                    3: "🎯 تقييم الفرص...",
                    4: "🤖 تحليل الذكاء الاصطناعي...",
                    5: "📝 بناء الإشارات...",
                    6: "📈 إنشاء الرسوم البيانية...",
                    7: "✅ اكتمل!"
                }
                if step in steps:
                    await progress_msg.edit_text(f"🔍 {steps[step]}")
            
            # Run analysis (await directly - we're already in async handler)
            signals = await run_scalp_analysis(progress_callback=update_progress)
            
            if not signals:
                await progress_msg.edit_text(
                    "❌ لم أجد فرص مناسبة حالياً.\n"
                    "جرب مرة أخرى بعد قليل."
                )
                return
            
            # Delete progress message
            await progress_msg.delete()
            
            # Send signals
            for signal in signals:
                await self._send_signal(update, signal)
            
            logger.info(f"Sent {len(signals)} signals to user {user_id}")
        
        except Exception as e:
            logger.error(f"Error in hunt request: {e}")
            import traceback
            traceback.print_exc()
            await progress_msg.edit_text(
                "❌ حدث خطأ أثناء التحليل.\n"
                "يرجى المحاولة مرة أخرى."
            )
    
    async def _send_signal(self, update: Update, signal: dict):
        """Send a single trading signal with chart"""
        try:
            # Build signal message
            direction_emoji = "🟢" if signal["direction"] == "BUY" else "🔴"
            
            message = (
                f"{direction_emoji} *إشارة {signal['direction']}*\n\n"
                f"💱 الزوج: `{signal['symbol']}`\n"
                f"📍 الدخول: `{signal['entry_price']:.5f}`\n"
                f"🎯 الهدف: `{signal['tp']:.5f}`\n"
                f"🛑 الإيقاف: `{signal['sl']:.5f}`\n"
                f"⏱ الصلاحية: {signal['expiry_minutes']} دقيقة\n\n"
                f"📊 النقاط: {signal['score']}/100\n"
                f"🔥 الثقة: {signal['confidence']}\n\n"
                f"💡 *التحليل:*\n{signal['reasoning']}"
            )
            
            # Send chart if available
            if signal.get("chart_path"):
                with open(signal["chart_path"], "rb") as chart_file:
                    await update.message.reply_photo(
                        photo=chart_file,
                        caption=message,
                        parse_mode='Markdown'
                    )
            else:
                await update.message.reply_text(message, parse_mode='Markdown')
        
        except Exception as e:
            logger.error(f"Error sending signal: {e}")
            await update.message.reply_text(
                f"⚠️ خطأ في إرسال إشارة {signal['symbol']}"
            )
    
    def run(self):
        """Start the bot with polling"""
        logger.info("🚀 Starting bot in POLLING mode...")
        logger.info("No Flask, No Webhook, No Threading - Clean Async")
        
        # Run polling (this blocks until stopped)
        self.app.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )


if __name__ == "__main__":
    print("🚀 AI Scalp Hunter - Polling Mode")
    print("=" * 50)
    ui = TelegramUI()
    ui.run()
