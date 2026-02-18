"""
anti_repeat_guard.py
AI Scalp Hunter | Anti Repeat Guard
"""

import time
from dataclasses import dataclass
from typing import Optional, Dict
from config import ANTI_REPEAT


@dataclass
class LastSignal:
    pair: str
    direction: str
    entry_price: float
    ts: float


class AntiRepeatGuard:
    def __init__(self):
        self.enabled = ANTI_REPEAT.get("enabled", True)
        self.price_distance = ANTI_REPEAT.get("price_distance", 0.001)
        self.time_window_min = ANTI_REPEAT.get("time_window", 6)
        self.max_score = ANTI_REPEAT.get("max_score", 0.7)
        self._last: Optional[LastSignal] = None

    def check(self, pair: str, direction: str, price: float) -> Dict:
        if not self.enabled or self._last is None:
            return {"is_repeat": False, "repeat_score": 0.0, "warning": None}

        now = time.time()
        age_min = (now - self._last.ts) / 60.0
        if age_min > self.time_window_min:
            return {"is_repeat": False, "repeat_score": 0.0, "warning": None}

        repeat_score = 0.0

        if self._last.pair == pair:
            repeat_score += 0.4
        if self._last.direction == direction:
            repeat_score += 0.3

        try:
            diff_pct = abs(self._last.entry_price - price) / max(price, 1e-9)
        except Exception:
            diff_pct = 1.0

        if diff_pct < self.price_distance:
            repeat_score += 0.3

        warning = None
        if repeat_score >= 0.7:
            warning = "⚠️ تنبيه: صفقة مشابهة جداً لآخر صفقة (احتمال تكرار)."
        elif repeat_score >= 0.4:
            warning = "⚠️ تنبيه: نفس الزوج/الاتجاه قريب من آخر صفقة لكن بظروف مختلفة."

        return {"is_repeat": repeat_score >= self.max_score, "repeat_score": round(repeat_score, 2), "warning": warning}

    def commit(self, pair: str, direction: str, price: float):
        self._last = LastSignal(pair=pair, direction=direction, entry_price=price, ts=time.time())
