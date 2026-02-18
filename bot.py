"""
bot.py
AI Scalp Hunter - Main Entry Point
"""

import asyncio
import logging
from telegram_ui import TelegramUI

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

if __name__ == "__main__":
    print("🚀 Starting AI Scalp Hunter...")
    bot = TelegramUI()
    bot.run()
