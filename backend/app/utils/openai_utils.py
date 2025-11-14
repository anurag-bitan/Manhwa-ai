"""
Robust multimodal OpenAI helper for generating "Manhwa Explainer" scripts.

Key improvements over the original:
 - Safer OpenAI client initialization with clear error message.
 - Defensive parsing of model output (handles string-wrapped JSON).
 - Validates scenes and clamps image indexes to available images.
 - Limits scene count to avoid overly large responses.
 - Graceful fallbacks if LLM fails or returns invalid structure.
 - Helpful debug prints for easier local troubleshooting.
"""

import os
import re
import json
import base64
import traceback
import logging
from typing import Dict, Any, List, Optional

# OpenAI client (newer official package)
try:
    from openai import OpenAI
except Exception:
    # older environments may not have the same package; raise informative error
    raise RuntimeError("OpenAI SDK not installed. Run: pip install openai (or the correct client package)")

from app.config import OPENAI_API_KEY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("openai_utils")

# Initialize OpenAI client with environment key (clear message if missing)
if not OPENAI_API_KEY:
    raise EnvironmentError("Missing OPENAI_API_KEY in app.config. Set your API key in the backend .env / config.")
client = OpenAI(api_key=OPENAI_API_KEY)

# Model choice (multimodal capable)
LLM_MODEL = os.getenv("MANHWA_LLM_MODEL", "gpt-4o-mini")

# Master prompt / rules (kept concise)
MANHWA_RULES = """
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
{
  "full_narration": "string",
  "scenes": [
    {
      "narration_segment": "string",
      "image_page_index": 0
    }
  ]
}
"""

# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------
def _safe_base64(img_bytes: bytes) -> str:
    """Return base64 string for image bytes. Small wrapper for clarity."""
    return base64.b64encode(img_bytes).decode("utf-8")


def _extract_json_from_text(raw: str) -> Optional[str]:
    """
    Try to extract a JSON object substring from possibly noisy model output.
    Returns None if extraction/parsing fails.
    """
    if not raw:
        return None

    raw = raw.strip()

    # If it already looks like JSON (startswith {), try directly
    if raw.startswith("{") and raw.endswith("}"):
        return raw

    # Try to find the first '{' and the matching '}' from the end
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        return raw[start:end + 1]

    # Last resort: try to match a top-level JSON using regex (balanced braces is hard, but this helps)
    m = re.search(r"\{[\s\S]*\}", raw)
    if m:
        return m.group(0)

    return None


def validate_scene(scene: Dict[str, Any], index: int) -> bool:
    """
    Validate scene has required fields and types.
    """
    if not isinstance(scene, dict):
        logger.debug(f"[scene {index}] invalid type: expected dict")
        return False

    if "narration_segment" not in scene or "image_page_index" not in scene:
        logger.debug(f"[scene {index}] missing keys")
        return False

    if not isinstance(scene["narration_segment"], str) or not scene["narration_segment"].strip():
        logger.debug(f"[scene {index}] invalid narration_segment")
        return False

    if not isinstance(scene["image_page_index"], int):
        logger.debug(f"[scene {index}] image_page_index not int")
        return False

    return True


