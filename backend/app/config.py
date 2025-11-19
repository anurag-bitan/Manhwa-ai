# backend/app/config.py

"""
Central configuration loader for the backend.
Loads all required environment variables safely.
"""

import os
from dotenv import load_dotenv

# Load .env from backend/.env
load_dotenv()

# -----------------------------
# OPENAI
# -----------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise EnvironmentError("❌ Missing OPENAI_API_KEY in backend/.env")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise EnvironmentError("❌ Missing GOOGLE_API_KEY in backend/.env")
# -----------------------------
# SUPABASE
# -----------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")   # 🔥 USE SERVICE ROLE KEY
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "Manhwa_ai")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise EnvironmentError("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")


# -----------------------------
# GOOGLE OCR
# -----------------------------
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# -----------------------------
# TTS CACHE
# -----------------------------
TTS_CACHE_DIR = os.path.join(os.getcwd(), "tts_cache")
os.makedirs(TTS_CACHE_DIR, exist_ok=True)


# -----------------------------
# TEMP DIRS
# -----------------------------
TEMP_DIR = os.path.join(os.getcwd(), "temp")
os.makedirs(TEMP_DIR, exist_ok=True)
