"""
market_analyzer.py
AI Scalp Hunter | Market Analysis
"""

import pandas as pd
import numpy as np
from config import INDICATORS, VWAP_CONFIG


class MarketAnalyzer:
    def __init__(self, data_fetcher):
        self.data_fetcher = data_fetcher

    async def analyze_pair(self, symbol: str) -> dict | None:
        df_1m = await self.data_fetcher.fetch_candles(
            None, symbol, "1min"
        )
        df_3m = await self.data_fetcher.fetch_candles(
            None, symbol, "3min"
        )

        if df_1m is None or df_3m is None:
            return None

        ind_1m = self._calculate_indicators(df_1m)
        ind_3m = self._calculate_indicators(df_3m)

        return self._prepare_features(symbol, ind_1m, ind_3m)

    def _calculate_indicators(self, df: pd.DataFrame) -> dict:
        df = df.copy()

        # RSI
        delta = df["close"].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.rolling(INDICATORS["rsi_period"]).mean()
        avg_loss = loss.rolling(INDICATORS["rsi_period"]).mean()

        rs = avg_gain / avg_loss
        df["rsi"] = 100 - (100 / (1 + rs))

        # EMA
        df["ema"] = df["close"].ewm(span=INDICATORS["ema_period"], adjust=False).mean()

        # MACD
        ema_fast = df["close"].ewm(span=INDICATORS["macd_fast"], adjust=False).mean()
        ema_slow = df["close"].ewm(span=INDICATORS["macd_slow"], adjust=False).mean()
        df["macd"] = ema_fast - ema_slow
        df["macd_signal"] = df["macd"].ewm(span=INDICATORS["macd_signal"], adjust=False).mean()
        df["macd_hist"] = df["macd"] - df["macd_signal"]

        # ATR
        high_low = df["high"] - df["low"]
        high_close = np.abs(df["high"] - df["close"].shift())
        low_close = np.abs(df["low"] - df["close"].shift())
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df["atr"] = true_range.rolling(INDICATORS["atr_period"]).mean()

        # VWAP/TWAP
        if VWAP_CONFIG["enabled"]:
            if "volume" in df.columns and df["volume"].sum() > 0:
                typical_price = (df["high"] + df["low"] + df["close"]) / 3
                df["vwap"] = (typical_price * df["volume"]).cumsum() / df["volume"].cumsum()
            elif VWAP_CONFIG["fallback_to_twap"]:
                df["vwap"] = df["close"].rolling(VWAP_CONFIG["twap_period"]).mean()
            else:
                df["vwap"] = df["close"]

        # Momentum
        momentum = df["close"].pct_change().rolling(5).mean()
        df["momentum_strength"] = momentum.abs()

        return df.iloc[-1]

    def _prepare_features(self, symbol, ind_1m, ind_3m) -> dict:
        current_price = ind_1m["close"]

        structure_alignment = (
            (ind_1m["close"] > ind_1m["ema"])
            == (ind_3m["close"] > ind_3m["ema"])
        )

        vwap_distance = (
            (current_price - ind_1m["vwap"]) / ind_1m["atr"]
            if ind_1m["atr"] != 0
            else 0
        )

        return {
            "symbol": symbol,
            "price": float(current_price),
            "rsi_1m": float(ind_1m["rsi"]),
            "macd_hist_1m": float(ind_1m["macd_hist"]),
            "ema_position_1m": bool(ind_1m["close"] > ind_1m["ema"]),
            "atr_1m": float(ind_1m["atr"]),
            "vwap_distance": float(vwap_distance),
            "momentum_1m": float(ind_1m["momentum_strength"]),
            "rsi_3m": float(ind_3m["rsi"]),
            "macd_hist_3m": float(ind_3m["macd_hist"]),
            "ema_position_3m": bool(ind_3m["close"] > ind_3m["ema"]),
            "structure_alignment": bool(structure_alignment),
        }