def fallback_script(name: str, ocr: str) -> Dict[str, Any]:
    """Simple fallback when LLM doesn't produce acceptable output."""
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
# Main multimodal function
# ---------------------------------------------------------
def generate_cinematic_script(
    manga_name: str,
    manga_genre: str,
    ocr_data: str,
    image_bytes_list: List[bytes],
    max_scenes: int = 200
) -> Dict[str, Any]:
    """
    Construct a multimodal prompt (images + OCR pages) and call the LLM to
    produce a structured "Manhwa Explainer" JSON.
    Returns a dictionary with keys: 'full_narration' and 'scenes'.
    """

    logger.info("→ Preparing multimodal content for OpenAI...")

    # Basic safe-guards
    if not isinstance(image_bytes_list, list):
        image_bytes_list = []

    # Build messages
    system_message = {"role": "system", "content": MANHWA_RULES}

    user_blocks: List[Dict[str, Any]] = [
        {"type": "text", "text": f"Manga Name: {manga_name}\nGenre: {manga_genre}\nStart explaining panel-by-panel:"}
    ]

    # Break OCR into per-page pieces
    ocr_pages = []
    if ocr_data:
        ocr_pages = ocr_data.split("\n\n--- PAGE BREAK ---\n\n")
    else:
        ocr_pages = []

    # Attach images + OCR text (guarding indices)
    for i, img_bytes in enumerate(image_bytes_list):
        try:
            b64 = _safe_base64(img_bytes)
            user_blocks.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
        except Exception:
            # If base64 encoding fails, continue but log it
            logger.warning(f"→ Unable to encode image at index {i}, skipping image in prompt.")
            continue

        page_text = ocr_pages[i] if i < len(ocr_pages) else ""
        user_blocks.append({"type": "text", "text": f"[PANEL {i}] OCR:\n{page_text}\nExplain this panel with visuals, dialogue and internal thoughts."})

    user_blocks.append({"type": "text", "text": "Return final script in pure JSON only with the format {\"full_narration\":..., \"scenes\":[...] }."})

    user_message = {"role": "user", "content": user_blocks}

    # Call the model
    response_content = None
    try:
        logger.info(f"   [DEBUG] Calling OpenAI Multimodal API with model: {LLM_MODEL}")
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[system_message, user_message],
            temperature=0.45,
            max_tokens=3500,
            response_format={"type": "json_object"},
        )

        # response.choices[0].message.content may be a string or a structured object depending on client
        raw = None
        try:
            raw = response.choices[0].message.content
        except Exception:
            # fallback to str(response)
            raw = str(response)

        # If the SDK already returned a dict-like object, try returning it after validation
        if isinstance(raw, dict):
            candidate = raw
        else:
            # raw likely a string — try to extract JSON substring
            json_str = _extract_json_from_text(str(raw))
            if json_str is None:
                logger.debug("   [DEBUG] Could not extract JSON substring from model output.")
                return fallback_script(manga_name, ocr_data)
            try:
                candidate = json.loads(json_str)
            except Exception as e:
                logger.debug("   [DEBUG] json.loads failed on extracted substring: %s", e)
                return fallback_script(manga_name, ocr_data)

        # Validate top-level keys
        if not candidate or "full_narration" not in candidate or "scenes" not in candidate:
            logger.debug("   [DEBUG] Candidate missing required keys.")
            return fallback_script(manga_name, ocr_data)

        scenes = candidate.get("scenes", [])
        if not isinstance(scenes, list) or not scenes:
            logger.debug("   [DEBUG] 'scenes' is not a non-empty list.")
            return fallback_script(manga_name, ocr_data)

        # Validate and sanitize scenes
        validated_scenes = []
        for i, s in enumerate(scenes):
            if len(validated_scenes) >= max_scenes:
                logger.info("   [INFO] Reached max_scenes limit; truncating remaining scenes.")
                break

            if not validate_scene(s, i):
                logger.debug(f"   [DEBUG] Scene {i} failed validation; skipping.")
                continue

            # Clamp image index within available images
            image_count = max(1, len(image_bytes_list))
            page_index = s.get("image_page_index", 0)
            if page_index < 0:
                page_index = 0
            if page_index >= image_count:
                # map out-of-range indices to nearest valid index (preferably 0)
                logger.debug(f"   [DEBUG] Scene {i} image_page_index {s.get('image_page_index')} out-of-range; clamping to 0.")
                page_index = 0

            sanitized_scene = {
                "narration_segment": s["narration_segment"].strip(),
                "image_page_index": int(page_index)
            }

            validated_scenes.append(sanitized_scene)

        if not validated_scenes:
            logger.debug("   [DEBUG] No valid scenes after sanitization.")
            return fallback_script(manga_name, ocr_data)

        result = {
            "full_narration": candidate.get("full_narration", "").strip(),
            "scenes": validated_scenes
        }

        logger.info(f"   [SUCCESS] Generated and validated 'Manhwa Explainer' script with {len(validated_scenes)} scenes.")
        return result

    except Exception as e:
        logger.error("❌ Multimodal LLM failed: %s", e)
        traceback.print_exc()
        return fallback_script(manga_name, ocr_data)
