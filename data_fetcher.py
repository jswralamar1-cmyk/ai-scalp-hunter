"""
data_fetcher.py
AI Scalp Hunter - Async Data Fetcher (Simplified)
"""

import aiohttp
import asyncio
import pandas as pd
from typing import Optional
from config import TWELVEDATA_API_KEY, CANDLES_COUNT

BASE_URL = "https://api.twelvedata.com/time_series"


class DataFetcher:
    def __init__(self):
        self.semaphore = asyncio.Semaphore(10)  # 10 طلبات متوازية

    async def fetch_candles(self, session_or_symbol, symbol_or_interval=None, interval=None) -> Optional[pd.DataFrame]:
        """
        تجلب بيانات الشموع لزوج معين
        يدعم كلا الاستدعاءين:
        - fetch_candles(symbol, interval)
        - fetch_candles(session, symbol, interval)  # session يتم تجاهله
        """
        # 🔥 Backward compatibility
        if interval is None:
            # الاستدعاء الجديد: fetch_candles(symbol, interval)
            symbol = session_or_symbol
            interval = symbol_or_interval
        else:
            # الاستدعاء القديم: fetch_candles(session, symbol, interval)
            symbol = symbol_or_interval
        params = {
            "symbol": symbol,
            "interval": interval,
            "outputsize": CANDLES_COUNT,
            "apikey": TWELVEDATA_API_KEY,
        }

        headers = {
            "Accept-Encoding": "gzip, deflate"  # 🔥 منع Brotli
        }

        async with self.semaphore:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(BASE_URL, params=params, headers=headers) as resp:
                        if resp.status != 200:
                            print(f"⚠️ HTTP {resp.status} for {symbol} {interval}")
                            return None

                        data = await resp.json()

                        # 🔥 التحقق من وجود values
                        if "values" not in data:
                            print(f"⚠️ No 'values' in response for {symbol} {interval}")
                            return None

                        # تحويل إلى DataFrame
                        df = pd.DataFrame(data["values"])
                        df = df.rename(columns={"datetime": "time"})
                        df["time"] = pd.to_datetime(df["time"])
                        df.set_index("time", inplace=True)

                        # تحويل الأعمدة إلى أرقام
                        for col in ["open", "high", "low", "close", "volume"]:
                            if col in df.columns:
                                df[col] = pd.to_numeric(df[col], errors="coerce")

                        return df.sort_index()

            except Exception as e:
                print(f"❌ Error fetching {symbol} {interval}: {e}")
                return None
