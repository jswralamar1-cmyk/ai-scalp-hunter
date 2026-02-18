"""
signal_builder.py
AI Scalp Hunter | Signal Builder
"""

from typing import Dict, Optional, List
from confidence_engine import ConfidenceEngine
from anti_repeat_guard import AntiRepeatGuard
from config import CONFIDENCE

AR_RISK_LABELS = {
    "low_liquidity": "سيولة ضعيفة",
    "range_market": "سوق داخل رينج",
    "news_impact": "احتمال خبر/تذبذب",
    "spread_wide": "سبريد واسع",
    "volatility_spike": "تقلب عالي"
}


class SignalBuilder:
    def __init__(self):
        self.conf_engine = ConfidenceEngine()
        self.anti_repeat = AntiRepeatGuard()
        self.min_conf = CONFIDENCE["min_to_show"]

    def build_one(self, ai_pick: Dict, score_snapshot: Dict, timeframe_label: str) -> Optional[Dict]:
        # Validate required fields
        if "pair" not in ai_pick or "direction" not in ai_pick:
            return None
        
        # Use market price, not AI-generated price
        market_price = float(score_snapshot.get("last_close", 0))
        if market_price == 0:
            return None
        
        conf = self.conf_engine.calculate(score_snapshot, ai_pick)
        if not conf["accepted"]:
            return None

        repeat = self.anti_repeat.check(
            pair=ai_pick["pair"],
            direction=ai_pick["direction"],
            price=market_price
        )

        message = self._build_arabic_message(
            ai_pick=ai_pick,
            score_snapshot=score_snapshot,
            conf=conf,
            timeframe_label=timeframe_label,
            repeat_warning=repeat.get("warning")
        )

        chart_payload = {
            "pair": ai_pick["pair"],
            "timeframe": timeframe_label,
            "direction": ai_pick["direction"],
            "entry_price": market_price,
            "expiry_minutes": int(ai_pick.get("expiry_minutes", 1))
        }

        return {
            "pair": ai_pick["pair"],
            "direction": ai_pick["direction"],
            "entry_price": market_price,
            "expiry_minutes": int(ai_pick.get("expiry_minutes", 1)),
            "final_confidence": conf["final_confidence"],
            "quality": conf["quality"],
            "risk_flags": conf["risk_flags"],
            "message": message,
            "chart_payload": chart_payload,
            "repeat_warning": repeat.get("warning")
        }

    def commit_sent(self, signal: Dict):
        self.anti_repeat.commit(signal["pair"], signal["direction"], signal["entry_price"])

    def _build_arabic_message(self, ai_pick: Dict, score_snapshot: Dict, conf: Dict,
                              timeframe_label: str, repeat_warning: Optional[str]) -> str:
        pair = ai_pick["pair"]
        direction = ai_pick["direction"]
        entry = float(score_snapshot.get("last_close", 0))
        expiry = int(ai_pick.get("expiry_minutes", 1))
        final_conf = conf["final_confidence"]
        quality = conf["quality"]

        dir_ar = "صعود (CALL)" if direction == "CALL" else "نزول (PUT)"

        reasons = ai_pick.get("reasoning", []) or []
        reasons = [r.strip() for r in reasons if isinstance(r, str) and r.strip()]
        reasons = reasons[:6] if reasons else ["تحليل متعدد العوامل (زخم + هيكل + نمط)."]

        risk_flags = conf.get("risk_flags", []) or []
        risk_text = None
        if risk_flags:
            labels = [AR_RISK_LABELS.get(f, f) for f in risk_flags][:4]
            risk_text = "⚠️ مخاطر: " + "، ".join(labels)

        base_score = score_snapshot.get("score", 0)

        lines = []
        lines.append("🎯 **تحليل ذكي | سكالبينغ**")
        lines.append(f"💱 الزوج: **{pair}**")
        lines.append(f"⏱️ الفريم: **{timeframe_label}**")
        lines.append(f"📌 الاتجاه: **{dir_ar}**")
        lines.append(f"💵 سعر الدخول المقترح: **{entry:.5f}**")
        lines.append(f"⏳ مدة الصفقة: **{expiry} دقيقة**")
        lines.append("")
        lines.append(f"✅ الثقة النهائية: **{final_conf:.1f}%** ({quality})")
        lines.append(f"📊 Score رياضي: **{base_score}/100**")
        lines.append("")
        lines.append("🧠 أسباب القرار:")
        for r in reasons:
            lines.append(f"• {r}")

        if risk_text:
            lines.append("")
            lines.append(risk_text)

        if repeat_warning:
            lines.append("")
            lines.append(repeat_warning)

        lines.append("")
        lines.append("⚠️ **تحذير:** السكالبينغ عالي المخاطر. القرار النهائي عليك.")

        return "\n".join(lines)
