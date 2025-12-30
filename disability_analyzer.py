
# ============================================================================
# disability_analyzer.py - המנתח 
# ============================================================================

from dataclasses import dataclass
import json
import logging
from typing import List, Dict

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

class DisabilityAnalyzer:
    def __init__(self, openai_client, rag_system):
        self.ai = openai_client
        self.rag = rag_system

    def analyze_patient_data(self, medical_json: dict) -> dict:
        logging.info("--- התחלת ניתוח בשיטת 'חבילות ראיות' לפי איברים ---")
        
        evidence_bundles = self._create_evidence_bundles(medical_json)
        results = []
        for bundle in evidence_bundles:
            result = self._analyze_single_organ(bundle)
            if result:
                results.append(result)

        
        return self._calculate_combined_disability(results)

    def _create_evidence_bundles(self, medical_json: dict) -> List[dict]:
        """שלב הזיקוק: איחוד כל הממצאים לאיברים ייחודיים"""
        logging.info("מזקק ראיות לפי איברים...")
        
        raw_data = medical_json.get('diagnoses_by_body_part', {})
        
        prompt = f"""
        משימה קריטית: אחד את כל הממצאים הרפואיים לאיברים ייחודיים בלבד.

        כללי איחוד קפדניים:
        1. **איחוד כפילויות**: "כתף ימין" ו"כתף" → רק "כתף ימין" אחת
        2. **שמירת ממצאים מלאים**: אל תסכם! העתק את כל הממצאים הקליניים:
           - טווחי תנועה במעלות (למשל: "סיבוב פנימי 30 מעלות")
           - שמות ניתוחים מלאים (למשל: "ניתוח בנקרט")
           - ממצאי הדמיה (למשל: "קרע מסיבי ברוטטור קאף", "בלט דיסק L4-L5")
           - ממצאים אובייקטיביים (למשל: "אי יציבות", "כאב בלחיצה")
        3. **כל איבר פעם אחת**: אם יש "כתף ימין" וגם "כתף", צרף הכל ל"כתף ימין" אחת
        4. **דצימציה**: גב תחתון, ירך, ברך, קרסול - כל אחד בנפרד

        נתונים גולמיים:
        {json.dumps(raw_data, ensure_ascii=False, indent=2)}

        החזר JSON במבנה:
        {{
           "bundles": [
              {{
                "body_part": "שם האיבר המדויק (למשל 'כתף ימין', 'גב תחתון')",
                "evidence_text": "ריכוז כל הממצאים הקליניים והטכניים מכל המקורות",
                "main_diagnosis": "האבחנה המרכזית"
              }}
           ]
        }}
        
        דוגמה:
        אם יש "כתף" עם "קרע רוטטור" ו"כתף ימין" עם "הגבלת תנועה 30°", 
        החזר איבר אחד "כתף ימין" עם שני הממצאים ביחד.
        """
        
        response = self.ai.call(
            prompt=prompt,
            system_prompt="אתה עוזר רפואי מדייק. תפקידך לאחד כפילויות ולשמור על כל הממצאים הקליניים ללא סיכום.",
            response_format={"type": "json_object"}
        )
        
        bundles = json.loads(response).get('bundles', [])
        logging.info(f"זוקק ל-{len(bundles)} איברים ייחודיים")
        
        return bundles

    def _analyze_single_organ(self, bundle: dict) -> dict:
        """ניתוח ממוקד לאיבר אחד: RAG ו-GPT"""
        body_part = bundle['body_part']
        evidence = bundle['evidence_text']
        
        logging.info(f"🔍 מנתח איבר: {body_part} {evidence}")

        rag_query = f"סעיפי ליקוי בביטוח לאומי עבור {body_part}: {evidence}"
        context = self.rag.query_as_context(rag_query, k=7)

        prompt = f"""
        אתה מומחה רפואי לוועדות נכות של ביטוח לאומי.
        
        **משימה**: קבע אחוז נכות מדויק עבור: {body_part}
        
        **הממצאים הרפואיים (הראיות)**:
        {evidence}

        **סעיפי התקנות הרלוונטיים**:
        {context}

        **הנחיות לקביעת אחוז**:
        1. בחר את הסעיף המתאים ביותר לממצאים הקליניים
        2. התאם בין חומרת הממצא (למשל "הגבלת תנועה קשה") לחומרת הסעיף
        3. אם יש כמה סעיפים, בחר את המשקף הכי טוב את המצב הכללי
        4. אם אין סעיף מתאים או הממצאים לא מספיק ברורים, החזר 0
        5. היה שמרן - רק ממצאים מתועדים טוב מקבלים אחוזים

        **פורמט החזרה** (JSON בלבד):
        {{
            "body_part": "{body_part}",
            "disability_percentage":  (0 אם אין התאמה) מספר_שלם_בלבד,
            "section_used": "מספר הסעיף המדויק (למשל 'סעיף 5(4)(ה)') או 'N/A' אם 0",
            "reasoning": "אם disability_percentage=0, הסבר בדיוק מה חסר (למשל: 'דרוש טווח תנועה במעלות', 'דרוש EMG', 'חסר תיעוד של תדירות כאב') הסבר קצר: איזה ממצא קליני הוביל לאיזה סעיף ולמה",
            "confidence": "high/medium/low"
        }}
        """
        
        response = self.ai.call(
            prompt=prompt,
            system_prompt="אתה מומחה בתקנות ביטוח לאומי. ענה רק ב-JSON תקני. אל תחזיר טקסט נוסף.",
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response)
        if not result.get('disability_percentage') or result.get('disability_percentage') == 0:
            result['missing_info'] = result.get('reasoning', 'לא נמצא סעיף מתאים')
            result['status'] = 'חסר מידע'
        else:
            result['missing_info'] = None
            result['status'] = 'הושלם'
        logging.info(f"   {body_part}: {result.get('disability_percentage', 0)}% ({result.get('section_used', 'N/A')})")
        
        return result
    def _calculate_combined_disability(self, results: List[dict]) -> dict:
        """חישוב משוקלל סופי של כל התוצאות (נוסחת בלבנד)"""
        
        valid_results = [r for r in results if float(r.get('disability_percentage', 0)) > 0]
        
        percentages = []
        summary_details = []

        for res in valid_results:
            p = float(res.get('disability_percentage', 0))
            percentages.append(p)
            summary_details.append({
                "organ": res['body_part'],
                "percent": p,
                "section": res.get('section_used', 'לא צוין')
            })

        percentages.sort(reverse=True)
        total = 0.0
        health = 100.0
        for p in percentages:
            total += (p * health / 100.0)
            health = 100.0 - total
        
        logging.info(f"📊 סיכום: {len(valid_results)} איברים, נכות כוללת: {round(total, 2)}%")
            
        return {
            "total_disability": round(total, 2),
            "breakdown": summary_details,
            "full_results": results  
        }
    def _calculate_combined_disability1(self, results: List[dict]) -> dict:
        """חישוב משוקלל סופי של כל התוצאות (נוסחת בלבנד)"""
        
        valid_results = [r for r in results if r.get('disability_percentage', 0) > 0]
        
        percentages = []
        summary_details = []

        for res in valid_results:
            p = res.get('disability_percentage', 0)
            percentages.append(float(p))
            summary_details.append({
                "organ": res['body_part'],
                "percent": p,
                "section": res.get('section_used', 'לא צוין')
            })

        percentages.sort(reverse=True)
        total = 0.0
        health = 100.0
        
        for p in percentages:
            total += (p * health / 100.0)
            health = 100.0 - total
        
        logging.info(f"📊 סיכום: {len(valid_results)} איברים, נכות כוללת: {round(total, 2)}%")
            
        return {
            "total_disability": round(total, 2),
            "breakdown": summary_details,
            "full_results": valid_results
        }
