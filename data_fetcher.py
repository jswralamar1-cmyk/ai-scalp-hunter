"""
data_fetcher.py
AI Scalp Hunter | Async Data Fetcher
"""

import aiohttp
import asyncio
import time
import pandas as pd
from typing import Dict, Tuple
from config import TWELVEDATA_API_KEY, PERFORMANCE, CANDLES_COUNT

BASE_URL = "https://api.twelvedata.com/time_series"


class DataFetcher:
    def __init__(self):
        self.cache: Dict[Tuple[str, str], Dict] = {}
        self.cache_ttl = PERFORMANCE["cache_ttl"]
        self.semaphore = asyncio.Semaphore(PERFORMANCE["max_concurrent"])
        self.timeout = aiohttp.ClientTimeout(total=15)

    def _get_cached(self, symbol: str, timeframe: str):
        key = (symbol, timeframe)
        if key in self.cache:
            cached_data = self.cache[key]
            if time.time() - cached_data["timestamp"] < self.cache_ttl:
                return cached_data["data"]
        return None

    def _set_cache(self, symbol: str, timeframe: str, data):
        key = (symbol, timeframe)
        self.cache[key] = {
            "data": data,
            "timestamp": time.time()
        }

    async def fetch_candles(self, session: aiohttp.ClientSession,
                            symbol: str,
                            timeframe: str) -> pd.DataFrame | None:
        cached = self._get_cached(symbol, timeframe)
        if cached is not None:
            return cached

        params = {
            "symbol": symbol,
            "interval": timeframe,
            "outputsize": CANDLES_COUNT,
            "apikey": TWELVEDATA_API_KEY,
            "format": "JSON"
        }

        async with self.semaphore:
            for attempt in range(2):
                try:
                    # Disable brotli compression to avoid aiohttp compatibility issues
                    headers = {'Accept-Encoding': 'gzip, deflate'}
                    async with session.get(BASE_URL, params=params, headers=headers, timeout=self.timeout) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            raise Exception(f"HTTP {response.status}: {error_text}")

                        data = await response.json()
                        
                        # Check if data is None
                        if data is None:
                            raise Exception("API returned None")
                        
                        # Check for API error messages
                        if "status" in data and data["status"] == "error":
                            raise Exception(f"API Error: {data.get('message', 'Unknown error')}")
                        
                        if "values" not in data:
                            raise Exception(f"Invalid response (no values): {data}")

                        df = pd.DataFrame(data["values"])
                        df = df.rename(columns={"datetime": "time"})

                        df["time"] = pd.to_datetime(df["time"])
                        df.set_index("time", inplace=True)

                        # Convert numeric columns (forex pairs don't have volume)
                        numeric_cols = ["open", "high", "low", "close"]
                        for col in numeric_cols:
                            if col in df.columns:
                                df[col] = pd.to_numeric(df[col], errors="coerce")
                        
                        # Handle volume if present (stocks/crypto)
                        if "volume" in df.columns:
                            df["volume"] = pd.to_numeric(df["volume"], errors="coerce")

                        df = df.sort_index()
                        self._set_cache(symbol, timeframe, df)
                        return df

                except Exception as e:
                    if attempt == 1:
                        print(f"❌ Failed fetching {symbol} {timeframe}: {e}")
                        return None
                    await asyncio.sleep(1)

        return None
