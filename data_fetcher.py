"""
data_fetcher.py
AI Scalp Hunter - Professional Data Fetcher
Rewritten for stability and clarity
"""

import aiohttp
import asyncio
import pandas as pd
import logging
from typing import Optional
from config import TWELVEDATA_API_KEY, CANDLES_COUNT

logger = logging.getLogger(__name__)


class DataFetcher:
    """
    Fetches OHLCV data from TwelveData API
    - Uses semaphore to limit concurrent requests
    - Handles errors gracefully
    - Returns clean DataFrame or None
    """
    
    BASE_URL = "https://api.twelvedata.com/time_series"
    
    def __init__(self, max_concurrent: int = 10):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def fetch_candles(
        self, 
        session,  # Ignored, kept for compatibility
        symbol: str, 
        timeframe: str
    ) -> Optional[pd.DataFrame]:
        """
        Fetch candles for a symbol and timeframe
        
        Args:
            session: Ignored (kept for backward compatibility)
            symbol: Trading pair (e.g. "EUR/USD")
            timeframe: Interval (e.g. "1min", "5min")
        
        Returns:
            DataFrame with OHLCV data or None if failed
        """
        async with self.semaphore:
            try:
                # Create fresh session for each request
                async with aiohttp.ClientSession() as new_session:
                    params = {
                        "symbol": symbol,
                        "interval": timeframe,
                        "outputsize": CANDLES_COUNT,
                        "apikey": TWELVEDATA_API_KEY,
                    }
                    
                    headers = {
                        "Accept-Encoding": "gzip, deflate"  # Disable brotli
                    }
                    
                    async with new_session.get(
                        self.BASE_URL, 
                        params=params, 
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=15)
                    ) as resp:
                        
                        # Check HTTP status
                        if resp.status != 200:
                            logger.warning(f"HTTP {resp.status} for {symbol} {timeframe}")
                            return None
                        
                        # Parse JSON
                        try:
                            data = await resp.json()
                        except Exception as e:
                            logger.error(f"JSON parse error for {symbol}: {e}")
                            return None
                        
                        # Check for API errors
                        if "status" in data and data["status"] == "error":
                            logger.warning(f"API error for {symbol}: {data.get('message', 'Unknown')}")
                            return None
                        
                        # Check for values
                        if "values" not in data or not data["values"]:
                            logger.warning(f"No values for {symbol} {timeframe}")
                            return None
                        
                        # Build DataFrame
                        df = pd.DataFrame(data["values"])
                        
                        # Rename datetime column
                        df = df.rename(columns={"datetime": "time"})
                        
                        # Convert time to datetime
                        df["time"] = pd.to_datetime(df["time"])
                        df = df.set_index("time")
                        
                        # Convert OHLCV to numeric
                        for col in ["open", "high", "low", "close"]:
                            if col in df.columns:
                                df[col] = pd.to_numeric(df[col], errors="coerce")
                        
                        # Volume might be missing for forex
                        if "volume" in df.columns:
                            df["volume"] = pd.to_numeric(df["volume"], errors="coerce")
                        else:
                            df["volume"] = 0.0
                        
                        # Sort by time (oldest first)
                        df = df.sort_index()
                        
                        # Drop rows with NaN in OHLC
                        df = df.dropna(subset=["open", "high", "low", "close"])
                        
                        if len(df) < 50:
                            logger.warning(f"Insufficient data for {symbol} {timeframe}: {len(df)} candles")
                            return None
                        
                        return df
            
            except asyncio.TimeoutError:
                logger.error(f"Timeout fetching {symbol} {timeframe}")
                return None
            
            except Exception as e:
                logger.error(f"Unexpected error fetching {symbol} {timeframe}: {e}")
                return None
