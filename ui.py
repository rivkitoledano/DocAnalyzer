# ============================================================================
# ui.py - ממשק משתמש משופר עם עיצוב מודרני
# ============================================================================

from datetime import datetime
import json
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from threading import Thread
from typing import List, Tuple

from config import Config
from disability_analyzer import DisabilityAnalyzer
from medical_extractor import MedicalJSONExtractor
from ocr_processor import OCRProcessor
from openai_client import OpenAIClient
from rag_system import RAGSystem

class ModernButton(tk.Button):
    """כפתור מודרני עם אפקטים"""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.config(
            relief=tk.FLAT,
            borderwidth=0,
            cursor="hand2",
            font=("Segoe UI", 11, "bold")
        )
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.default_bg = kwargs.get('bg', '#2e7d32')
        
    def _on_enter(self, e):
        if self['state'] != tk.DISABLED:
            self.config(bg='#388e3c')
    
    def _on_leave(self, e):
        if self['state'] != tk.DISABLED:
            self.config(bg=self.default_bg)

class DisabilityAssessmentUI:
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("מערכת הערכת נכות - ביטוח לאומי")
        self.root.geometry("950x700")
        self.root.configure(bg="#f5f5f5")
        
        # הגדרת צבעים
        self.colors = {
            'primary': '#2e7d32',
            'primary_dark': '#1b5e20',
            'primary_light': '#4caf50',
            'secondary': '#81c784',
            'bg_light': '#e8f5e9',
            'bg_card': '#ffffff',
            'text_dark': '#212121',
            'text_light': '#757575',
            'success': '#4caf50',
            'error': '#f44336',
            'warning': '#ff9800'
        }
        
        self.input_dir = None
        self._create_widgets()
        self._center_window()
    
    def _center_window(self):
        """ממרכז את החלון במסך"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def _create_widgets(self):
        header_frame = tk.Frame(self.root, bg=self.colors['primary'], height=120)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text="🏥 מערכת הערכת נכות רפואית",
            font=("Segoe UI", 22, "bold"),
            bg=self.colors['primary'],
            fg="white"
        )
        title_label.pack(pady=(25, 5))
        
        subtitle_label = tk.Label(
            header_frame,
            text="המוסד לביטוח לאומי • ניתוח מסמכים רפואיים מבוסס AI",
            font=("Segoe UI", 11),
            bg=self.colors['primary'],
            fg="white"
        )
        subtitle_label.pack()
        
        main_frame = tk.Frame(self.root, bg="#f5f5f5")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)
        
        self._create_section(
            main_frame,
            "📂 בחירת תיקיית מסמכים",
            self._create_file_selector
        )
        
        self._create_section(
            main_frame,
            "⚙️ סטטוס מערכת",
            self._create_system_status
        )
        
        button_frame = tk.Frame(main_frame, bg="#f5f5f5")
        button_frame.pack(pady=20)
        
        self.start_button = ModernButton(
            button_frame,
            text="🔬 התחל ניתוח רפואי",
            command=self._start_processing,
            bg=self.colors['primary'],
            fg="white",
            state=tk.DISABLED,
            height=2,
            width=30,
            font=("Segoe UI", 13, "bold")
        )
        self.start_button.pack()
        
        self.progress_frame = tk.Frame(main_frame, bg="#f5f5f5")
        self.progress_frame.pack(pady=10, fill=tk.X)
        
        self.progress_label = tk.Label(
            self.progress_frame,
            text="",
            font=("Segoe UI", 10),
            bg="#f5f5f5",
            fg=self.colors['primary']
        )
        self.progress_label.pack()
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(
            "green.Horizontal.TProgressbar",
            troughcolor='#e0e0e0',
            bordercolor='#e0e0e0',
            background=self.colors['primary'],
            lightcolor=self.colors['primary_light'],
            darkcolor=self.colors['primary_dark']
        )
        
        self.progress = ttk.Progressbar(
            self.progress_frame,
            length=700,
            mode='indeterminate',
            style="green.Horizontal.TProgressbar"
        )
        self.progress.pack(pady=5)
        self.progress_frame.pack_forget()  
        # === Log Section ===
        log_container = tk.Frame(main_frame, bg="#f5f5f5")
        log_container.pack(pady=10, fill=tk.BOTH, expand=True)
        
        log_header = tk.Label(
            log_container,
            text="📋 יומן עיבוד",
            font=("Segoe UI", 12, "bold"),
            bg="#f5f5f5",
            fg=self.colors['text_dark'],
            anchor='w'
        )
        log_header.pack(fill=tk.X, pady=(0, 5))
        
        log_frame = tk.Frame(log_container, bg="#263238", relief=tk.SOLID, borderwidth=1)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(
            log_frame,
            height=12,
            width=100,
            state=tk.DISABLED,
            bg="#263238",
            fg="#a5d6a7",
            font=("Consolas", 9),
            relief=tk.FLAT,
            padx=10,
            pady=10
        )
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure tags for colored output
        self.log_text.tag_config("success", foreground="#81c784")
        self.log_text.tag_config("error", foreground="#ef5350")
        self.log_text.tag_config("info", foreground="#64b5f6")
        self.log_text.tag_config("warning", foreground="#ffb74d")
        self.log_text.tag_config("header", foreground="#fff9c4", font=("Consolas", 9, "bold"))
        
        scrollbar = tk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        self._log("» מערכת מוכנה לעיבוד מסמכים רפואיים", "info")
    
    def _create_section(self, parent, title, content_creator):
        """יוצר section עם כותרת ותוכן"""
        section_frame = tk.Frame(parent, bg="#f5f5f5")
        section_frame.pack(fill=tk.X, pady=10)
        
        title_label = tk.Label(
            section_frame,
            text=title,
            font=("Segoe UI", 12, "bold"),
            bg="#f5f5f5",
            fg=self.colors['primary'],
            anchor='w'
        )
        title_label.pack(fill=tk.X, pady=(0, 8))
        
        content_frame = tk.Frame(
            section_frame,
            bg=self.colors['bg_card'],
            relief=tk.FLAT,
            borderwidth=0
        )
        content_frame.pack(fill=tk.X)
        
        # Add subtle shadow effect
        shadow_frame = tk.Frame(section_frame, bg="#e0e0e0", height=2)
        shadow_frame.pack(fill=tk.X)
        
        content_creator(content_frame)
    
    def _create_file_selector(self, parent):
        """יוצר את מבחר התיקיות"""
        inner_frame = tk.Frame(parent, bg=self.colors['bg_card'])
        inner_frame.pack(fill=tk.X, padx=20, pady=15)
        
        # File selector button
        self.file_button = tk.Button(
            inner_frame,
            text="📁 בחר תיקייה",
            command=self._select_directory,
            bg=self.colors['bg_light'],
            fg=self.colors['text_dark'],
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=20,
            pady=10
        )
        self.file_button.pack(side=tk.RIGHT)
        
        # Label for selected directory
        label_frame = tk.Frame(inner_frame, bg=self.colors['bg_card'])
        label_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        tk.Label(
            label_frame,
            text="תיקייה נבחרת:",
            font=("Segoe UI", 10),
            bg=self.colors['bg_card'],
            fg=self.colors['text_light']
        ).pack(anchor='w')
        
        self.dir_label = tk.Label(
            label_frame,
            text="לא נבחרה תיקייה",
            font=("Segoe UI", 10, "bold"),
            bg=self.colors['bg_card'],
            fg=self.colors['text_light'],
            anchor='w'
        )
        self.dir_label.pack(anchor='w', pady=(3, 0))
    
    def _create_system_status(self, parent):
        """יוצר את תצוגת סטטוס המערכת"""
        inner_frame = tk.Frame(parent, bg=self.colors['bg_card'])
        inner_frame.pack(fill=tk.X, padx=20, pady=15)
        
        # RAG Status
        self._create_status_item(
            inner_frame,
            "בסיס נתונים רפואי (RAG)",
            Config.RAG_FILE.exists()
        )
        
        # AI Engine Status
        self._create_status_item(
            inner_frame,
            "מנוע בינה מלאכותית",
            True
        )
        
        # OCR Status
        self._create_status_item(
            inner_frame,
            "מערכת OCR",
            True
        )
    
    def _create_status_item(self, parent, label, is_active):
        """יוצר פריט סטטוס בודד"""
        item_frame = tk.Frame(parent, bg="#f5f5f5", relief=tk.FLAT)
        item_frame.pack(fill=tk.X, pady=5)
        
        # Label
        tk.Label(
            item_frame,
            text=label,
            font=("Segoe UI", 10),
            bg="#f5f5f5",
            fg=self.colors['text_dark'],
            anchor='w'
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=10)
        
        # Status badge
        status_text = "✓ מחובר" if is_active else "✗ לא זמין"
        status_bg = "#c8e6c9" if is_active else "#ffcdd2"
        status_fg = "#1b5e20" if is_active else "#b71c1c"
        
        status_label = tk.Label(
            item_frame,
            text=status_text,
            font=("Segoe UI", 9, "bold"),
            bg=status_bg,
            fg=status_fg,
            padx=12,
            pady=5
        )
        status_label.pack(side=tk.RIGHT, padx=10)
    
    def _select_directory(self):
        """בחירת תיקייה"""
        directory = filedialog.askdirectory(title="בחר תיקייה עם מסמכים רפואיים")
        if directory:
            self.input_dir = Path(directory)
            self.dir_label.config(
                text=str(self.input_dir),
                fg=self.colors['primary']
            )
            self._check_ready()
            self._log(f"✓ תיקייה נבחרה: {self.input_dir.name}", "success")
    
    def _check_ready(self):
        """בדיקה אם אפשר להתחיל"""
        if self.input_dir and Config.RAG_FILE.exists():
            self.start_button.config(state=tk.NORMAL)
        elif self.input_dir and not Config.RAG_FILE.exists():
            messagebox.showerror("שגיאה", f"קובץ RAG לא נמצא ב:\n{Config.RAG_FILE}")
    
    def _start_processing(self):
        """התחלת העיבוד"""
        self.start_button.config(state=tk.DISABLED)
        self.progress_frame.pack(pady=10, fill=tk.X)
        self.progress_label.config(text="מבצע עיבוד רפואי...")
        self.progress.start(10)
        
        thread = Thread(target=self._run_processing)
        thread.daemon = True
        thread.start()
    
    def _run_processing(self):
        """תהליך עיבוד משופר"""
        try:
            self._log("=" * 60, "header")
            self._log("מתחיל תהליך ניתוח רפואי", "info")
            self._log("=" * 60, "header")
            
            ocr_dir = self.input_dir / "ocr_txt"
            json_dir = Config.OUTPUT_DIR / "extracted_json"
            consolidated_file = json_dir / "all_medical_data_consolidated.json"
            
            medical_data = None

            if consolidated_file.exists():
                self._log(f"נמצא קובץ נתונים מאוחד: {consolidated_file.name}", "info")
                use_existing = messagebox.askyesno(
                    "נתונים קיימים",
                    "נמצא קובץ אבחנות רפואיות מוכן.\nהאם להשתמש בו ולדלג לניתוח אחוזי הנכות?"
                )
                
                if use_existing:
                    with open(consolidated_file, 'r', encoding='utf-8') as f:
                        medical_data = json.load(f)
                    self._log("✓ טוען נתונים מקובץ קיים", "success")

            if medical_data is None:
                existing_txt = list(ocr_dir.glob("*.txt")) if ocr_dir.exists() else []
                if existing_txt:
                    self._log(f"נמצאו {len(existing_txt)} קבצי טקסט קיימים", "info")
                    ocr_response = messagebox.askyesno(
                        "קבצי טקסט קיימים",
                        "נמצאו קבצי טקסט מעיבוד קודם.\nלהשתמש בהם במקום להריץ OCR מחדש?"
                    )
                    if ocr_response:
                        txt_files = existing_txt
                    else:
                        txt_files, failed = self._run_ocr()
                else:
                    self._log("שלב 1/4: מבצע OCR על המסמכים...", "info")
                    txt_files, failed = self._run_ocr()

                if not txt_files:
                    raise Exception("לא נמצאו קבצי טקסט לעיבוד")

                # חילוץ JSON
                self._log("שלב 2/4: חילוץ מידע רפואי באמצעות AI...", "info")
                ai_client = OpenAIClient(api_key=Config.OPENAI_API_KEY, model=Config.GPT_MODEL)
                extractor = MedicalJSONExtractor(ai_client)
                
                json_dir.mkdir(exist_ok=True)
                medical_data = extractor.extract_from_directory(ocr_dir, json_dir)
                self._log("✓ חילוץ מידע הושלם", "success")

            if not medical_data or not medical_data.get('diagnoses_by_body_part'):
                raise Exception("לא נמצאו אבחנות רפואיות בנתונים")

            self._log("שלב 3/4: טעינת בסיס נתונים רפואי (RAG)...", "info")
            rag = self._load_rag()

            self._log("שלב 4/4: ניתוח והערכת אחוזי נכות...", "info")
            
            if 'ai_client' not in locals():
                ai_client = OpenAIClient(api_key=Config.OPENAI_API_KEY, model=Config.GPT_MODEL)
                
            analyzer = DisabilityAnalyzer(ai_client, rag)
            results = analyzer.analyze_patient_data(medical_data)
            self._log("✓ חישוב אחוזי נכות הושלם", "success")

            results_file = Config.OUTPUT_DIR / "final_disability_assessment.json"
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

            report = self._generate_report(results)
            report_file = Config.OUTPUT_DIR / "disability_report.txt"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)

            self._log("=" * 60, "header")
            self._log("✓✓✓ התהליך הושלם בהצלחה ✓✓✓", "success")
            self._log(f"תוצאות נשמרו ב: {results_file.name}", "info")
            self._log(f"דוח נשמר ב: {report_file.name}", "info")
            self._log("=" * 60, "header")

            self._log("\n📊 סיכום נכות:", "header")
            for item in results.get('breakdown', []):
                self._log(f"  • {item['organ']}: {item['percent']}% (סעיף {item['section']})", "info")
            self._log(f"\n💚 סה\"כ נכות משוקללת: {results.get('total_disability', 0)}%", "success")

            missing_info_items = [
                r for r in results.get('full_results', []) 
                if float(r.get('disability_percentage', 0)) == 0
            ]

            if missing_info_items:
                self._log("\n⚠️  איברים הדורשים מידע נוסף:", "warning")
                for item in missing_info_items:
                    reason = item.get('reasoning', 'נדרש תיעוד רפואי נוסף')
                    self._log(f"  • {item['body_part']}: {reason}", "warning")

            self.root.after(0, self._processing_complete)

        except Exception as e:
            self._log(f"\n❌ שגיאה: {str(e)}", "error")
            import traceback
            self._log(traceback.format_exc(), "error")
            self.root.after(0, self._processing_error)
    
    def _run_ocr(self) -> Tuple[List[Path], List[Path]]:
        """מריץ OCR"""
        ocr = OCRProcessor(
            tesseract_path=Config.TESSERACT_PATH,
            languages=Config.OCR_LANGUAGES
        )
        ocr_dir = self.input_dir / "ocr_txt"
        successful, failed = ocr.process_directory(self.input_dir, ocr_dir)
        
        self._log(f"✓ OCR הושלם: {len(successful)} הצליחו, {len(failed)} נכשלו", "success")
        
        if failed:
            self._log("קבצים שנכשלו:", "warning")
            for f in failed:
                self._log(f"  • {f.name}", "warning")
        
        return successful, failed
    
    def _load_rag(self) -> RAGSystem:
        """טוען RAG"""
        with open(Config.RAG_FILE, 'r', encoding='utf-8') as f:
            rag_data = json.load(f)
        
        texts = []
        metadata = []
        
        if isinstance(rag_data, dict):
            for key, value in rag_data.items():
                text = json.dumps(value, ensure_ascii=False) if isinstance(value, dict) else str(value)
                texts.append(text)
                metadata.append({'section_number': key, 'title': key})
        
        elif isinstance(rag_data, list):
            for i, item in enumerate(rag_data):
                if isinstance(item, dict):
                    text = json.dumps(item, ensure_ascii=False)
                    section_id = item.get('id') or item.get('section') or f"section_{i}"
                    title = item.get('title') or section_id
                else:
                    text = str(item)
                    section_id = f"section_{i}"
                    title = section_id
                
                texts.append(text)
                metadata.append({'section_number': section_id, 'title': title})
        
        rag = RAGSystem(model_path=Config.EMBEDDING_MODEL)
        rag.build_index(texts, metadata)
        
        self._log(f"✓ RAG נטען: {len(texts)} רשומות", "success")
        return rag
    
    def _generate_report(self, results: dict) -> str:
        """יצירת דוח"""
        report = f"""
