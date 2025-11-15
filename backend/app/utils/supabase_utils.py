# backend/app/utils/supabase_utils.py

import os
import time
from supabase import create_client, Client


# -------------------------------------------------------------
# Load required environment variables
# -------------------------------------------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise EnvironmentError(
        "❌ Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in environment."
    )

# -------------------------------------------------------------
# Initialize Client (sync only)
# -------------------------------------------------------------
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    raise RuntimeError(f"❌ Failed to initialize Supabase client: {e}")


# -------------------------------------------------------------
# Clean path helper
# -------------------------------------------------------------
def _clean_path(path: str) -> str:
    p = str(path).replace("\r", "").replace("\n", "")
    while "//" in p:
        p = p.replace("//", "/")
    return p.lstrip("/")


# -------------------------------------------------------------
# SYNC Upload helper
# -------------------------------------------------------------
def supabase_upload(file_bytes: bytes, path: str, content_type: str = "image/jpeg") -> str:
    """
    Fully synchronous Supabase uploader.
    Ensures the return value is ALWAYS a real string (not coroutine).
    """

    path = _clean_path(path)
    path = path.lstrip("/")
    path = path.replace(" ", "_")

    print(f"⬆ Uploading to Supabase → {path}")

    max_retries = 3
    for attempt in range(1, max_retries + 1):

        try:
            res = supabase.storage.from_(SUPABASE_BUCKET).upload(
                path,
                file_bytes,
                {"content-type": content_type, "x-upsert": "true"}
            )

            # For older versions: response may be a dict containing error
            if isinstance(res, dict) and res.get("error"):
                raise RuntimeError(res["error"])

            # Generate public URL (ALWAYS sync)
            pub = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(path)

            if isinstance(pub, dict) and pub.get("publicUrl"):
                public_url = pub["publicUrl"]
            elif isinstance(pub, dict) and pub.get("url"):
                public_url = pub["url"]
            else:
                # Fallback deterministic URL
                public_url = (
                    f"{SUPABASE_URL}/storage/v1/object/public/"
                    f"{SUPABASE_BUCKET}/{path}"
                )

            print(f"✔ Uploaded → {public_url}")
            return public_url

        except Exception as e:
            print(f"Upload attempt {attempt}/{max_retries} failed: {e}")
            if attempt < max_retries:
                time.sleep(attempt * 1)
            else:
                raise RuntimeError(f"❌ Supabase upload failed: {e}")
