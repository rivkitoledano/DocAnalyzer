
# ============================================================================
# main.py - נקודת כניסה
# ============================================================================

from pathlib import Path
from config import Config
from ui import DisabilityAssessmentUI


def main():
    """נקודת כניסה"""
    
    if not Config.OPENAI_API_KEY:
        print(" חסר API Key של OpenAI!")
        print("צור קובץ .env עם:")
        print("OPENAI_API_KEY=your-key-here")
        return
    
    if not Config.RAG_FILE.exists():
        print(f" קובץ RAG לא נמצא ב:")
        print(f"   {Config.RAG_FILE}")
        print("\nוודא שהנתיב נכון ב-config.py")
        return
    
    if not Path(Config.TESSERACT_PATH).exists():
        print("  Tesseract לא נמצא!")
        print(f"עדכן את הנתיב ב-config.py או התקן מ:")
        print("https://github.com/UB-Mannheim/tesseract/wiki")
        response = input("\nלהמשיך בכל זאת? (y/n): ")
        if response.lower() != 'y':
            return
    
    print("\n" + "="*70)
    print("🏥 מערכת הערכת נכות - ביטוח לאומי".center(70))
    print("="*70 + "\n")
    
    ui = DisabilityAssessmentUI()
    ui.run()


if __name__ == "__main__":
    print("התחלת התוכנית...\n")
    main()


