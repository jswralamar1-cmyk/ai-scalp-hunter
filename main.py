"""
main.py
AI Scalp Hunter - Simple Polling Mode
Clean, stable, production-ready
"""

import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from bot_runner import BotRunner
from config import TELEGRAM_BOT_TOKEN

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class ScalpHunterBot:
    """
    Simple Telegram Bot with Polling
    No Flask, No Webhook, No Threads - Just clean polling
    """
    
    def __init__(self):
        if not TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN is not set")
        
        self.bot_runner = BotRunner()
        self.application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Register handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CallbackQueryHandler(self.button_handler))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /start command
        """
        keyboard = [
            [InlineKeyboardButton("🎯 اصطاد سكالبينغ", callback_data="hunt")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🤖 **AI Scalp Hunter**\n\n"
            "مرحباً! أنا بوت صيد فرص السكالبينغ.\n\n"
            "اضغط الزر أدناه لبدء التحليل...",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle button clicks
        """
        query = update.callback_query
        await query.answer()
        
        if query.data == "hunt":
            await self.hunt_scalp(query)
    
    async def hunt_scalp(self, query):
        """
        Run scalp hunting analysis
        """
        try:
            # Send progress message
            progress_msg = await query.message.reply_text(
                "🔍 **جاري التحليل...**\n\n"
                "⏳ يرجى الانتظار 20-40 ثانية...",
                parse_mode="Markdown"
            )
            
            # Run analysis
            result = await self.bot_runner.run_analysis()
            
            # Delete progress message
            await progress_msg.delete()
            
            # Send result
            if "error" in result:
                await query.message.reply_text(
                    f"❌ **خطأ:**\n\n{result['error']}",
                    parse_mode="Markdown"
                )
            else:
                # Send chart
                if result.get("chart_path"):
                    with open(result["chart_path"], "rb") as photo:
                        await query.message.reply_photo(
                            photo=photo,
                            caption=result["message"],
                            parse_mode="Markdown"
                        )
                else:
                    await query.message.reply_text(
                        result["message"],
                        parse_mode="Markdown"
                    )
        
        except Exception as e:
            logger.error(f"Hunt error: {e}")
            await query.message.reply_text(
                f"❌ **خطأ:**\n\n{str(e)}",
                parse_mode="Markdown"
            )
    
    def run(self):
        """
        Start bot with polling
        Simple, stable, production-ready
        """
        logger.info("🚀 Starting AI Scalp Hunter (Polling Mode)...")
        logger.info("Bot is running. Press Ctrl+C to stop.")
        
        # Run polling - that's it!
        self.application.run_polling(
            drop_pending_updates=True,
            allowed_updates=["message", "callback_query"]
        )


if __name__ == "__main__":
    bot = ScalpHunterBot()
    bot.run()
