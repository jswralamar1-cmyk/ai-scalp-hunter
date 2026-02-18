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
            logger.info(f"Starting AI analysis for {len(top_candidates)} candidates")
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
            logger.info(f"AI raw response length: {len(content)} chars")
            logger.info(f"AI FULL RESPONSE: {content}")  # Print full response
            parsed = json.loads(content)
            logger.info(f"AI parsed type: {type(parsed)}")
            logger.info(f"AI parsed keys: {list(parsed.keys()) if isinstance(parsed, dict) else 'NOT A DICT'}")
            if isinstance(parsed, dict) and 'top_2' in parsed:
                logger.info(f"top_2 type: {type(parsed['top_2'])}")
                logger.info(f"top_2 value: {parsed['top_2']}")
            
            # Validate response structure
            if not isinstance(parsed, dict):
                logger.error("AI response is not a dictionary")
                return {"error": "Invalid AI response format"}
            
            if "top_2" not in parsed:
                logger.error("AI response missing 'top_2' field")
                return {"error": "Invalid AI response format"}
            
            # Defensive parsing: handle string-encoded arrays
            if isinstance(parsed["top_2"], str):
                logger.warning("AI returned top_2 as string, attempting to parse...")
                try:
                    parsed["top_2"] = json.loads(parsed["top_2"])
                    logger.info("Successfully parsed top_2 from string")
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse top_2 string: {e}")
                    return {"error": "Invalid AI response format"}
            
            if not isinstance(parsed["top_2"], list):
                logger.error(f"AI 'top_2' is not a list, it's: {type(parsed['top_2'])}")
                logger.error(f"AI 'top_2' content: {parsed['top_2']}")
                return {"error": "Invalid AI response format"}
            
            # Validate each pick has required fields
            validated_picks = []
            for i, pick in enumerate(parsed["top_2"]):
                # Defensive: handle string-encoded picks
                if isinstance(pick, str):
                    logger.warning(f"Pick {i} is string, attempting to parse...")
                    try:
                        pick = json.loads(pick)
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse pick {i} from string")
                        continue
                
                if not isinstance(pick, dict):
                    logger.warning(f"Skipping non-dict pick {i}: {type(pick)}")
                    continue
                
                # Must have pair and direction
                if "pair" not in pick or "direction" not in pick:
                    logger.warning(f"Skipping pick {i} without pair/direction: {pick}")
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
- reasoning: array of strings IN ARABIC (why this is a good opportunity - MUST be in Arabic language)
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
5. CRITICAL: "top_2" MUST be a JSON array, NOT a string
6. DO NOT wrap the array in quotes
7. CRITICAL: "reasoning" array MUST be in ARABIC language only

Return format (EXACT structure required):
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
      "reasoning": ["زخم صاعد قوي", "دعم من المتوسط المتحرك", "تقاطع إيجابي في الماكد"],
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
      "reasoning": ["نموذج ابتلاع هابط", "مستوى مقاومة قوي"],
      "confidence_modifier": 0
    }}
  ]
}}

Candidates:
{json.dumps(top_candidates, indent=2)}
"""
