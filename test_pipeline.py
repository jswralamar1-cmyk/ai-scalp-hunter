"""
test_pipeline.py
Test the complete signal generation pipeline
"""

import asyncio
import logging
from bot_runner import run_scalp_analysis

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def test_pipeline():
    """Test the complete pipeline"""
    logger.info("=" * 60)
    logger.info("🧪 TESTING AI SCALP HUNTER PIPELINE")
    logger.info("=" * 60)
    
    try:
        # Run analysis
        logger.info("\n📊 Starting analysis...")
        result = await run_scalp_analysis()
        
        # Check result
        logger.info("\n" + "=" * 60)
        logger.info("📋 RESULTS:")
        logger.info("=" * 60)
        
        if result.get("success"):
            signals = result.get("signals", [])
            logger.info(f"✅ Success: {len(signals)} signals generated")
            
            for i, signal in enumerate(signals, 1):
                logger.info(f"\n🎯 Signal {i}:")
                logger.info(f"   Symbol: {signal.get('symbol')}")
                logger.info(f"   Direction: {signal.get('direction')}")
                logger.info(f"   Confidence: {signal.get('confidence')}%")
                logger.info(f"   Quality: {signal.get('quality')}")
                logger.info(f"   Entry: {signal.get('entry_price')}")
                logger.info(f"   TP: {signal.get('take_profit')}")
                logger.info(f"   SL: {signal.get('stop_loss')}")
                
                # Check confidence calculation details
                if 'risk_flags' in signal:
                    logger.info(f"   Risk Flags: {signal.get('risk_flags')}")
                if 'risk_penalty' in signal:
                    logger.info(f"   Risk Penalty: {signal.get('risk_penalty')}")
        else:
            error = result.get("error", "Unknown error")
            logger.error(f"❌ Failed: {error}")
            
            # Check for detailed error info
            if "details" in result:
                logger.error(f"Details: {result['details']}")
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ TEST COMPLETE")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_pipeline())
