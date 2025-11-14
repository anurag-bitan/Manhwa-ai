# backend/app/routers/generate_audio_story.py
import asyncio
import io
import os
import tempfile
import traceback
from typing import List

from fastapi import APIRouter, Form, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from pydub import AudioSegment

# --- Storage uploader (Supabase or other storage adapter) ---
from ..utils.supabase_utils import supabase_upload

# --- PDF extraction (high quality) ---
from ..utils.pdf_utils import extract_pdf_images_high_quality

# --- OCR ---
from ..utils.vision_utils import ocr_image_bytes

# --- TTS ---
from ..utils.tts_utils import generate_narration_audio

# --- LLM ---
from ..utils.openai_utils import generate_cinematic_script
from fastapi import File
router = APIRouter()


# ------------------------------------------------------
# Convert extracted PIL images → JPEG bytes
# ------------------------------------------------------
def pil_images_to_bytes(images: List) -> List[bytes]:
    output = []
    for img in images:
        buf = io.BytesIO()
        img.save(buf, format="JPEG", optimize=True, quality=90)
        output.append(buf.getvalue())
    return output


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
    master_audio_tmp_path = None
    manga_folder = manga_name.replace(" ", "_").lower()

    try:
        # ------------------------------------------------------
        # STEP 1: Save uploaded PDF temporarily
        # ------------------------------------------------------
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(await manga_pdf.read())
            temp_pdf_path = tmp.name

        print("✔ PDF saved, starting high-quality image extraction")

        # ------------------------------------------------------
        # STEP 2: Extract HQ images
        # ------------------------------------------------------
        images = await run_in_threadpool(extract_pdf_images_high_quality, temp_pdf_path)
        if not images:
            raise HTTPException(status_code=400, detail="No images extracted from PDF. Check PDF file.")

        image_bytes = pil_images_to_bytes(images)
        print(f"✔ Extracted {len(image_bytes)} images from PDF")

        # ------------------------------------------------------
        # STEP 3: OCR all pages
        # ------------------------------------------------------
        print("✔ Running OCR on all pages...")
        ocr_tasks = [run_in_threadpool(ocr_image_bytes, img) for img in image_bytes]
        ocr_text_results = await asyncio.gather(*ocr_tasks)
        extracted_text = "\n\n--- PAGE BREAK ---\n\n".join([t for t in ocr_text_results if t])
        print("✔ OCR completed")

        # ------------------------------------------------------
        # STEP 4: LLM Script generation (images + OCR)
        # ------------------------------------------------------
        print("✔ Generating narrative script using LLM...")
        llm_output = await run_in_threadpool(
            generate_cinematic_script,
            manga_name,
            manga_genre,
            extracted_text,
            image_bytes
        )

        scenes = llm_output.get("scenes", [])
        if not scenes:
            raise HTTPException(status_code=500, detail="LLM failed, no scenes returned")

        # Ensure every scene has an image_page_index and narration_segment
        for i, s in enumerate(scenes):
            if "image_page_index" not in s:
                s["image_page_index"] = 0
            if "narration_segment" not in s:
                s["narration_segment"] = ""

        # ------------------------------------------------------
        # STEP 5: Upload images to Supabase (or configured storage)
        # ------------------------------------------------------
        print("✔ Uploading images to Supabase Storage...")
        supabase_img_tasks = []
        for idx, img in enumerate(image_bytes):
            file_path = f"{manga_folder}/images/page_{idx:02d}.jpg"
            # supabase_upload expects bytes, path, content_type
            supabase_img_tasks.append(
                run_in_threadpool(supabase_upload, img, file_path, "image/jpeg")
            )

        image_urls = await asyncio.gather(*supabase_img_tasks)
        print(f"✔ Uploaded {len(image_urls)} images")

        # ------------------------------------------------------
        # STEP 6: TTS for each scene, collect timings
        # ------------------------------------------------------
        print("✔ Generating narration audio for scenes...")
        current_time = 0.0
        merged_audio = AudioSegment.empty()
        final_scenes = []

        for scene in scenes:
            narration = scene.get("narration_segment", "").strip()
            if not narration:
                # skip empty narration segments but keep minimal metadata
                continue

            # generate_narration_audio returns (path, duration)
            audio_path, duration = await run_in_threadpool(generate_narration_audio, narration)

            # load and append
            try:
                clip = AudioSegment.from_mp3(audio_path)
                merged_audio += clip
            except Exception as e:
                print(f"⚠ Failed to load generated audio {audio_path}: {e}")
                # create 1s silent placeholder to avoid breaking timeline
                merged_audio += AudioSegment.silent(duration=1000)
                duration = max(duration, 1.0)

            scene["start_time"] = round(current_time, 2)
            scene["duration"] = round(duration, 2)
            current_time += duration
            final_scenes.append(scene)

        if not final_scenes:
            raise HTTPException(status_code=500, detail="No valid scenes with audio generated.")

        # ------------------------------------------------------
        # STEP 7: Export merged audio and upload to Supabase
        # ------------------------------------------------------
        print("✔ Exporting merged audio...")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_audio:
            merged_audio.export(tmp_audio.name, format="mp3")
            master_audio_tmp_path = tmp_audio.name

        audio_file_path = f"{manga_folder}/audio/master_audio.mp3"
        with open(master_audio_tmp_path, "rb") as f:
            audio_bytes = f.read()

        audio_url = await run_in_threadpool(supabase_upload, audio_bytes, audio_file_path, "audio/mpeg")
        print(f"✔ Uploaded master audio to {audio_file_path}")

        # ------------------------------------------------------
        # FINAL RESPONSE
        # ------------------------------------------------------
        return JSONResponse({
            "manga_name": manga_name,
            "image_urls": image_urls,
            "audio_url": audio_url,
            "final_video_segments": final_scenes
        })

    except HTTPException:
        # re-raise FastAPI HTTP exceptions as-is
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Audio story failed: {str(e)}")
    finally:
        # cleanup temporary files
        try:
            if temp_pdf_path and os.path.exists(temp_pdf_path):
                os.remove(temp_pdf_path)
        except Exception:
            pass

        try:
            if master_audio_tmp_path and os.path.exists(master_audio_tmp_path):
                os.remove(master_audio_tmp_path)
        except Exception:
            pass
