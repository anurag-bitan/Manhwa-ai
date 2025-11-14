# backend/app/utils/supabase_utils.py

import os
from supabase import create_client, Client
from typing import Optional
from app.config import TTS_CACHE_DIR


# -------------------------------------------------------------
# Load required environment variables
# -------------------------------------------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") 
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET")  

if not SUPABASE_URL or not SUPABASE_KEY:
    raise EnvironmentError(
        "❌ Missing SUPABASE_URL or SUPABASE_KEY in environment variables.\n"
        "Add them in backend/.env"
    )

# -------------------------------------------------------------
# Initialize Supabase client
# -------------------------------------------------------------
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    raise RuntimeError(f"❌ Failed to initialize Supabase client: {e}")


# -------------------------------------------------------------
# Helper: Upload bytes to Supabase Storage
# -------------------------------------------------------------
def supabase_upload(file_bytes: bytes, path: str, content_type: str) -> str:
    """
    Uploads a file to Supabase Storage and returns a public URL.

    Args:
        file_bytes (bytes): The file content
        path (str): Destination path inside bucket
        content_type (str): MIME type (image/jpeg, audio/mpeg)

    Returns:
        str: Public URL of the uploaded file
    """

    print(f"⬆ Uploading to Supabase → {path}")

    # Upload file into the bucket
    try:
        supabase.storage.from_(SUPABASE_BUCKET).upload(
            file=file_bytes,
            path=path,
            file_options={"content-type": content_type, "upsert": "true"}
        )
    except Exception as e:
        raise RuntimeError(f"❌ Supabase upload failed for {path}: {e}")

    # Generate PUBLIC URL
    try:
        public_url = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(path)
        print(f"✔ Uploaded → {public_url}")
        return public_url
    except Exception as e:
        raise RuntimeError(f"❌ Failed to generate public URL: {e}")
