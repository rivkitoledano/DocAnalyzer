# ============================================================================
# config.py
# ============================================================================

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
    """הגדרות גלובליות"""
    
    # API Keys
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Models
    EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    GPT_MODEL = "gpt-4o"
    
    # RAG Settings
    DEFAULT_TOP_K = 6
    MAX_CHUNK_SIZE = 2000
    
    # Paths
    PROJECT_ROOT = Path(__file__).parent
    OUTPUT_DIR = PROJECT_ROOT / "output"
    RAG_FILE = Path(r"C:\Users\user1\Documents\justice\rag.json") 
    
    # OCR Settings
    TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    OCR_LANGUAGES = "heb+eng"
    
    # Retry settings
    MAX_RETRIES = 2 
    
    # Ensure directories exist
    OUTPUT_DIR.mkdir(exist_ok=True)
