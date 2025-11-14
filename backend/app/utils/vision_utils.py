"""
Local OCR engine using Tesseract or fallback to GPT OCR
-------------------------------------------------------
No Google Cloud required.
"""

import io
import os
import pytesseract
from PIL import Image
from typing import Optional

# ----------------------------------------------------------
# 1. OPTIONAL: Windows Tesseract path fix
# ----------------------------------------------------------
# If you installed Tesseract normally from:
# https://github.com/UB-Mannheim/tesseract/wiki
# uncomment the next line and put your path:
#
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# ----------------------------------------------------------


# ----------------------------------------------------------
# 2. Simple OCR function (LOCAL)
# ----------------------------------------------------------
def ocr_image_bytes(img_bytes: bytes) -> str:
    """
    Local OCR using pytesseract.
    Super fast, no external API required.
    """
    try:
        image = Image.open(io.BytesIO(img_bytes))
        text = pytesseract.image_to_string(image)
        return text.strip()
    except Exception as e:
        print("OCR failed:", e)
        return ""


# ----------------------------------------------------------
# 3. (Optional) Language detection
# ----------------------------------------------------------
def detect_language(text: str) -> str:
    if not text.strip():
        return "unknown"

    # very naive language detection
    if any(char in "अआइईउऊएऐओऔकखगघङचछजझञटठडढणतथदधन" for char in text):
        return "hi"

    return "en"
