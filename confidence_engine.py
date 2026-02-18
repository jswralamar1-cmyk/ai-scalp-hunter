"""
confidence_engine.py
AI Scalp Hunter | Confidence Core
"""

from config import CONFIDENCE

RISK_PENALTIES = {
    "low_liquidity": 3,
    "range_market": 5,
    "news_impact": 8,
    "spread_wide": 4,
    "volatility_spike": 6
}


class ConfidenceEngine:
    def __init__(self):
        self.min_confidence = CONFIDENCE["min_to_show"]
        self.levels = CONFIDENCE["levels"]

    def calculate(self, score_data: dict, ai_data: dict) -> dict:
        base_score = score_data["score"]

        momentum = ai_data.get("momentum_strength", 0) * 20
        pattern = ai_data.get("pattern_conviction", 0) * 15
        structure = 5 if ai_data.get("structure_alignment", False) else 0

        ai_modifier = ai_data.get("confidence_modifier", 0)

        risk_flags = ai_data.get("risk_flags", [])
        risk_penalty = self._calculate_risk_penalty(risk_flags)

        final_confidence = (
            (base_score * 0.5)
            + momentum
            + pattern
            + structure
            - risk_penalty
            + ai_modifier
        )

        final_confidence = max(0, min(100, round(final_confidence, 2)))

        quality = self._determine_quality(final_confidence)

        return {
            "final_confidence": final_confidence,
            "quality": quality,
            "risk_flags": risk_flags,
            "risk_penalty": risk_penalty,
            "accepted": final_confidence >= self.min_confidence
        }

    def _calculate_risk_penalty(self, flags: list) -> int:
        total = 0
        for flag in flags:
            total += RISK_PENALTIES.get(flag, 0)
        return total

    def _determine_quality(self, confidence: float) -> str:
        if confidence >= self.levels["excellent"]:
            return "ممتازة"
        elif confidence >= self.levels["good"]:
            return "قوية"
        elif confidence >= self.levels["acceptable"]:
            return "مقبولة"
        else:
            return "مرفوضة"