╔══════════════════════════════════════════════════════════════════╗
║              דוח הערכת נכות - ביטוח לאומי                       ║
╚══════════════════════════════════════════════════════════════════╝

תאריך: {datetime.now().strftime('%d/%m/%Y %H:%M')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
אחוזי נכות לפי איברים
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
        for item in results.get('breakdown', []):
            report += f"🔹 {item['organ']}: {item['percent']}% (סעיף {item['section']})\n"
        
        report += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
נכות מצטברת
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

סה"כ לפי נוסחת בלבנד: {results.get('total_disability', 0)}%

הערות:
1. זהו חישוב ראשוני - יש להתייעץ עם עו"ד מומחה
2. נדרשת בדיקת חפיפות בין פגיעות
3. החישוב דורש אישור רפואי מוסמך

"""
        
        missing_info_items = [
            r for r in results.get('full_results', []) 
            if float(r.get('disability_percentage', 0)) == 0
        ]
        
        if missing_info_items:
            report += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  איברים הדורשים התייחסות רפואית נוספת (0%)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
            for item in missing_info_items:
                report += f"🔸 {item['body_part']}\n"
                reason = item.get('reasoning', 'נדרש תיעוד רפואי נוסף')
                report += f"   הנחיה: {reason}\n\n"
        
        return report
    
    def _log(self, message: str, tag: str = ""):
        """הוספת הודעה ללוג"""
        def append():
            self.log_text.config(state=tk.NORMAL)
            if tag:
                self.log_text.insert(tk.END, message + "\n", tag)
            else:
                self.log_text.insert(tk.END, message + "\n")
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        
        self.root.after(0, append)
    
    def _processing_complete(self):
        """סיום מוצלח"""
        self.progress.stop()
        self.progress_frame.pack_forget()
        self.start_button.config(state=tk.NORMAL)
        messagebox.showinfo(
            "הצלחה",
            "✓ התהליך הושלם בהצלחה!\n\nהתוצאות נשמרו בתיקיית output"
        )
    
    def _processing_error(self):
        """שגיאה"""
        self.progress.stop()
        self.progress_frame.pack_forget()
        self.start_button.config(state=tk.NORMAL)
        messagebox.showerror(
            "שגיאה",
            "❌ אירעה שגיאה בעיבוד\nראה יומן לפרטים"
        )
    
    def run(self):
        """הרצת הממשק"""
        self.root.mainloop()


if __name__ == "__main__":
    app = DisabilityAssessmentUI()
    app.run()