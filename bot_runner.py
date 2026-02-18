"""
bot_runner.py
AI Scalp Hunter | Main Execution Engine
"""

import asyncio
import logging
from typing import List, Dict, Callable, Awaitable, Optional

from data_fetcher import DataFetcher
from market_analyzer import MarketAnalyzer
from score_engine import ScoreEngine
from ai_engine import AIEngine
from signal_builder import SignalBuilder
from chart_generator import ChartGenerator
from config import SYMBOLS, TOP_CANDIDATES_COUNT


async def run_scalp_analysis(
    progress_callback: Optional[Callable[[int], Awaitable[None]]] = None
) -> List[Dict]:
    if progress_callback:
        await progress_callback(1)

    fetcher = DataFetcher()
    analyzer = MarketAnalyzer(fetcher)
    score_engine = ScoreEngine()
    ai_engine = AIEngine()
    signal_builder = SignalBuilder()
    chart_gen = ChartGenerator()

    if progress_callback:
        await progress_callback(2)

    analysis_tasks = [analyzer.analyze_pair(symbol) for symbol in SYMBOLS]
    features_list = await asyncio.gather(*analysis_tasks)
    features_list = [f for f in features_list if f is not None]

    if not features_list:
        logging.error("No valid features found")
        return []

    if progress_callback:
        await progress_callback(3)

    scored = []
    for features in features_list:
        score_result = score_engine.evaluate(
            symbol=features["symbol"],
            df_1m=None,
            features=features
        )
        scored.append(score_result)

    top_15 = sorted(scored, key=lambda x: x["score"], reverse=True)[:TOP_CANDIDATES_COUNT]

    if progress_callback:
        await progress_callback(4)

    ai_result = await ai_engine.analyze(top_15)

    if "error" in ai_result:
        logging.error(f"AI Error: {ai_result['error']}")
        return []

    if progress_callback:
        await progress_callback(5)

    signals = []
    for pick in ai_result.get("top_2", []):
        score_snap = next(
            (s for s in scored if s["symbol"] == pick["pair"]),
            None
        )
        if not score_snap:
            continue

        signal = signal_builder.build_one(
            ai_pick=pick,
            score_snapshot=score_snap,
            timeframe_label="1m"
        )
        if signal:
            signals.append(signal)

    if progress_callback:
        await progress_callback(6)

    if progress_callback:
        await progress_callback(7)

    if signals:
        chart_tasks = [chart_gen.generate(signal) for signal in signals]
        chart_paths = await asyncio.gather(*chart_tasks)

        for i, path in enumerate(chart_paths):
            signals[i]["chart_path"] = path

        for signal in signals:
            signal_builder.commit_sent(signal)

    return signals
