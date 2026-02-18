"""
data_fetcher.py
AI Scalp Hunter - Async Data Fetcher (Compatible)
"""

import aiohttp
import asyncio
import pandas as pd
from typing import Optional
from config import TWELVEDATA_API_KEY, CANDLES_COUNT

BASE_URL = "https://api.twelvedata.com/time_series"


class DataFetcher:
    def __init__(self):
        self.semaphore = asyncio.Semaphore(10)

    async def fetch_candles(self, session, symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
        """
        تجلب بيانات الشموع لزوج معين
        ملاحظة: session تُهمل (ننشئ session خاص داخل الدالة)
        """
        # 🔥 نحول timeframe من "1min" إلى "1min" (هو نفسه)
        interval = timeframe

        params = {
            "symbol": symbol,
            "interval": interval,
            "outputsize": CANDLES_COUNT,
            "apikey": TWELVEDATA_API_KEY,
        }

        headers = {
            "Accept-Encoding": "gzip, deflate"
        }

        async with self.semaphore:
            try:
                # 🔥 ننشئ session خاص بنا بدلاً من استخدام session الوارد
                async with aiohttp.ClientSession() as new_session:
                    async with new_session.get(BASE_URL, params=params, headers=headers) as resp:
                        if resp.status != 200:
                            print(f"⚠️ HTTP {resp.status} for {symbol} {interval}")
                            return None

                        data = await resp.json()

                        if "values" not in data:
                            print(f"⚠️ No 'values' in response for {symbol} {interval}")
                            return None

                        df = pd.DataFrame(data["values"])
                        df = df.rename(columns={"datetime": "time"})
                        df["time"] = pd.to_datetime(df["time"])
                        df.set_index("time", inplace=True)

                        for col in ["open", "high", "low", "close", "volume"]:
                            if col in df.columns:
                                df[col] = pd.to_numeric(df[col], errors="coerce")

                        return df.sort_index()

            except Exception as e:
                print(f"❌ Error fetching {symbol} {interval}: {e}")
                return None
