import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("❌ .env 파일에 GOOGLE_API_KEY가 없습니다.")

genai.configure(api_key=api_key)

class Config:
    MODEL_NAME = "gemini-2.5-pro" 
    
    GENERATION_CONFIG = {
        "temperature": 0.0,
        "response_mime_type": "application/json"
    }

    RAW_DATA_DIR = "data/raw"
    INDEX_DIR = "data/indices"