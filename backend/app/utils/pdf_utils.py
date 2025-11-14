"""
High-quality Manga PDF → Image Panel Extractor
----------------------------------------------
Extracts:
  • full page images
  • AND individual manga panel crops (stacked vertically)
"""

import io
import cv2
import numpy as np
from typing import List
from pdf2image import convert_from_path
from PIL import Image, ImageOps, ImageFilter


# ----------------------------------------------------------
# 1. Convert PDF pages → high quality PIL images
# ----------------------------------------------------------
def _load_pdf_pages(pdf_path: str, dpi: int = 350, max_pages: int = 50) -> List[Image.Image]:
    pages = convert_from_path(
        pdf_path,
        dpi=dpi,
        first_page=1,
        last_page=max_pages,
        fmt="jpeg"
    )

    processed = []
    for img in pages:
        img = img.convert("RGB")
        img = ImageOps.autocontrast(img, cutoff=2)
        img = img.filter(ImageFilter.SHARPEN)
        processed.append(img)

    return processed


# ----------------------------------------------------------
# 2. Detect vertical manga panels using OpenCV
# ----------------------------------------------------------
def _extract_panels_from_page(pil_img: Image.Image) -> List[Image.Image]:
    """
    Detects manga panels top→bottom using edges + dilate + contours.
    """

    img = np.array(pil_img)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)

    # Edge detection
    edges = cv2.Canny(gray, 60, 120)

    # Connect borders
    kernel = np.ones((15, 15), np.uint8)
    dilated = cv2.dilate(edges, kernel, iterations=2)

    contours, _ = cv2.findContours(
        dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    panel_images = []
    H, W = gray.shape

    # Sort top → bottom
    contours = sorted(contours, key=lambda c: cv2.boundingRect(c)[1])

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)

        # Ignore tiny junk contours
        if h < H * 0.10:
            continue

        crop = img[y:y+h, x:x+w]
        pil_crop = Image.fromarray(crop).convert("RGB")
        pil_crop = ImageOps.autocontrast(pil_crop, cutoff=3)

        panel_images.append(pil_crop)

    # Fallback: return entire page
    if not panel_images:
        return [pil_img]

    return panel_images


# ----------------------------------------------------------
# 3. Convert PIL Images → JPEG bytes
# ----------------------------------------------------------
def _pil_to_jpeg_bytes(images: List[Image.Image]) -> List[bytes]:
    out = []
    for img in images:
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        out.append(buf.getvalue())
    return out


# ----------------------------------------------------------
# OLD FUNCTION → Returns bytes (kept for compatibility)
# ----------------------------------------------------------
def pdf_to_images(pdf_path: str) -> List[bytes]:
    pages = _load_pdf_pages(pdf_path)

    all_panels: List[Image.Image] = []
    for page in pages:
        all_panels.extend(_extract_panels_from_page(page))

    print(f"✔ Extracted {len(all_panels)} total panels")
    return _pil_to_jpeg_bytes(all_panels)


# =====================================================================
# NEW REQUIRED FUNCTION — EXACT NAME IMPORTED BY YOUR BACKEND
# =====================================================================
def extract_pdf_images_high_quality(
    pdf_path: str,
    dpi: int = 350,
    max_pages: int = 50
) -> List[Image.Image]:
    """
    Wrapper used by generate_audio_story.py
    Returns LIST OF PIL IMAGES (not bytes)
    """

    pages = _load_pdf_pages(pdf_path, dpi=dpi, max_pages=max_pages)

    all_panels: List[Image.Image] = []
    for page in pages:
        all_panels.extend(_extract_panels_from_page(page))

    print(f"✔ extract_pdf_images_high_quality() → {len(all_panels)} panels")

    return all_panels
