# backend/app/routers/generate_video.py
import os
import shutil
import tempfile
import traceback
import uuid
import time
from typing import Any, Dict, List
import json
import requests

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

# MoviePy imports
from moviepy.editor import AudioFileClip, CompositeVideoClip, ImageClip, concatenate_videoclips

# Use your Supabase uploader helper (must be implemented in utils.supabase_utils)
from app.utils.supabase_utils import supabase_upload

# Cinematic clip generator (your file provided earlier)
from app.utils.image_utils import generate_cinematic_clip

router = APIRouter()
VIDEO_FPS = 30
VIDEO_RESOLUTION = (1080, 1920)

# Local job-status directory (same pattern used elsewhere)
STATUS_DIR = os.path.join(os.getcwd(), "job_status")
os.makedirs(STATUS_DIR, exist_ok=True)


def write_status(job_id: str, data: dict):
    """Write a small JSON file that frontend polls for job status."""
    try:
        path = os.path.join(STATUS_DIR, f"{job_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception as e:
        print(f"[STATUS WRITE ERROR] job={job_id} error={e}")


class VideoGenerationRequest(BaseModel):
    manga_name: str
    audio_url: str
    image_urls: List[str]
    final_video_segments: List[Dict[str, Any]]


# -------------------------
# Helper: download file sync
# -------------------------
def download_file_sync(url: str, local_path: str, retries: int = 2):
    """
    Download a file (images/audio) to local_path. Raises ValueError on failure.
    Keep simple and robust: retries, timeouts.
    """
    headers = {"User-Agent": "Manhwa-AI/1.0"}
    for attempt in range(retries + 1):
        try:
            with requests.get(url, stream=True, timeout=30, headers=headers) as r:
                r.raise_for_status()
                with open(local_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            return
        except Exception as e:
            last_err = e
            print(f"[DOWNLOAD] Attempt {attempt+1}/{retries+1} failed for {url}: {e}")
            time.sleep(0.5)
    raise ValueError(f"Failed to download {url}: {last_err}")


# -------------------------
# Utility: upload local file via supabase_upload helper
# -------------------------
def upload_local_file_to_supabase(local_path: str, dest_path: str, content_type: str):
    """
    Reads local file as bytes and calls supabase_upload.
    This function is synchronous; we call it inside run_in_threadpool when needed.
    """
    with open(local_path, "rb") as f:
        data = f.read()
    # supabase_upload may be sync or async in your implementation.
    # If it's async, the caller uses run_in_threadpool, so ensure the function runs fine.
    return supabase_upload(data, dest_path, content_type)


# -------------------------
# Full-resolution final render
# -------------------------
def render_video_sync(manga_name: str, audio_url: str, image_urls: List[str], segments: List[Dict[str, Any]], temp_dir: str) -> str:
    """
    Downloads audio & images, builds cinematic clips using your image_utils,
    composites them and writes final MP4 into temp_dir.
    Returns the local path of the final rendered video.
    """
    clips_to_close = []
    try:
        print("--- [RENDER] Downloading audio & images ---")
        audio_path = os.path.join(temp_dir, "narration.mp3")
        download_file_sync(audio_url, audio_path)

        # download images (all pages referenced)
        local_image_paths = {}
        for i, u in enumerate(image_urls):
            img_path = os.path.join(temp_dir, f"page_{i}.jpg")
            download_file_sync(u, img_path)
            local_image_paths[i] = img_path

        audio_clip = AudioFileClip(audio_path)
        clips_to_close.append(audio_clip)

        print("--- [RENDER] Generating cinematic clips ---")
        video_clips = []
        for seg_index, seg in enumerate(segments):
            img_index = seg.get("image_page_index")
            duration = seg.get("duration", 2.0)
            start_time = seg.get("start_time", 0.0)
            crop_coordinates = seg.get("crop_coordinates", [0, 0, 1000, 1000])
            animation_type = seg.get("animation_type", "static_zoom")

            if img_index not in local_image_paths:
                print(f"   - [WARN] segment {seg_index} references missing image index {img_index} - skipping")
                continue

            image_path = local_image_paths[img_index]

            # create cinematic clip using your utility (it returns a CompositeVideoClip)
            try:
                clip = generate_cinematic_clip(
                    image_path=image_path,
                    coords_1000=crop_coordinates,
                    clip_duration=duration,
                    animation_type=animation_type
                )
                clip = clip.set_start(start_time)
                video_clips.append(clip)
                clips_to_close.append(clip)
            except Exception as e:
                print(f"   - [ERROR] Failed to generate clip for segment {seg_index}: {e}")
                continue

        if not video_clips:
            raise ValueError("No valid video clips were generated.")

        print("--- [RENDER] Compositing final video ---")
        final_video = CompositeVideoClip(video_clips, size=VIDEO_RESOLUTION)
        final_video.set_audio(audio_clip)
        final_video.duration = audio_clip.duration
        clips_to_close.append(final_video)

        output_name = f"{manga_name.replace(' ', '_')}.mp4"
        output_path = os.path.join(temp_dir, output_name)

        print("--- [RENDER] Writing video file (this may take a while) ---")
        final_video.write_videofile(
            output_path,
            fps=VIDEO_FPS,
            codec="libx264",
            audio_codec="aac",
            bitrate="8000k",
            preset="medium",
            threads=os.cpu_count() or 2,
        )

        return output_path

    finally:
        # close clips gracefully
        for c in clips_to_close:
            try:
                c.close()
            except Exception:
                pass


# -------------------------
# Fast preview render (small, low-bitrate)
# -------------------------
def render_preview_sync(manga_name: str, audio_url: str, image_urls: List[str], duration: int, temp_dir: str) -> str:
    preview_dir = os.path.join(temp_dir, "previews")
    os.makedirs(preview_dir, exist_ok=True)
    preview_path = os.path.join(preview_dir, f"{manga_name.replace(' ', '_')}_preview_{int(time.time())}.mp4")

    print("--- [PREVIEW] Preparing images ---")
    usable_images = []
    for i, u in enumerate(image_urls[:5]):
        try:
            img_path = os.path.join(temp_dir, f"preview_page_{i}.jpg")
            download_file_sync(u, img_path)
            usable_images.append(img_path)
        except Exception as e:
            print(f"   - [PREVIEW] Failed to download image {i}: {e}")

    clips = []
    if usable_images:
        per_image_dur = max(0.5, float(duration) / len(usable_images))
        for img in usable_images:
            clips.append(ImageClip(img).set_duration(per_image_dur).resize(width=480))
        slideshow = concatenate_videoclips(clips, method="compose")
    else:
        from moviepy.video.VideoClip import ColorClip, TextClip
        color = ColorClip(size=(480, 270), color=(20, 20, 20)).set_duration(duration)
        try:
            txt = TextClip("Preview not available", fontsize=24, color="white").set_position("center").set_duration(duration)
            slideshow = CompositeVideoClip([color, txt])
        except Exception:
            slideshow = color

    # attach audio snippet if available
    audio_local = os.path.join(temp_dir, "preview_narration.mp3")
    try:
        download_file_sync(audio_url, audio_local)
        audio_clip = AudioFileClip(audio_local)
        snippet = audio_clip.subclip(0, min(duration, audio_clip.duration))
        slideshow = slideshow.set_audio(snippet)
        audio_clip.close()
    except Exception as e:
        print(f"   - [PREVIEW] No audio: {e}")

    # write low-res preview
    slideshow.write_videofile(
        preview_path,
        fps=12,
        codec="libx264",
        audio_codec="aac",
        bitrate="400k",
        preset="ultrafast",
        threads=1,
        verbose=False,
        logger=None
    )

    return preview_path


# -------------------------
# Background full render + upload
# -------------------------
def _render_and_upload_full_job(manga_name: str, audio_url: str, image_urls: List[str], segments: List[Dict[str, Any]], temp_dir: str, job_id: str):
    try:
        print(f"--- [JOB {job_id}] Background final render starting... ---")
        final_video_path = render_video_sync(manga_name, audio_url, image_urls, segments, temp_dir)

        print(f"--- [JOB {job_id}] Uploading final video to Supabase... ---")
        firebase_path = f"videos/{os.path.basename(final_video_path)}"

        try:
            # read file & upload via supabase_upload (runs in threadpool)
            uploaded_url = run_in_threadpool(upload_local_file_to_supabase, final_video_path, firebase_path, "video/mp4")
            print(f"--- [JOB {job_id}] Final video uploaded: {uploaded_url} ---")

            write_status(job_id, {
                "status": "completed",
                "preview_url": None,
                "video_url": uploaded_url,
                "message": "Final video ready"
            })

        except Exception as e:
            print(f"--- [JOB {job_id}] ERROR uploading final video: {e} ---")
            write_status(job_id, {
                "status": "error",
                "preview_url": None,
                "video_url": None,
                "message": f"Upload failed: {e}"
            })

    except Exception as exc:
        print("\n" + "=" * 70)
        print(f"   [FATAL ERROR] in background video generation pipeline: {exc}")
        print("=" * 70)
        traceback.print_exc()
        write_status(job_id, {
            "status": "error",
            "preview_url": None,
            "video_url": None,
            "message": str(exc)
        })
    finally:
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                print(f"--- [CLEANUP] Removed temporary directory (background job): {temp_dir} ---")
        except Exception as e:
            print(f"--- [CLEANUP ERROR] while removing {temp_dir}: {e}")


# -------------------------
# API Endpoint
# -------------------------
@router.post("/generate_video")
async def generate_video_endpoint(request: VideoGenerationRequest, background_tasks: BackgroundTasks):
    """
    1) Create quick preview synchronously
    2) Upload preview to Supabase
    3) Write 'processing' status and schedule background final render
    """
    job_id = str(uuid.uuid4())
    temp_dir = os.path.join(tempfile.gettempdir(), f"job_{job_id}")
    os.makedirs(temp_dir, exist_ok=True)

    try:
        print(f"--- [JOB {job_id}] Creating preview (fast clip)... ---")
        preview_path = await run_in_threadpool(
            render_preview_sync,
            request.manga_name,
            request.audio_url,
            request.image_urls,
            5,  # seconds
            temp_dir,
        )

        preview_dest = f"previews/{job_id}/{os.path.basename(preview_path)}"
        preview_url = await run_in_threadpool(upload_local_file_to_supabase, preview_path, preview_dest, "video/mp4")

        print(f"--- [JOB {job_id}] Uploaded preview to Supabase: {preview_url} ---")

        write_status(job_id, {
            "status": "processing",
            "preview_url": preview_url,
            "video_url": None,
            "message": "Preview ready, final render in background"
        })

        # schedule background final render
        background_tasks.add_task(
            _render_and_upload_full_job,
            request.manga_name,
            request.audio_url,
            request.image_urls,
            request.final_video_segments,
            temp_dir,
            job_id,
        )

        return {
            "status": "processing",
            "preview_url": preview_url,
            "job_id": job_id,
            "message": "Preview available; final video is rendering in background.",
        }

    except Exception as e:
        print("\n" + "=" * 70)
        print(f"   [FATAL ERROR] while creating preview for job {job_id}: {e}")
        print("=" * 70)
        traceback.print_exc()
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        except Exception:
            pass

        write_status(job_id, {
            "status": "error",
            "preview_url": None,
            "video_url": None,
            "message": f"Preview creation failed: {e}"
        }) 

        raise HTTPException(status_code=500, detail=f"Failed to start video generation: {str(e)}")
