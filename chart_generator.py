"""
chart_generator.py
AI Scalp Hunter | Chart Generator
"""

import asyncio
import pandas as pd
import mplfinance as mpf
from config import CHART
from data_fetcher import DataFetcher


class ChartGenerator:
    def __init__(self):
        self.fetcher = DataFetcher()
        self.style = mpf.make_mpf_style(
            base_mpf_style='nightclouds',
            rc={'font.size': 8}
        )

    async def generate(self, signal: dict) -> str:
        """Generate chart for signal"""
        try:
            payload = signal.get("chart_payload", {})
            pair = payload.get("pair", "EUR/USD")
            timeframe = payload.get("timeframe", "1m")
            
            # Fetch data
            df = await self.fetcher.fetch_candles(None, pair, "1min")
            
            if df is None or len(df) < 10:
                return None
            
            # Take last 50 candles
            df = df.tail(50)
            
            # Prepare chart
            entry_price = payload.get("entry_price", df['close'].iloc[-1])
            
            # Add horizontal line for entry price
            hlines = dict(hlines=[entry_price], colors=['orange'], linestyle='--', linewidths=1.5)
            
            # Generate chart
            filename = CHART["temp_file"]
            
            mpf.plot(
                df,
                type='candle',
                style=self.style,
                volume=CHART["show_volume"],
                figsize=CHART["figsize"],
                hlines=hlines,
                savefig=filename,
                tight_layout=True
            )
            
            return filename
            
        except Exception as e:
            print(f"Chart generation error: {e}")
            return None
