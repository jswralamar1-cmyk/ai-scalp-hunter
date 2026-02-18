"""
ai_engine.py
AI Scalp Hunter - Professional AI Engine
Uses Groq AI to analyze top candidates and select best opportunities
"""

import asyncio
import json
import logging
from typing import Dict, List
from groq import Groq
from config import GROQ_API_KEY, GROQ_MODEL, AI_TIMEOUT

logger = logging.getLogger(__name__)


class AIEngine:
    """
    AI-powered analysis engine using Groq
    - Analyzes top 15 candidates
    - Selects best 2 opportunities
    - Provides confidence modifiers and reasoning
    """
    
    def __init__(self):
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not set")
        
        self.client = Groq(api_key=GROQ_API_KEY)
        self.model = GROQ_MODEL
    
    async def analyze(self, top_candidates: List[Dict]) -> Dict:
        """
        Analyze top candidates and select best opportunities
        
        Args:
            top_candidates: List of top 15 scored candidates
        
        Returns:
            Dictionary with top_2 picks or error
        """
        try:
            prompt = self._build_prompt(top_candidates)
            
            # Run Groq API in thread pool (it's synchronous)
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an elite scalping trading analyst with deep expertise in technical analysis and market microstructure."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.2,
                    response_format={"type": "json_object"}
                ),
                timeout=AI_TIMEOUT
            )
            
            # Parse response
            content = response.choices[0].message.content
            parsed = json.loads(content)
            
            # Validate response structure
            if not isinstance(parsed, dict):
                logger.error("AI response is not a dictionary")
                return {"error": "Invalid AI response format"}
            
            if "top_2" not in parsed:
                logger.error("AI response missing 'top_2' field")
                return {"error": "Invalid AI response format"}
            
            if not isinstance(parsed["top_2"], list):
                logger.error("AI 'top_2' is not a list")
                return {"error": "Invalid AI response format"}
            
            # Validate each pick has required fields
            validated_picks = []
            for pick in parsed["top_2"]:
                if not isinstance(pick, dict):
                    logger.warning("Skipping non-dict pick")
                    continue
                
                # Must have pair and direction
                if "pair" not in pick or "direction" not in pick:
                    logger.warning(f"Skipping pick without pair/direction: {pick}")
                    continue
                
                # Add defaults for missing optional fields
                pick.setdefault("expiry_minutes", 2)
                pick.setdefault("pattern_conviction", 0.5)
                pick.setdefault("momentum_strength", 0.5)
                pick.setdefault("structure_alignment", False)
                pick.setdefault("risk_flags", [])
                pick.setdefault("reasoning", [])
                pick.setdefault("confidence_modifier", 0)
                
                validated_picks.append(pick)
            
            if not validated_picks:
                logger.error("No valid picks after validation")
                return {"error": "No valid AI picks"}
            
            return {"top_2": validated_picks}
        
        except asyncio.TimeoutError:
            logger.error(f"AI timeout after {AI_TIMEOUT}s")
            return {"error": "AI timeout"}
        
        except json.JSONDecodeError as e:
            logger.error(f"AI JSON parse error: {e}")
            return {"error": "AI response not valid JSON"}
        
        except Exception as e:
            logger.error(f"AI error: {e}")
            return {"error": str(e)}
    
    def _build_prompt(self, top_candidates: List[Dict]) -> str:
        """
        Build prompt for AI analysis
        
        Args:
            top_candidates: List of candidates
        
        Returns:
            Formatted prompt string
        """
        return f"""
You are a professional scalping analyst.

You are given {len(top_candidates)} pre-filtered trading candidates.
Select ONLY the best 2 opportunities with the highest probability of success.

For each opportunity, return:

- pair: Trading pair (e.g. "EUR/USD")
- direction: "CALL" or "PUT"
- expiry_minutes: 1, 2, or 3 (recommended expiry time)
- pattern_conviction: 0.0 to 1.0 (how strong is the pattern)
- momentum_strength: 0.0 to 1.0 (how strong is the momentum)
- structure_alignment: true or false (do timeframes align)
- risk_flags: array of strings (any concerns)
- reasoning: array of strings (why this is a good opportunity)
- confidence_modifier: -10 to +10 (adjustment to base confidence)

Important rules:
1. You may reverse the initial direction ONLY if strong reversal evidence exists
2. If reversing, clearly explain why in reasoning
3. Prioritize opportunities with:
   - High score (70+)
   - Low risk flags
   - Strong structure alignment
   - Clear patterns
4. Return STRICT JSON format

Return format:
{{
  "top_2": [
    {{
      "pair": "EUR/USD",
      "direction": "CALL",
      "expiry_minutes": 2,
      "pattern_conviction": 0.85,
      "momentum_strength": 0.75,
      "structure_alignment": true,
      "risk_flags": [],
      "reasoning": ["Strong bullish momentum", "EMA support", "MACD crossover"],
      "confidence_modifier": 5
    }},
    {{
      "pair": "GBP/JPY",
      "direction": "PUT",
      "expiry_minutes": 1,
      "pattern_conviction": 0.70,
      "momentum_strength": 0.65,
      "structure_alignment": true,
      "risk_flags": ["slight_divergence"],
      "reasoning": ["Bearish engulfing", "Resistance level"],
      "confidence_modifier": 0
    }}
  ]
}}

Candidates:
{json.dumps(top_candidates, indent=2)}
"""
