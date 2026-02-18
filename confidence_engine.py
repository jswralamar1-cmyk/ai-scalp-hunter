"""
confidence_engine.py
AI Scalp Hunter | Confidence Core
Clean Architecture: Score-based confidence calculation
"""

import logging
from config import CONFIDENCE

logger = logging.getLogger(__name__)

RISK_PENALTIES = {
    "low_liquidity": 5,
    "range_market": 7,
    "news_impact": 10,
    "spread_wide": 6,
    "volatility_spike": 8,
    "low_volatility": 3,
    "structure_misaligned": 4,
    "no_clear_pattern": 3
}


class ConfidenceEngine:
    def __init__(self):
        self.min_confidence = CONFIDENCE["min_to_show"]
        self.levels = CONFIDENCE["levels"]

    def calculate(self, score_data: dict, ai_data: dict) -> dict:
        """
        Calculate final confidence based on:
        1. Base score (from ScoreEngine)
        2. Structure bonus
        3. Risk penalty
        4. AI modifier
        
        Args:
            score_data: Output from ScoreEngine (contains score, features, risk_flags)
            ai_data: Output from AI (contains confidence_modifier)
        
        Returns:
            Confidence result with final_confidence, quality, accepted
        """
        # 1. Base confidence (from ScoreEngine)
        base_score = score_data.get("score", 0)
        
        # 2. Structure bonus (small boost if aligned)
        structure_bonus = 0
        features = score_data.get("features", {})
        if features.get("structure_alignment", False):
            structure_bonus = 3
        
        # 3. Risk penalty
        risk_flags = score_data.get("risk_flags", [])
        risk_penalty = self._calculate_risk_penalty(risk_flags)
        
        # 4. AI modifier (capped at ±10)
        ai_modifier = ai_data.get("confidence_modifier", 0)
        ai_modifier = max(-10, min(10, ai_modifier))
        
        # Calculate final confidence
        final_confidence = (
            base_score
            + structure_bonus
            - risk_penalty
            + ai_modifier
        )
        
        # Clamp to [0, 100]
        final_confidence = max(0, min(100, round(final_confidence, 2)))
        
        # Determine quality
        quality = self._determine_quality(final_confidence)
        
        # Log for debugging
        logger.info(f"Confidence calculation: base={base_score}, structure_bonus={structure_bonus}, "
                   f"risk_penalty={risk_penalty}, ai_modifier={ai_modifier}, final={final_confidence}")
        
        return {
            "final_confidence": final_confidence,
            "quality": quality,
            "risk_flags": risk_flags,
            "risk_penalty": risk_penalty,
            "accepted": final_confidence >= self.min_confidence
        }

    def _calculate_risk_penalty(self, flags: list) -> int:
        """Calculate total penalty from risk flags"""
        total = 0
        for flag in flags:
            penalty = RISK_PENALTIES.get(flag, 0)
            if penalty > 0:
                total += penalty
                logger.debug(f"Risk flag '{flag}' → penalty {penalty}")
        return total

    def _determine_quality(self, confidence: float) -> str:
        """Determine quality label based on confidence level"""
        if confidence >= self.levels["excellent"]:
            return "ممتازة"
        elif confidence >= self.levels["good"]:
            return "قوية"
        elif confidence >= self.levels["acceptable"]:
            return "مقبولة"
        else:
            return "مرفوضة"
