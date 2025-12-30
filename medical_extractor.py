

# ============================================================================
# medical_extractor.py - חילוץ JSON (מתוקן)
# ============================================================================

from datetime import datetime
import json
import logging
from pathlib import Path
import time
from typing import Any, List

from openai_client import OpenAIClient
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
class MedicalJSONExtractor:
    """מחלץ מידע רפואי עם retry"""
    
    def __init__(self, openai_client: OpenAIClient):
        self.ai = openai_client
        self.extraction_prompt = self._build_extraction_prompt()
    
    def _build_extraction_prompt(self) -> str:
        return """
        אתה מומחה רפואי משפטי המתמחה בניתוח תיעוד רפואי לצורך הערכת נכות.

        הנחיות:
        1. התעלם משגיאות OCR - תבין את הכוונה
        2. תרגם מונחים רפואיים לעברית ברורה
        3. זהה חומרות: קל/בינוני/חמור/קשה מאוד
        4. חלץ תאריכים
        5. זהה תלות בטיפולים: קבועה/לסירוגין/לא תלוי

        החזר JSON:
        {
        "diagnoses": [
            {
            "body_part": "איבר בעברית",
            "condition_hebrew": "אבחנה בעברית פשוטה",
            "condition_medical_term": "מונח רפואי מדויק",
            "severity": "קל/בינוני/חמור/קשה מאוד",
            "severity_indicators": {
                "functional_limitation": "מה לא יכול לעשות",
                "frequency": "קבועה/לסירוגין/נדירה",
                "progression": "מחמיר/יציב/משתפר"
            },
            "chronic": true/false,
            "date_diagnosed": "תאריך או null",
            "details": "פרטים נוספים"
            }
        ],
        "treatments": [...],
        "surgeries": [...],
        "medical_tests": [...],
        "functional_limitations": [...]
        }
        """
    
    def extract_from_file(self, file_path: Path) -> dict:
        """מחלץ מידע מקובץ עם retry"""
        logging.info(f"מחלץ מידע מ: {file_path.name}")
        
        # קריאת קובץ
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='windows-1255') as f:
                content = f.read()
        
        if len(content.strip()) < 50:
            logging.warning(f"קובץ {file_path.name} קצר מדי או ריק")
            return self._create_empty_result(file_path.name, "Empty file")
        
        # ניסיון עיבוד
        for attempt in range(2):
            try:
                full_prompt = self.extraction_prompt + "\n\nתיעוד רפואי:\n\n" + content
                
                response = self.ai.call(
                    prompt=full_prompt,
                    system_prompt="אתה מומחה רפואי משפטי לניתוח תיעוד רפואי.",
                    response_format={"type": "json_object"},
                    temperature=0.1
                )
                
                result = json.loads(response)
                result['file_metadata'] = {
                    'filename': file_path.name,
                    'processing_date': datetime.now().isoformat(),
                    'status': 'success'
                }
                
                return self._clean_nulls(result)
                
            except json.JSONDecodeError as e:
                logging.warning(f"    נסיון {attempt+1}: JSON לא תקין - {e}")
                if attempt == 1:
                    return self._create_empty_result(file_path.name, f"JSON decode failed: {e}")
                time.sleep(1)
                
            except Exception as e:
                logging.error(f"   נסיון {attempt+1}: {e}")
                if attempt == 1:
                    return self._create_empty_result(file_path.name, str(e))
                time.sleep(1)
        
        return self._create_empty_result(file_path.name, "All retries failed")
    
    def extract_from_directory(self, directory: Path, output_dir: Path) -> dict:
        """מעבד תיקייה"""
        txt_files = sorted(directory.glob("*.txt"))
        
        if not txt_files:
            logging.error(f"לא נמצאו קבצי TXT ב-{directory}")
            return {}
        
        logging.info(f"מעבד {len(txt_files)} קבצים...\n")
        
        all_results = []
        successful = 0
        failed = 0
        
        for i, file_path in enumerate(txt_files, 1):
            logging.info(f"[{i}/{len(txt_files)}]")
            result = self.extract_from_file(file_path)
            
            if result.get('file_metadata', {}).get('status') == 'success':
                successful += 1
            else:
                failed += 1
            
            all_results.append(result)
            
            # שמירה בודדת
            output_file = output_dir / f"{file_path.stem}_extracted.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        
        # איחוד
        consolidated = self._consolidate_results(all_results)
        
        consolidated_file = output_dir / "all_medical_data_consolidated.json"
        with open(consolidated_file, 'w', encoding='utf-8') as f:
            json.dump(consolidated, f, ensure_ascii=False, indent=2)
        
        logging.info(f"\n חילוץ הושלם:")
        logging.info(f"  • הצליחו: {successful}/{len(txt_files)}")
        logging.info(f"  • נכשלו: {failed}/{len(txt_files)}")
        logging.info(f"  • נשמר ב: {consolidated_file}\n")
        
        return consolidated
    
    def _consolidate_results(self, results: List[dict]) -> dict:
        consolidated = {
            'metadata': {
                'total_files_processed': len(results),
                'successful': sum(1 for r in results if r.get('file_metadata', {}).get('status') == 'success'),
                'failed': sum(1 for r in results if r.get('file_metadata', {}).get('status') != 'success'),
                'processing_date': datetime.now().isoformat()
            },
            'diagnoses_by_body_part': {},
            'all_treatments': [],
            'all_surgeries': [],
            'all_medical_tests': [],
            'all_functional_limitations': []
        }
        
        for result in results:
            if result.get('file_metadata', {}).get('status') != 'success':
                continue
            
            for diag in result.get('diagnoses', []):
                body_part = diag.get('body_part', 'לא מוגדר')
                
                if body_part not in consolidated['diagnoses_by_body_part']:
                    consolidated['diagnoses_by_body_part'][body_part] = {
                        'body_part': body_part,
                        'conditions': []
                    }
                
                consolidated['diagnoses_by_body_part'][body_part]['conditions'].append(diag)
            
            consolidated['all_treatments'].extend(result.get('treatments', []))
            consolidated['all_surgeries'].extend(result.get('surgeries', []))
            consolidated['all_medical_tests'].extend(result.get('medical_tests', []))
            consolidated['all_functional_limitations'].extend(result.get('functional_limitations', []))
        
        return consolidated
    
    def _clean_nulls(self, data: Any) -> Any:
        if isinstance(data, dict):
            return {k: self._clean_nulls(v) for k, v in data.items() if v not in [None, "", [], {}, "null"]}
        elif isinstance(data, list):
            return [self._clean_nulls(item) for item in data if item]
        return data
    
    def _create_empty_result(self, filename: str, error: str) -> dict:
        return {
            'file_metadata': {
                'filename': filename,
                'processing_date': datetime.now().isoformat(),
                'status': 'failed',
                'error': error
            },
            'diagnoses': []
        }

