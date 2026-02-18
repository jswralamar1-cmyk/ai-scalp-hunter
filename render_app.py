"""
render_app.py
AI Scalp Hunter - Render Compatible Version
"""

import threading
import logging
import asyncio
from flask import Flask, jsonify
from telegram_ui import TelegramUI

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Bot status
bot_status = {"running": False, "error": None}


def run_bot():
    """Run Telegram bot in background thread"""
    global bot_status
    try:
        logger.info("🚀 Starting Telegram Bot in background...")
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        bot_status["running"] = True
        bot = TelegramUI()
        bot.run()
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")
        bot_status["running"] = False
        bot_status["error"] = str(e)


# Flask app
app = Flask(__name__)


@app.route('/')
def home():
    """Home endpoint"""
    return jsonify({
        "status": "running",
        "message": "AI Scalp Hunter is alive! 🚀",
        "bot": "active" if bot_status["running"] else "error",
        "version": "1.0.0"
    })


@app.route('/health')
def health():
    """Health check endpoint for Render"""
    if bot_status["running"]:
        return jsonify({"status": "healthy", "bot": "running"}), 200
    else:
        return jsonify({
            "status": "unhealthy",
            "bot": "stopped",
            "error": bot_status.get("error")
        }), 503


@app.route('/status')
def status():
    """Detailed status endpoint"""
    return jsonify({
        "bot_running": bot_status["running"],
        "bot_error": bot_status.get("error"),
        "endpoints": {
            "/": "Home",
            "/health": "Health check",
            "/status": "Detailed status"
        }
    })


# Start bot in background when app starts
logger.info("🔧 Initializing AI Scalp Hunter...")
bot_thread = threading.Thread(target=run_bot, daemon=True)
bot_thread.start()
logger.info("✅ Bot thread started")

if __name__ == "__main__":
    logger.info("🌐 Starting Flask server on port 10000...")
    app.run(host="0.0.0.0", port=10000)
