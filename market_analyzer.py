"""
market_analyzer.py
AI Scalp Hunter - Professional Market Analyzer
Calculates technical indicators and extracts features
"""

import pandas as pd
import numpy as np
import logging
from typing import Optional, Dict
from config import INDICATORS, VWAP_CONFIG

logger = logging.getLogger(__name__)


class MarketAnalyzer:
    """
    Analyzes market data and calculates technical indicators
    - RSI (Relative Strength Index)
    - MACD (Moving Average Convergence Divergence)
    - EMA (Exponential Moving Average)
    - ATR (Average True Range)
    - VWAP/TWAP (Volume/Time Weighted Average Price)
    - Momentum
    """
    
    def __init__(self, data_fetcher):
        self.data_fetcher = data_fetcher
    
    async def analyze_pair(self, symbol: str) -> Optional[Dict]:
        """
        Analyze a trading pair on multiple timeframes
        
        Args:
            symbol: Trading pair (e.g. "EUR/USD")
        
        Returns:
            Dictionary with features or None if failed
        """
        try:
            # Fetch data for both timeframes
            df_1m = await self.data_fetcher.fetch_candles(None, symbol, "1min")
            df_5m = await self.data_fetcher.fetch_candles(None, symbol, "5min")
            
            if df_1m is None or df_5m is None:
                logger.warning(f"Missing data for {symbol}")
                return None
            
            # Calculate indicators for both timeframes
            ind_1m = self._calculate_indicators(df_1m)
            ind_5m = self._calculate_indicators(df_5m)
            
            if ind_1m is None or ind_5m is None:
                logger.warning(f"Indicator calculation failed for {symbol}")
                return None
            
            # Extract and prepare features
            features = self._prepare_features(symbol, ind_1m, ind_5m)
            
            return features
        
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return None
    
    def _calculate_indicators(self, df: pd.DataFrame) -> Optional[pd.Series]:
        """
        Calculate all technical indicators for a DataFrame
        
        Args:
            df: OHLCV DataFrame
        
        Returns:
            Series with last row indicators or None if failed
        """
        try:
            df = df.copy()
            
            # RSI (Relative Strength Index)
            delta = df["close"].diff()
            gain = delta.clip(lower=0)
            loss = -delta.clip(upper=0)
            
            avg_gain = gain.rolling(window=INDICATORS["rsi_period"], min_periods=1).mean()
            avg_loss = loss.rolling(window=INDICATORS["rsi_period"], min_periods=1).mean()
            
            rs = avg_gain / (avg_loss + 1e-10)  # Avoid division by zero
            df["rsi"] = 100 - (100 / (1 + rs))
            
            # EMA (Exponential Moving Average)
            df["ema"] = df["close"].ewm(
                span=INDICATORS["ema_period"], 
                adjust=False, 
                min_periods=1
            ).mean()
            
            # MACD (Moving Average Convergence Divergence)
            ema_fast = df["close"].ewm(
                span=INDICATORS["macd_fast"], 
                adjust=False, 
                min_periods=1
            ).mean()
            
            ema_slow = df["close"].ewm(
                span=INDICATORS["macd_slow"], 
                adjust=False, 
                min_periods=1
            ).mean()
            
            df["macd"] = ema_fast - ema_slow
            df["macd_signal"] = df["macd"].ewm(
                span=INDICATORS["macd_signal"], 
                adjust=False, 
                min_periods=1
            ).mean()
            df["macd_hist"] = df["macd"] - df["macd_signal"]
            
            # ATR (Average True Range)
            high_low = df["high"] - df["low"]
            high_close = np.abs(df["high"] - df["close"].shift())
            low_close = np.abs(df["low"] - df["close"].shift())
            
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            df["atr"] = true_range.rolling(
                window=INDICATORS["atr_period"], 
                min_periods=1
            ).mean()
            
            # VWAP/TWAP
            if VWAP_CONFIG["enabled"]:
                if "volume" in df.columns and df["volume"].sum() > 0:
                    # VWAP (Volume Weighted Average Price)
                    typical_price = (df["high"] + df["low"] + df["close"]) / 3
                    df["vwap"] = (typical_price * df["volume"]).cumsum() / df["volume"].cumsum()
                elif VWAP_CONFIG["fallback_to_twap"]:
                    # TWAP (Time Weighted Average Price)
                    df["vwap"] = df["close"].rolling(
                        window=VWAP_CONFIG["twap_period"], 
                        min_periods=1
                    ).mean()
                else:
                    df["vwap"] = df["close"]
            else:
                df["vwap"] = df["close"]
            
            # Momentum Strength
            momentum = df["close"].pct_change().rolling(window=5, min_periods=1).mean()
            df["momentum_strength"] = momentum.abs()
            
            # Return last row
            return df.iloc[-1]
        
        except Exception as e:
            logger.error(f"Indicator calculation error: {e}")
            return None
    
    def _prepare_features(
        self, 
        symbol: str, 
        ind_1m: pd.Series, 
        ind_5m: pd.Series
    ) -> Dict:
        """
        Prepare features dictionary from indicators
        
        Args:
            symbol: Trading pair
            ind_1m: 1min indicators
            ind_5m: 5min indicators
        
        Returns:
            Dictionary with all features
        """
        current_price = float(ind_1m["close"])
        
        # Structure alignment: both timeframes agree on trend direction
        structure_alignment = (
            (ind_1m["close"] > ind_1m["ema"]) == (ind_5m["close"] > ind_5m["ema"])
        )
        
        # VWAP distance in ATR units
        atr_1m = float(ind_1m["atr"])
        vwap_distance = (
            (current_price - float(ind_1m["vwap"])) / atr_1m
            if atr_1m > 0
            else 0.0
        )
        
        return {
            "symbol": symbol,
            "price": current_price,
            
            # 1min indicators
            "rsi_1m": float(ind_1m["rsi"]),
            "macd_hist_1m": float(ind_1m["macd_hist"]),
            "ema_position_1m": bool(ind_1m["close"] > ind_1m["ema"]),
            "atr_1m": atr_1m,
            "vwap_distance": vwap_distance,
            "momentum_1m": float(ind_1m["momentum_strength"]),
            
            # 5min indicators
            "rsi_5m": float(ind_5m["rsi"]),
            "macd_hist_5m": float(ind_5m["macd_hist"]),
            "ema_position_5m": bool(ind_5m["close"] > ind_5m["ema"]),
            
            # Multi-timeframe
            "structure_alignment": bool(structure_alignment),
        }
