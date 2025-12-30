
# ============================================================================
# ocr_processor.py - עיבוד OCR (מתוקן)
# ============================================================================

import logging
from pathlib import Path
from typing import List, Tuple
import pytesseract
import pypdfium2 as pdfium
from PIL import Image
import shutil

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

class OCRProcessor:
    """מעבד OCR עם retry ומעקף Netfree"""
    
    def __init__(self, tesseract_path: str = None, languages: str = "heb+eng"):
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        self.languages = languages
    
    def process_directory(self, input_dir: Path, output_dir: Path = None) -> Tuple[List[Path], List[Path]]:
        """
        מעבד תיקייה שלמה עם retry
        
        Returns:
            (רשימת קבצים שהצליחו, רשימת קבצים שנכשלו)
        """
        if output_dir is None:
            output_dir = input_dir / "ocr_txt"
        
        output_dir.mkdir(exist_ok=True)
        
        logging.info(f" סורק תיקייה: {input_dir}")
        
        files_to_process = self._collect_files(input_dir)
        
        if not files_to_process:
            logging.warning(f"לא נמצאו קבצים לעיבוד ב-{input_dir}")
            return [], []
        
        logging.info(f"נמצאו {len(files_to_process)} קבצים לעיבוד\n")
        
        successful = []
        failed = []
        
        for i, file_path in enumerate(files_to_process, 1):
            logging.info(f"[{i}/{len(files_to_process)}] מעבד: {file_path.name}")
            
            result = self._process_single_file(file_path, output_dir)
            if result:
                successful.append(result)
            else:
                failed.append(file_path)
        
        if failed:
            logging.info(f"\n מנסה שוב {len(failed)} קבצים שנכשלו...\n")
            
            for file_path in failed[:]:  # העתק כי נשנה את הרשימה
                logging.info(f" נסיון 2: {file_path.name}")
                
                # אם זה PDF, נסה דרך העתק זמני
                if file_path.suffix.lower() == '.pdf':
                    result = self._try_via_temp_copy(file_path, output_dir)
                else:
                    result = self._process_single_file(file_path, output_dir)
                
                if result:
                    successful.append(result)
                    failed.remove(file_path)
                    logging.info(f"  ✓ הצליח בנסיון שני!\n")
                else:
                    logging.error(f"  ✗ נכשל גם בנסיון שני\n")
        
        logging.info(f" OCR הושלם:")
        logging.info(f"  • הצליחו: {len(successful)}/{len(files_to_process)}")
        logging.info(f"  • נכשלו: {len(failed)}/{len(files_to_process)}\n")
        
        if failed:
            logging.warning("קבצים שנכשלו:")
            for f in failed:
                logging.warning(f"   {f.name}")
        
        return successful, failed
    
    def _collect_files(self, input_dir: Path) -> List[Path]:
        """אוסף קבצים מהתיקייה"""
        files = []
        for ext in ['.pdf', '.jpg', '.jpeg', '.png']:
            files.extend(list(input_dir.glob(f"*{ext}")))
            files.extend(list(input_dir.glob(f"*{ext.upper()}")))
        return files
    
    def _process_single_file(self, file_path: Path, output_dir: Path) -> Path:
        """מעבד קובץ בודד"""
        try:
            txt_path = output_dir / f"{file_path.stem}.txt"
            
            if txt_path.exists():
                logging.info(f"    כבר קיים, מדלג\n")
                return txt_path
            
            if file_path.suffix.lower() == '.pdf':
                text = self._process_pdf(file_path)
            else:
                text = self._process_image(file_path)
            
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(text)
            
            logging.info(f"  ✓ נשמר ב: {txt_path.name}\n")
            return txt_path
            
        except Exception as e:
            logging.error(f"  ✗ שגיאה: {e}\n")
            return None
    
    def _try_via_temp_copy(self, pdf_path: Path, output_dir: Path) -> Path:
        """
         מעקף Netfree: העתקה זמנית עם שם נקי
        """
        try:
            temp_name = f"temp_ocr_{pdf_path.stem[:20].replace(' ', '_')}.pdf"
            temp_path = pdf_path.parent / temp_name
            
            logging.info(f"   מעתיק זמנית ל: {temp_name}")
            shutil.copy2(pdf_path, temp_path)
            
            result = self._process_single_file(temp_path, output_dir)
            
            temp_path.unlink()
            
            if result:
                correct_name = output_dir / f"{pdf_path.stem}.txt"
                if result != correct_name:
                    result.rename(correct_name)
                    return correct_name
            
            return result
            
        except Exception as e:
            logging.error(f"  ✗ נכשל גם דרך העתק זמני: {e}")
            if temp_path.exists():
                temp_path.unlink()
            return None
    
    def _process_pdf(self, pdf_path: Path) -> str:
        """מעבד קובץ PDF"""
        pdf = pdfium.PdfDocument(str(pdf_path))
        all_text = []
        
        for page_num in range(len(pdf)):
            page = pdf[page_num]
            pil_image = page.render(scale=2).to_pil()
            text = pytesseract.image_to_string(pil_image, lang=self.languages)
            all_text.append(text)
        
        return "\n\n".join(all_text)
    
    def _process_image(self, image_path: Path) -> str:
        """מעבד קובץ תמונה"""
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image, lang=self.languages)
        return text

