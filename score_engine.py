"""
score_engine.py
AI Scalp Hunter - Professional Scoring Engine
Evaluates trading opportunities and assigns scores
"""

import pandas as pd
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ScoreEngine:
    """
    Scores trading opportunities based on:
    1. Indicator Base (40 points)
    2. Micro Structure (20 points)
    3. Pattern Recognition (20 points)
    4. VWAP Distance (10 points)
    5. ATR Filter (10 points)
    
    Total: 100 points
    """
    
    def __init__(self, data_fetcher):
        self.data_fetcher = data_fetcher
    
    async def evaluate(self, symbol: str, features: Dict) -> Optional[Dict]:
        """
        Evaluate a trading opportunity
        
        Args:
            symbol: Trading pair
            features: Market features dictionary
        
        Returns:
            Score result dictionary or None if failed
        """
        try:
            score = 0
            direction = None
            risk_flags = []
            
            # 1. Indicator Base (40 points)
            # EMA Position (15 points)
            if features["ema_position_1m"]:
                score += 15
                direction = "CALL"
            else:
                score += 15
                direction = "PUT"
            
            # MACD Histogram (10 points)
            if features["macd_hist_1m"] > 0:
                score += 10
            else:
                score += 10
            
            # RSI Range (10 points)
            if 30 <= features["rsi_1m"] <= 70:
                score += 10
            else:
                score += 5
            
            # Structure Alignment (5 points)
            if features["structure_alignment"]:
                score += 5
            
            # 2. Micro Structure (20 points)
            # Need df_1m for this
            df_1m = await self.data_fetcher.fetch_candles(None, symbol, "1min")
            if df_1m is not None and len(df_1m) >= 5:
                ms_score = self._micro_structure(df_1m)
                score += ms_score
            else:
                score += 5  # Default score if no data
            
            # 3. Pattern Score (20 points)
            if df_1m is not None and len(df_1m) >= 3:
                pattern_score = self._pattern_score(df_1m)
                score += pattern_score
            else:
                pattern_score = 5  # Default score
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
            
            # Cap at 100
            score = min(100, score)
            
            return {
                "symbol": symbol,
                "score": score,
                "direction": direction,
                "risk_flags": risk_flags,
                "features": features
            }
        
        except Exception as e:
            logger.error(f"Error evaluating {symbol}: {e}")
            return None
    
    def _micro_structure(self, df: pd.DataFrame) -> int:
        """
        Analyze micro structure (last 5 candles)
        
        Returns:
            20 points if strong trend, 5 otherwise
        """
        try:
            last_5 = df.tail(5)
            highs = last_5["high"].values
            lows = last_5["low"].values
            
            # Higher highs (bullish)
            higher_high = highs[-1] > highs[-2] > highs[-3]
            
            # Lower lows (bearish)
            lower_low = lows[-1] < lows[-2] < lows[-3]
            
            if higher_high or lower_low:
                return 20
            return 5
        
        except Exception as e:
            logger.error(f"Micro structure error: {e}")
            return 5
    
    def _pattern_score(self, df: pd.DataFrame) -> int:
        """
        Recognize candlestick patterns
        
        Returns:
            20 points for engulfing, 15 for acceleration, 5 otherwise
        """
        try:
            last_3 = df.tail(3)
            c1 = last_3.iloc[0]
            c2 = last_3.iloc[1]
            c3 = last_3.iloc[2]
            
            # Bullish Engulfing
            if c3["close"] > c3["open"] and c2["close"] < c2["open"]:
                if c3["close"] > c2["open"] and c3["open"] < c2["close"]:
                    return 20
            
            # Bearish Engulfing
            if c3["close"] < c3["open"] and c2["close"] > c2["open"]:
                if c3["open"] > c2["close"] and c3["close"] < c2["open"]:
                    return 20
            
            # Acceleration Pattern
            body1 = abs(c1["close"] - c1["open"])
            body2 = abs(c2["close"] - c2["open"])
            body3 = abs(c3["close"] - c3["open"])
            
            if body3 > body2 > body1:
                return 15
            
            return 5
        
        except Exception as e:
            logger.error(f"Pattern score error: {e}")
            return 5
