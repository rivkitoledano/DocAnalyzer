
# ============================================================================
# openai_client.py - Wrapper ל-OpenAI
# ============================================================================

import logging
import time
import json
from openai import OpenAI
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
class OpenAIClient:
    """Wrapper לקריאות OpenAI עם retry"""
    
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        logging.info(f"OpenAI client initialized with {model}")
    
    def call(self, prompt: str, system_prompt: str = None, 
        response_format: dict = None, temperature: float = 0) -> str:
        """קריאה ל-OpenAI עם retry"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        for attempt in range(3):
            try:
                params = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature
                }
                
                if response_format:
                    params["response_format"] = response_format
                
                response = self.client.chat.completions.create(**params)
                return response.choices[0].message.content.strip()
                
            except Exception as e:
                logging.warning(f"נסיון {attempt + 1} נכשל: {e}")
                if attempt < 2:
                    time.sleep(1 + attempt)
                else:
                    raise
        
        return ""
