"""
test_rewrite.py
Test the rewritten modules
"""

import asyncio
import sys
from data_fetcher import DataFetcher
from market_analyzer import MarketAnalyzer
from score_engine import ScoreEngine


async def test_data_fetcher():
    print("=" * 60)
    print("Testing DataFetcher...")
    print("=" * 60)
    
    fetcher = DataFetcher()
    
    # Test 1min
    df_1m = await fetcher.fetch_candles(None, "EUR/USD", "1min")
    if df_1m is not None:
        print(f"✅ EUR/USD 1min: {len(df_1m)} candles")
        print(f"   Columns: {list(df_1m.columns)}")
        print(f"   Last close: {df_1m.iloc[-1]['close']}")
    else:
        print("❌ EUR/USD 1min failed")
        return False
    
    # Test 5min
    df_5m = await fetcher.fetch_candles(None, "GBP/JPY", "5min")
    if df_5m is not None:
        print(f"✅ GBP/JPY 5min: {len(df_5m)} candles")
    else:
        print("❌ GBP/JPY 5min failed")
        return False
    
    print()
    return True


async def test_market_analyzer():
    print("=" * 60)
    print("Testing MarketAnalyzer...")
    print("=" * 60)
    
    fetcher = DataFetcher()
    analyzer = MarketAnalyzer(fetcher)
    
    features = await analyzer.analyze_pair("EUR/USD")
    
    if features is None:
        print("❌ MarketAnalyzer failed")
        return False
    
    print(f"✅ EUR/USD features:")
    print(f"   Symbol: {features['symbol']}")
    print(f"   Price: {features['price']}")
    print(f"   RSI 1m: {features['rsi_1m']:.2f}")
    print(f"   RSI 5m: {features['rsi_5m']:.2f}")
    print(f"   MACD Hist 1m: {features['macd_hist_1m']:.6f}")
    print(f"   EMA Position 1m: {features['ema_position_1m']}")
    print(f"   Structure Alignment: {features['structure_alignment']}")
    print(f"   ATR 1m: {features['atr_1m']:.6f}")
    print(f"   VWAP Distance: {features['vwap_distance']:.2f}")
    
    print()
    return True


async def test_score_engine():
    print("=" * 60)
    print("Testing ScoreEngine...")
    print("=" * 60)
    
    fetcher = DataFetcher()
    analyzer = MarketAnalyzer(fetcher)
    score_engine = ScoreEngine(fetcher)
    
    features = await analyzer.analyze_pair("GBP/JPY")
    
    if features is None:
        print("❌ Features failed")
        return False
    
    score_result = await score_engine.evaluate("GBP/JPY", features)
    
    if score_result is None:
        print("❌ ScoreEngine failed")
        return False
    
    print(f"✅ GBP/JPY score:")
    print(f"   Symbol: {score_result['symbol']}")
    print(f"   Score: {score_result['score']}/100")
    print(f"   Direction: {score_result['direction']}")
    print(f"   Risk Flags: {score_result['risk_flags']}")
    
    print()
    return True


async def main():
    print("\n🧪 Testing Rewritten Modules\n")
    
    try:
        # Test 1: DataFetcher
        if not await test_data_fetcher():
            print("❌ DataFetcher test failed")
            return
        
        # Test 2: MarketAnalyzer
        if not await test_market_analyzer():
            print("❌ MarketAnalyzer test failed")
            return
        
        # Test 3: ScoreEngine
        if not await test_score_engine():
            print("❌ ScoreEngine test failed")
            return
        
        print("=" * 60)
        print("🎉 All tests passed!")
        print("=" * 60)
    
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
