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
            for attempt in range(3):  # 🔥 3 محاولات
                try:
                    # Disable brotli compression to avoid aiohttp compatibility issues
                    headers = {'Accept-Encoding': 'gzip, deflate'}
                    async with session.get(BASE_URL, params=params, headers=headers, timeout=self.timeout) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            print(f"⚠️ TwelveData Error {response.status}: {error_text[:200]}")
                            if attempt == 2:
                                return None
                            await asyncio.sleep(2)
                            continue

                        try:
                            data = await response.json()
                        except Exception as json_err:
                            print(f"⚠️ JSON parse error for {symbol}: {json_err}")
                            if attempt == 2:
                                return None
                            await asyncio.sleep(2)
                            continue
                        
                        # Check if data is None
                        if data is None:
                            print(f"⚠️ TwelveData returned None for {symbol}")
                            if attempt == 2:
                                return None
                            await asyncio.sleep(2)
                            continue
                        
                        # Check for API error messages
                        if isinstance(data, dict) and "status" in data and data["status"] == "error":
                            error_msg = data.get('message', 'Unknown error')
                            error_code = data.get('code', 'unknown')
                            print(f"⚠️ TwelveData API error for {symbol}: {error_code} - {error_msg}")
                            if attempt == 2:
                                return None
                            await asyncio.sleep(2)
                            continue
                        
                        # 🔥 التحقق من وجود "values"
                        if "values" not in data:
                            print(f"⚠️ TwelveData: no 'values' in response for {symbol}: {data.get('status', 'unknown')}")
                            if "code" in data:
                                print(f"⚠️ TwelveData error code: {data['code']} - {data.get('message', '')}")
                            if attempt == 2:
                                return None
                            await asyncio.sleep(2)
                            continue

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
                    print(f"❌ Attempt {attempt+1}/3 failed for {symbol} {timeframe}: {e}")
                    if attempt == 2:
                        print(f"❌ Failed fetching {symbol} {timeframe} after 3 attempts")
                        return None
                    await asyncio.sleep(2)

        return None
