"""
data_fetcher.py
AI Scalp Hunter - Async Data Fetcher (TwelveData Fixed)
"""

import aiohttp
import asyncio
import time
import pandas as pd
from typing import Dict, Tuple, Optional
from config import TWELVEDATA_API_KEY, PERFORMANCE, CANDLES_COUNT

BASE_URL = "https://api.twelvedata.com/time_series"


class DataFetcher:
    def __init__(self):
        self.cache: Dict[Tuple[str, str], Dict] = {}
        self.cache_ttl = PERFORMANCE["cache_ttl"]
        self.semaphore = asyncio.Semaphore(PERFORMANCE["max_concurrent"])
        self.timeout = aiohttp.ClientTimeout(total=15)

    def _get_cached(self, symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
        key = (symbol, timeframe)
        if key in self.cache:
            cached_data = self.cache[key]
            if time.time() - cached_data["timestamp"] < self.cache_ttl:
                return cached_data["data"]
        return None

    def _set_cache(self, symbol: str, timeframe: str, data: pd.DataFrame):
        key = (symbol, timeframe)
        self.cache[key] = {
            "data": data,
            "timestamp": time.time()
        }

    async def fetch_candles(self, session: aiohttp.ClientSession,
                            symbol: str,
                            timeframe: str) -> Optional[pd.DataFrame]:

        # التحقق من الكاش أولاً
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

        headers = {
            "Accept-Encoding": "gzip, deflate"
        }

        async with self.semaphore:
            for attempt in range(3):
                try:
                    async with session.get(BASE_URL, params=params, headers=headers) as response:
                        if response.status != 200:
                            print(f"⚠️ TwelveData HTTP {response.status} for {symbol} {timeframe}")
                            if attempt == 2:
                                return None
                            await asyncio.sleep(2)
                            continue

                        # 🔥 قراءة الـ JSON
                        data = await response.json()

                        # 🔥 التحقق من وجود "values"
                        if data is None:
                            print(f"❌ TwelveData returned None for {symbol} {timeframe}")
                            return None

                        if "values" not in data:
                            print(f"⚠️ TwelveData: no 'values' in response for {symbol} {timeframe}")
                            print(f"   Response: {data}")
                            return None

                        # تحويل البيانات إلى DataFrame
                        df = pd.DataFrame(data["values"])
                        df = df.rename(columns={"datetime": "time"})

                        df["time"] = pd.to_datetime(df["time"])
                        df.set_index("time", inplace=True)

                        # تحويل الأعمدة إلى أرقام
                        numeric_cols = ["open", "high", "low", "close", "volume"]
                        for col in numeric_cols:
                            if col in df.columns:
                                df[col] = pd.to_numeric(df[col], errors="coerce")

                        df = df.sort_index()

                        # حفظ في الكاش
                        self._set_cache(symbol, timeframe, df)

                        return df

                except Exception as e:
                    print(f"❌ Attempt {attempt+1}/3 failed for {symbol} {timeframe}: {e}")
                    if attempt == 2:
                        return None
                    await asyncio.sleep(2)

        return None
