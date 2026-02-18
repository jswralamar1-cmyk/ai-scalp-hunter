"""
score_engine.py
AI Scalp Hunter | Scoring Engine
"""

import pandas as pd
from config import TOP_CANDIDATES_COUNT


class ScoreEngine:
    def evaluate(self, symbol: str, df_1m: pd.DataFrame, features: dict):
        score = 0
        direction = None
        risk_flags = []

        # 1. Indicator Base (40 points)
        if features["ema_position_1m"]:
            score += 15
            direction = "CALL"
        else:
            score += 15
            direction = "PUT"

        if features["macd_hist_1m"] > 0:
            score += 10
        else:
            score += 10

        if 30 <= features["rsi_1m"] <= 70:
            score += 10
        else:
            score += 5

        if features["structure_alignment"]:
            score += 5

        # 2. Micro Structure (20 points)
        ms_score = self._micro_structure(df_1m)
        score += ms_score

        # 3. Pattern Score (20 points)
        pattern_score = self._pattern_score(df_1m)
        score += pattern_score

        # 4. VWAP Distance (10 points)
        vwap_dist = abs(features["vwap_distance"])
        if vwap_dist < 0.5:
            score += 10
        elif vwap_dist < 1.0:
            score += 5

        # 5. ATR Filter (10 points)
        if features["atr_1m"] > 0:
            score += 10

        # Risk Flags
        if features["atr_1m"] < 0.0002:
            risk_flags.append("low_volatility")
        if not features["structure_alignment"]:
            risk_flags.append("structure_misaligned")
        if pattern_score == 0:
            risk_flags.append("no_clear_pattern")

        score = min(100, score)

        return {
            "symbol": symbol,
            "score": score,
            "direction": direction,
            "risk_flags": risk_flags,
            "features": features
        }

    def _micro_structure(self, df: pd.DataFrame) -> int:
        if len(df) < 5:
            return 0

        last_5 = df.tail(5)
        highs = last_5["high"].values
        lows = last_5["low"].values

        higher_high = highs[-1] > highs[-2] > highs[-3]
        lower_low = lows[-1] < lows[-2] < lows[-3]

        if higher_high or lower_low:
            return 20
        return 5

    def _pattern_score(self, df: pd.DataFrame) -> int:
        if len(df) < 3:
            return 0

        last_3 = df.tail(3)
        c1 = last_3.iloc[0]
        c2 = last_3.iloc[1]
        c3 = last_3.iloc[2]

        # Engulfing
        if c3["close"] > c3["open"] and c2["close"] < c2["open"]:
            if c3["close"] > c2["open"] and c3["open"] < c2["close"]:
                return 20
        if c3["close"] < c3["open"] and c2["close"] > c2["open"]:
            if c3["open"] > c2["close"] and c3["close"] < c2["open"]:
                return 20

        # Acceleration
        body1 = abs(c1["close"] - c1["open"])
        body2 = abs(c2["close"] - c2["open"])
        body3 = abs(c3["close"] - c3["open"])

        if body3 > body2 > body1:
            return 15

        return 5
