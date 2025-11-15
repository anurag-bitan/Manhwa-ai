# backend/app/routers/generate_audio_story.py
import asyncio
import io
import os
import tempfile
import traceback
from typing import List

from fastapi import APIRouter, Form, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from pydub import AudioSegment

# --- Storage uploader ---
from ..utils.supabase_utils import supabase_upload

# --- PDF extraction ---
from ..utils.pdf_utils import extract_pdf_images_high_quality

# --- OCR ---
from ..utils.vision_utils import ocr_image_bytes

# --- TTS ---
from ..utils.tts_utils import generate_narration_audio

# --- LLM ---
from ..utils.openai_utils import generate_cinematic_script

router = APIRouter()


# ------------------------------------------------------
# Convert PIL Images → list[bytes] (jpeg)
# ------------------------------------------------------
def pil_images_to_bytes(images: List) -> List[bytes]:
    out = []
    for img in images:
        buf = io.BytesIO()
        img.save(buf, format="JPEG", optimize=True, quality=90)
        out.append(buf.getvalue())
    return out


# ------------------------------------------------------
# MAIN ENDPOINT
# ------------------------------------------------------
@router.post("/generate_audio_story")
async def generate_audio_story(
    manga_name: str = Form(...),
    manga_genre: str = Form(...),
    manga_pdf: UploadFile = File(...)
):
    temp_pdf_path = None
    merged_audio_tmp = None

    # Folder-safe version
    manga_folder = manga_name.replace(" ", "_").replace("/", "_").lower()

    try:
        # ------------------------------------------------------
        # STEP 1 — Save PDF temporarily
        # ------------------------------------------------------
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(await manga_pdf.read())
            temp_pdf_path = tmp.name

        print("✔ PDF saved, starting high-quality image extraction")

        # ------------------------------------------------------
        # STEP 2 — Extract high-quality images
        # ------------------------------------------------------
        images = await run_in_threadpool(extract_pdf_images_high_quality, temp_pdf_path)

        if not images:
            raise HTTPException(400, "No images extracted from PDF")

        image_bytes = pil_images_to_bytes(images)
        print(f"✔ Extracted {len(image_bytes)} images from PDF")
        # ------------------------------------------------------
        # NEW STEP: upload preview images immediately
        # ------------------------------------------------------
        print("✔ Uploading preview images (instant frontend display)...")

        preview_upload_jobs = []
        for idx, img in enumerate(image_bytes):
            preview_path = f"{manga_folder}/preview/page_{idx:02d}.jpg"
            preview_upload_jobs.append(
                run_in_threadpool(supabase_upload, img, preview_path, "image/jpeg")
            )

        preview_image_urls = await asyncio.gather(*preview_upload_jobs)

        # Return preview immediately (frontend uses these)
        # Do not stop processing — continue with OCR/LLM/TTS in same request

        # ------------------------------------------------------
        # STEP 3 — OCR each page
        # ------------------------------------------------------
        print("✔ Running OCR on all pages...")
        ocr_jobs = [run_in_threadpool(ocr_image_bytes, b) for b in image_bytes]
        ocr_results = await asyncio.gather(*ocr_jobs)

        extracted_text = "\n\n--- PAGE BREAK ---\n\n".join([t for t in ocr_results if t])
        print("✔ OCR completed")

        # ------------------------------------------------------
        # STEP 4 — Generate LLM cinematic scenes
        # ------------------------------------------------------
        print("✔ Generating narrative script using LLM...")
        llm_output = await run_in_threadpool(
            generate_cinematic_script,
            manga_name,
            manga_genre,
            extracted_text,
            image_bytes,
        )

        scenes = llm_output.get("scenes", [])
        if not scenes:
            raise HTTPException(500, "LLM returned no scenes")

        # ensure required keys exist
        for i, sc in enumerate(scenes):
            sc.setdefault("image_page_index", i)
            sc.setdefault("narration_segment", "")

        # ------------------------------------------------------
        # STEP 5 — Upload extracted images to Supabase
        # ------------------------------------------------------
        print("✔ Uploading images to Supabase Storage...")
        upload_jobs = []

        for idx, img in enumerate(image_bytes):
            clean_path = f"{manga_folder}/images/page_{idx:02d}.jpg"
            upload_jobs.append(run_in_threadpool(supabase_upload, img, clean_path, "image/jpeg"))

        image_urls = await asyncio.gather(*upload_jobs)
        print(f"✔ Uploaded {len(image_urls)} images")

        # ------------------------------------------------------
        # STEP 6 — Generate narration for each scene
        # ------------------------------------------------------
        print("✔ Generating narration audio for scenes...")

        timeline = 0.0
        merged_audio = AudioSegment.empty()
        final_scenes = []

        for sc in scenes:
            narration = sc["narration_segment"].strip()
            if not narration:
                continue

            audio_path, duration = await run_in_threadpool(generate_narration_audio, narration)

            try:
                clip = AudioSegment.from_mp3(audio_path)
            except:
                print("⚠ Audio damaged — adding silent fallback.")
                clip = AudioSegment.silent(duration=duration * 1000)

            merged_audio += clip

            sc["start_time"] = round(timeline, 2)
            sc["duration"] = round(duration, 2)
            timeline += duration

            final_scenes.append(sc)

        if not final_scenes:
            raise HTTPException(500, "No scenes with audio generated")

        # ------------------------------------------------------
        # STEP 7 — Save merged audio → upload
        # ------------------------------------------------------
        print("✔ Exporting merged audio...")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            merged_audio.export(tmp.name, format="mp3")
            merged_audio_tmp = tmp.name

        audio_storage_path = f"{manga_folder}/audio/master_audio.mp3"

        with open(merged_audio_tmp, "rb") as f:
            audio_bytes = f.read()

        audio_url = await run_in_threadpool(
            supabase_upload,
            audio_bytes,
            audio_storage_path,
            "audio/mpeg"
        )

        print(f"✔ Uploaded master audio to {audio_storage_path}")

        # ------------------------------------------------------
        # RESPONSE
        # ------------------------------------------------------
        return JSONResponse({
            "manga_name": manga_name,
            "image_urls": image_urls,
            "audio_url": audio_url,
            "final_video_segments": final_scenes
        })

    except HTTPException:
        raise

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, f"Audio story failed: {str(e)}")

    finally:
        if temp_pdf_path and os.path.exists(temp_pdf_path):
            try: os.remove(temp_pdf_path)
            except: pass

        if merged_audio_tmp and os.path.exists(merged_audio_tmp):
            try: os.remove(merged_audio_tmp)
            except: pass
