"""
ai_engine.py
AI Scalp Hunter | AI Core
"""

import asyncio
import json
from groq import Groq
from config import GROQ_API_KEY, GROQ_MODEL, AI_TIMEOUT


class AIEngine:
    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)

    async def analyze(self, top_candidates: list) -> dict:
        prompt = self._build_prompt(top_candidates)

        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=GROQ_MODEL,
                    messages=[
                        {"role": "system", "content": "You are an elite scalping trading analyst."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,
                    response_format={"type": "json_object"}
                ),
                timeout=AI_TIMEOUT
            )

            content = response.choices[0].message.content
            parsed = json.loads(content)
            return parsed

        except asyncio.TimeoutError:
            return {"error": "AI timeout"}
        except Exception as e:
            return {"error": str(e)}

    def _build_prompt(self, top_candidates: list) -> str:
        return f"""
You are a professional scalping analyst.

You are given 15 pre-filtered trading candidates.
Select ONLY the best 2 opportunities.

For each opportunity return:

- pair
- direction (CALL or PUT)
- expiry_minutes (1, 2 or 3)
- pattern_conviction (0.0 to 1.0)
- momentum_strength (0.0 to 1.0)
- structure_alignment (true/false)
- risk_flags (array)
- reasoning (array of strings)
- confidence_modifier (-10 to +10)

Important rules:
- You may reverse the initial direction ONLY if strong reversal evidence exists.
- If reversing, clearly explain why.
- Return STRICT JSON.

Candidates:
{json.dumps(top_candidates, indent=2)}
"""
