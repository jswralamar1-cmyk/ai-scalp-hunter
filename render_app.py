"""
render_app.py
AI Scalp Hunter - Render Compatible Version
Flask runs in background, Bot runs in main thread
"""

import threading
import logging
from flask import Flask, jsonify
from telegram_ui import TelegramUI

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)

# Bot status
bot_status = {"running": False, "started": False}


@app.route('/')
def home():
    """Home endpoint"""
    return jsonify({
        "status": "running",
        "message": "AI Scalp Hunter is alive! 🚀",
        "bot": "running" if bot_status["started"] else "starting",
        "version": "1.0.0"
    })


@app.route('/health')
def health():
    """Health check endpoint for Render"""
    return jsonify({
        "status": "healthy",
        "bot": "running" if bot_status["started"] else "starting"
    }), 200


@app.route('/status')
def status():
    """Detailed status endpoint"""
    return jsonify({
        "bot_started": bot_status["started"],
        "endpoints": {
            "/": "Home",
            "/health": "Health check",
            "/status": "Detailed status"
        }
    })


def run_flask():
    """Run Flask in background thread"""
    logger.info("🌐 Starting Flask server in background on port 10000...")
    app.run(host="0.0.0.0", port=10000, debug=False, use_reloader=False)


if __name__ == "__main__":
    logger.info("🚀 Initializing AI Scalp Hunter...")
    
    # Start Flask in background thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info("✅ Flask thread started")
    
    # Run bot in main thread
    logger.info("🤖 Starting Telegram Bot in main thread...")
    bot_status["started"] = True
    bot = TelegramUI()
    bot.run()
