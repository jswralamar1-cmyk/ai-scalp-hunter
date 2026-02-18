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
    - Provides detailed Arabic analysis based on numerical data
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
                            "content": "أنت محلل سكالبينغ احترافي متخصص بفريم الدقيقة الواحدة. تحلل البيانات الرقمية بدقة وتقدم تحليلاً مخصصاً لكل زوج بناءً على القيم الفعلية."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.3,
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
                pick.setdefault("analysis", {
                    "market_structure": "غير متوفر",
                    "momentum": "غير متوفر",
                    "indicator_confluence": "غير متوفر",
                    "risk_assessment": "غير متوفر",
                    "entry_logic": "غير متوفر"
                })
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
        Build professional Arabic prompt for AI analysis
        
        Args:
            top_candidates: List of candidates with numerical data
        
        Returns:
            Formatted prompt string
        """
        return f"""
سيتم تزويدك ببيانات رقمية دقيقة لـ {len(top_candidates)} زوج عملات.

كل زوج يحتوي على:
- symbol: اسم الزوج
- score: التقييم الرياضي (من 100)
- direction: الاتجاه المقترح (CALL أو PUT)
- risk_flags: علامات المخاطر
- features: البيانات الرقمية التفصيلية:
  * rsi_1m: قيمة RSI (0-100)
  * macd_hist_1m: قيمة MACD Histogram (موجبة أو سالبة)
  * ema_position_1m: موقع السعر من EMA (true = أعلى, false = أسفل)
  * structure_alignment: توافق هيكل السوق (true/false)
  * atr_1m: مقياس التذبذب ATR
  * vwap_distance_1m: المسافة من VWAP
- last_close: آخر سعر إغلاق

⚠️ قواعد صارمة:

1. ⚠️ CRITICAL: يجب اختيار فرصتين بالضبط (2 فرص) - ليس واحدة، ليس ثلاثة
2. top_2 يجب أن يكون JSON array يحتوي على عنصرين بالضبط
3. يجب أن يكون التحليل مبنياً على الأرقام المرسلة فقط
4. اذكر القيم الرقمية داخل التحليل (مثال: "RSI عند 68 يشير إلى...")
5. يمنع منعاً باتاً تكرار نفس الأسباب بين الزوجين
6. كل زوج يجب أن يحصل على تحليل مخصص مختلف تماماً
7. لا تستخدم عبارات عامة مثل "الزخم قوي" بدون ذكر الرقم
8. التحليل باللغة العربية فقط
9. لا تضف أي نص خارج JSON
10. ⚠️ MUST return exactly 2 opportunities in the array

📋 الشكل المطلوب حصراً (زوجين بالضبط):

{{
  "top_2": [
    {{
      "pair": "الزوج الأول (مثال: EUR/JPY)",
      "direction": "CALL أو PUT",
      "expiry_minutes": 1 أو 2 أو 3,
      "analysis": {{
        "market_structure": "تحليل هيكل السوق بناءً على structure_alignment والأرقام",
        "momentum": "تحليل الزخم مبني على RSI و MACD بالأرقام الفعلية",
        "indicator_confluence": "تفسير توافق EMA و VWAP و ATR بالقيم الرقمية",
        "risk_assessment": "تقييم المخاطر بناءً على ATR و risk_flags",
        "entry_logic": "منطق الدخول المختصر المبني على الأرقام"
      }},
      "confidence_modifier": رقم من -10 إلى +10
    }},
    {{
      "pair": "الزوج الثاني (مثال: GBP/USD)",
      "direction": "CALL أو PUT",
      "expiry_minutes": 1 أو 2 أو 3,
      "analysis": {{
        "market_structure": "تحليل مختلف تماماً عن الزوج الأول",
        "momentum": "تحليل مختلف بأرقام مختلفة",
        "indicator_confluence": "تفسير مختلف بناءً على بيانات هذا الزوج",
        "risk_assessment": "تقييم مختلف",
        "entry_logic": "منطق مختلف"
      }},
      "confidence_modifier": رقم من -10 إلى +10
    }}
  ]
}}

🔥 مثال توضيحي:

بدلاً من: "الزخم قوي"
اكتب: "RSI عند 72 يشير إلى تشبع شرائي قريب، لكن MACD +0.0035 يؤكد استمرار الدفع"

بدلاً من: "دعم من المتوسط"
اكتب: "السعر أعلى EMA بمسافة 0.12% مما يدل على تفوق المشترين"

📊 البيانات:

{json.dumps(top_candidates, indent=2, ensure_ascii=False)}
"""
