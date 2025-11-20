"""
Gemini (Google AI Studio) replacement for OpenAI multimodal script generation.

This version keeps:
✔ The SAME function name: generate_cinematic_script
✔ The SAME arguments
✔ The SAME return structure
✔ The SAME helpers (validate_scene, fallback_script, JSON extraction)
✔ Debug logs
✔ Minimal changes to rest of backend

Just swap OpenAI → Google AI Studio.

Requires:
    pip install google-generativeai

Env var:
    GOOGLE_API_KEY=xxxxxx
"""

import os
import re
import json
import base64
import traceback
import logging
from typing import Dict, Any, List, Optional

# Google AI SDK (Gemini)
try:
    import google.generativeai as genai
except Exception:
    raise RuntimeError(
        "Google AI SDK missing. Install: pip install google-generativeai"
    )

from app.config import GOOGLE_API_KEY   # YOU MUST add this in config!

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("google_ai_utils")

# Initialize Google Gemini client
if not GOOGLE_API_KEY:
    raise EnvironmentError("Missing GOOGLE_API_KEY in app.config or .env")

genai.configure(api_key=GOOGLE_API_KEY)

# You can change the model here if needed:
# Recommended small + cheap multimodal model:
GEMINI_MODEL = os.getenv("MANHWA_LLM_MODEL", "gemini-2.0-flash-lite")


# ---------------------------------------------------------
# Reuse your helper logic exactly as before
# ---------------------------------------------------------
def _safe_base64(img_bytes: bytes) -> str:
    return base64.b64encode(img_bytes).decode("utf-8")


def _extract_json_from_text(raw: str) -> Optional[str]:
    if not raw:
        return None

    raw = raw.strip()

    if raw.startswith("{") and raw.endswith("}"):
        return raw

    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        return raw[start:end + 1]

    m = re.search(r"\{[\s\S]*\}", raw)
    if m:
        return m.group(0)

    return None


def validate_scene(scene: Dict[str, Any], index: int) -> bool:
    if not isinstance(scene, dict):
        return False
    if "narration_segment" not in scene or "image_page_index" not in scene:
        return False
    if not isinstance(scene["narration_segment"], str):
        return False
    if not isinstance(scene["image_page_index"], int):
        return False
    return True


def fallback_script(name: str, ocr: str) -> Dict[str, Any]:
    short = (ocr or "").strip()[:240]
    return {
        "full_narration": f"Yeh {name} ki kahani hai. {short}...",
        "scenes": [
            {
                "narration_segment": f"{name} ka short intro: {short}",
                "image_page_index": 0
            }
        ]
    }


# ---------------------------------------------------------
# MAIN FUNCTION — Gemini multimodal replacement
# ---------------------------------------------------------
def generate_cinematic_script(
    manga_name: str,
    manga_genre: str,
    ocr_data: str,
    image_bytes_list: List[bytes],
    max_scenes: int = 200
) -> Dict[str, Any]:

    logger.info("→ Preparing multimodal content for Gemini...")
    MAX_IMAGES_TO_LLM = 50
    if len(image_bytes_list) > MAX_IMAGES_TO_LLM:
        print(f"⚠ Limiting {len(image_bytes_list)} images → {MAX_IMAGES_TO_LLM} for LLM")
        # Take evenly distributed samples
        indices = np.linspace(0, len(image_bytes_list)-1, MAX_IMAGES_TO_LLM, dtype=int)
        image_bytes_list = [image_bytes_list[i] for i in indices]
    
    logger.info(f"→ Sending {len(image_bytes_list)} images to Gemini...")

    # Build the master instruction
    MANHWA_RULES = f"""
Tum ek popular 'Manhwa Explainer' YouTuber ho.

RULES:
1. Language → Hinglish (zyada Hindi, friendly tone)
2. Tense → Present tense narration
3. Har panel ke liye ek "scene" object banao
4. Har panel ke visuals ko clearly explain karo
5. Dialogue + Internal thoughts ko narration me merge karo
6. Script engaging ho → jaise dost ko story suna rahe ho
7. Sirf VALID JSON return karna (no text, no markdown)

OUTPUT JSON FORMAT:
{{
  "full_narration": "string",
  "scenes": [
    {{
      "narration_segment": "string",
      "image_page_index": 0
    }}
  ]
}}

Manga: {manga_name}
Genre: {manga_genre}
    """

    # OCR split
    if ocr_data:
        ocr_pages = ocr_data.split("\n\n--- PAGE BREAK ---\n\n")
    else:
        ocr_pages = []

    # Build the input list for Gemini
    contents = [
        {"role": "user", "parts": [{"text": MANHWA_RULES}]}
    ]

    # Add all images + OCR combos exactly like OpenAI version
    for idx, img_bytes in enumerate(image_bytes_list):
        try:
            b64 = _safe_base64(img_bytes)
            contents[0]["parts"].append(
                {"inline_data": {"mime_type": "image/jpeg", "data": b64}}
            )
        except:
            logger.warning(f"Could not base64 image {idx}")

        panel_text = ocr_pages[idx] if idx < len(ocr_pages) else ""
        contents[0]["parts"].append(
            {"text": f"[PANEL {idx}] OCR:\n{panel_text}\nExplain this panel."}
        )

    # Final instruction at end
    contents[0]["parts"].append(
        {"text": "Return ONLY JSON. No markdown."}
    )

    # ----------------------------
    # Gemini API CALL
    # ----------------------------
    try:
        logger.info(f"Calling Gemini model: {GEMINI_MODEL}")

        response = genai.GenerativeModel(GEMINI_MODEL).generate_content(
            contents,
            generation_config={
                "temperature": 0.4,
                "max_output_tokens": 4096,
                "response_mime_type": "application/json"
            }
        )

        # Gemini returns .text representing JSON if mime type is application/json
        raw = response.text
        if not raw:
            raw = str(response)

        json_str = _extract_json_from_text(raw)
        if json_str is None:
            logger.error("JSON extraction failed from Gemini output")
            return fallback_script(manga_name, ocr_data)

        candidate = json.loads(json_str)

        if "scenes" not in candidate or "full_narration" not in candidate:
            return fallback_script(manga_name, ocr_data)

        scenes = candidate["scenes"]
        if not isinstance(scenes, list) or not scenes:
            return fallback_script(manga_name, ocr_data)

        # Validate + sanitize scenes
        validated_scenes = []
        img_count = max(1, len(image_bytes_list))

        for i, s in enumerate(scenes):
            if len(validated_scenes) >= max_scenes:
                break
            if not validate_scene(s, i):
                continue

            idx = s["image_page_index"]
            if idx < 0 or idx >= img_count:
                idx = 0

            validated_scenes.append({
                "narration_segment": s["narration_segment"].strip(),
                "image_page_index": int(idx)
            })

        if not validated_scenes:
            return fallback_script(manga_name, ocr_data)

        logger.info(f"[SUCCESS] Gemini generated {len(validated_scenes)} scenes.")
        return {
            "full_narration": candidate.get("full_narration", "").strip(),
            "scenes": validated_scenes
        }

    except Exception as e:
        logger.error("❌ Gemini multimodal failed:", e)
        traceback.print_exc()
        return fallback_script(manga_name, ocr_data)
