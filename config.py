"""
config.py
AI Scalp Hunter - Configuration
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ====================================================
# 🔐 APIs
# ====================================================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TWELVEDATA_API_KEY = os.getenv("TWELVEDATA_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# ====================================================
# 💱 الأزواج (23 زوج)
# ====================================================
SYMBOLS = [
    "EUR/USD", "AUD/CHF", "USD/CAD", "GBP/JPY", "GBP/CHF",
    "USD/JPY", "AUD/NZD", "USD/CHF", "AUD/CAD", "AUD/JPY",
    "EUR/CHF", "AUD/USD", "CAD/CHF", "CHF/JPY", "EUR/CAD",
    "EUR/JPY", "GBP/AUD", "GBP/CAD", "EUR/AUD", "CAD/JPY",
    "NZD/USD", "NZD/JPY", "GBP/NZD"
]

# ====================================================
# ⏱️ الفريمات
# ====================================================
TIMEFRAMES = {
    "scalp_1m": "1min",
    "scalp_3m": "3min"
}

CANDLES_COUNT = 150

# ====================================================
# 📊 المؤشرات
# ====================================================
INDICATORS = {
    "rsi_period": 14,
    "rsi_overbought": 70,
    "rsi_oversold": 30,
    "macd_fast": 12,
    "macd_slow": 26,
    "macd_signal": 9,
    "ema_period": 100,
    "atr_period": 14
}

# ====================================================
# 🎯 VWAP
# ====================================================
VWAP_CONFIG = {
    "enabled": True,
    "fallback_to_twap": True,
    "twap_period": 20
}

# ====================================================
# 🤖 الذكاء الاصطناعي
# ====================================================
AI_TIMEOUT = 40
TOP_CANDIDATES_COUNT = 15

# ====================================================
# 🎯 الثقة
# ====================================================
CONFIDENCE = {
    "min_to_show": 65,
    "weights": {
        "score": 0.5,
        "momentum": 0.2,
        "pattern": 0.15,
        "structure": 0.1,
        "risk_penalty": -0.05
    },
    "levels": {
        "excellent": 80,
        "good": 70,
        "acceptable": 65
    }
}

# ====================================================
# 🛡️ عدم التكرار
# ====================================================
ANTI_REPEAT = {
    "enabled": True,
    "price_distance": 0.001,
    "time_window": 6,
    "max_score": 0.7
}

# ====================================================
# 🖼️ الشارت
# ====================================================
CHART = {
    "style": "nightclouds",
    "dark_mode": True,
    "figsize": (12, 8),
    "show_volume": True,
    "show_rsi": True,
    "temp_file": "temp_chart.png"
}

# ====================================================
# ⚡ الأداء
# ====================================================
PERFORMANCE = {
    "cache_ttl": 30,
    "max_concurrent": 10,
    "fallback_mode": True,
    "async_enabled": True
}
