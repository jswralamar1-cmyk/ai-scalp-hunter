"""
bot_runner.py
AI Scalp Hunter - Professional Main Execution Engine
Orchestrates the entire analysis pipeline
"""

import asyncio
import logging
from typing import List, Dict, Optional, Callable, Awaitable

from data_fetcher import DataFetcher
from market_analyzer import MarketAnalyzer
from score_engine import ScoreEngine
from ai_engine import AIEngine
from signal_builder import SignalBuilder
from chart_generator import ChartGenerator
from config import SYMBOLS, TOP_CANDIDATES_COUNT

logger = logging.getLogger(__name__)


async def run_scalp_analysis(
    progress_callback: Optional[Callable[[int], Awaitable[None]]] = None
) -> List[Dict]:
    """
    Main analysis pipeline
    
    Steps:
    1. Initialize all engines
    2. Analyze all pairs (parallel)
    3. Score all pairs
    4. Select top 15 candidates
    5. AI analysis to pick best 2
    6. Build signals
    7. Generate charts
    
    Args:
        progress_callback: Optional callback for progress updates (1-7)
    
    Returns:
        List of signal dictionaries
    """
    try:
        # Step 1: Initialize
        if progress_callback:
            await progress_callback(1)
        
        fetcher = DataFetcher()
        analyzer = MarketAnalyzer(fetcher)
        score_engine = ScoreEngine(fetcher)
        ai_engine = AIEngine()
        signal_builder = SignalBuilder()
        chart_gen = ChartGenerator()
        
        logger.info("All engines initialized")
        
        # Step 2: Analyze all pairs
        if progress_callback:
            await progress_callback(2)
        
        logger.info(f"Analyzing {len(SYMBOLS)} pairs...")
        analysis_tasks = [analyzer.analyze_pair(symbol) for symbol in SYMBOLS]
        features_list = await asyncio.gather(*analysis_tasks)
        features_list = [f for f in features_list if f is not None]
        
        if not features_list:
            logger.error("No valid features found")
            return []
        
        logger.info(f"Got features for {len(features_list)} pairs")
        
        # Step 3: Score all pairs
        if progress_callback:
            await progress_callback(3)
        
        logger.info("Scoring pairs...")
        score_tasks = [score_engine.evaluate(f["symbol"], f) for f in features_list]
        scored = await asyncio.gather(*score_tasks)
        scored = [s for s in scored if s is not None]
        
        if not scored:
            logger.error("No valid scores")
            return []
        
        logger.info(f"Scored {len(scored)} pairs")
        
        # Step 4: Select top 15
        top_15 = sorted(scored, key=lambda x: x["score"], reverse=True)[:TOP_CANDIDATES_COUNT]
        logger.info(f"Top 15 candidates selected (best score: {top_15[0]['score']})")
        
        # Step 5: AI analysis
        if progress_callback:
            await progress_callback(4)
        
        logger.info("Running AI analysis...")
        ai_result = await ai_engine.analyze(top_15)
        
        # Check if AI returned None
        if ai_result is None:
            logger.error("AI returned None (unexpected)")
            return []
        
        if "error" in ai_result:
            logger.error(f"AI Error: {ai_result['error']}")
            return []
        
        if "top_2" not in ai_result or len(ai_result["top_2"]) == 0:
            logger.error("AI returned no picks")
            return []
        
        logger.info(f"AI selected {len(ai_result['top_2'])} opportunities")
        
        # Step 6: Build signals
        if progress_callback:
            await progress_callback(5)
        
        signals = []
        for pick in ai_result["top_2"]:
            # Find matching score snapshot
            score_snap = next(
                (s for s in scored if s["symbol"] == pick["pair"]),
                None
            )
            
            if not score_snap:
                logger.warning(f"No score snapshot for {pick['pair']}")
                continue
            
            # Build signal
            signal = signal_builder.build_one(
                ai_pick=pick,
                score_snapshot=score_snap,
                timeframe_label="1m"
            )
            
            if signal:
                signals.append(signal)
                logger.info(f"Signal built: {signal['symbol']} {signal['direction']}")
        
        if not signals:
            logger.warning("No signals built")
            return []
        
        # Step 7: Generate charts
        if progress_callback:
            await progress_callback(6)
        
        logger.info("Generating charts...")
        chart_tasks = [chart_gen.generate(signal) for signal in signals]
        chart_paths = await asyncio.gather(*chart_tasks)
        
        for i, path in enumerate(chart_paths):
            signals[i]["chart_path"] = path
            logger.info(f"Chart generated: {path}")
        
        # Commit signals
        for signal in signals:
            signal_builder.commit_sent(signal)
        
        if progress_callback:
            await progress_callback(7)
        
        logger.info(f"Analysis complete: {len(signals)} signals")
        return signals
    
    except Exception as e:
        logger.error(f"Analysis pipeline error: {e}")
        import traceback
        traceback.print_exc()
        return []
