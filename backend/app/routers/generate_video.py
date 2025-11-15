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

# MoviePy imports (fixed order)
from moviepy.editor import (
    AudioFileClip,
    CompositeVideoClip,
    ImageClip,
    concatenate_videoclips,
    ColorClip
)

# Supabase uploader
from app.utils.supabase_utils import supabase_upload

# Cinematic clip generator
from app.utils.image_utils import generate_cinematic_clip

router = APIRouter()

VIDEO_FPS = 30
VIDEO_RESOLUTION = (1080, 1920)

STATUS_DIR = os.path.join(os.getcwd(), "job_status")
os.makedirs(STATUS_DIR, exist_ok=True)

# ---------------------------------------------------------------
# VIDEO COMPRESSION (H.264 + CRF)
# ---------------------------------------------------------------
def compress_video(input_path: str, output_path: str, crf: int = 28) -> str:
    """
    Compress video using ffmpeg (lower file size for Supabase limit).
    crf 23 = good quality
    crf 28 = low size
    crf 30+ = very small file
    """
    try:
        import subprocess

        cmd = [
            "ffmpeg",
            "-y",
            "-i", input_path,
            "-vcodec", "libx264",
            "-crf", str(crf),
            "-preset", "fast",
            "-acodec", "aac",
            output_path,
        ]

        print("🔧 Compressing video:", " ".join(cmd))
        subprocess.run(cmd, check=True)

        print("✔ Compression finished:", output_path)
        return output_path

    except Exception as e:
        print("❌ Compression failed, using original:", e)
        return input_path

def write_status(job_id: str, data: dict):
    """Write job status JSON. Use default=str to avoid serialization errors."""
    try:
        path = os.path.join(STATUS_DIR, f"{job_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    except Exception as e:
        print(f"[STATUS WRITE ERROR] job={job_id} error={e}")


class VideoGenerationRequest(BaseModel):
    manga_name: str
    audio_url: str
    image_urls: List[str]
    final_video_segments: List[Dict[str, Any]]


# --------------------------
# Download file (sync)
# --------------------------
def download_file_sync(url: str, local_path: str, retries: int = 2):
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


# --------------------------
# Upload via Supabase
# --------------------------
def upload_local_file_to_supabase(local_path: str, dest_path: str, ct: str):
    with open(local_path, "rb") as f:
        data = f.read()
    return supabase_upload(data, dest_path, ct)


# ================================================================
# FIXED FULL VIDEO RENDER
# ================================================================
def render_video_sync(manga_name, audio_url, image_urls, segments, temp_dir):

    clips_to_close = []

    try:
        print("--- [RENDER] Downloading audio & images ---")

        audio_path = os.path.join(temp_dir, "narration.mp3")
        download_file_sync(audio_url, audio_path)

        local_images = {}
        for i, url in enumerate(image_urls):
            img_path = os.path.join(temp_dir, f"page_{i}.jpg")
            download_file_sync(url, img_path)
            local_images[i] = img_path

        # Do NOT use "with AudioFileClip" to avoid closing audio reader too early
        audio_clip = AudioFileClip(audio_path)
        if not getattr(audio_clip, "fps", None):
            audio_clip = audio_clip.set_fps(44100)
        clips_to_close.append(audio_clip)

        print("--- [RENDER] Generating cinematic clips ---")
        video_clips = []

        for idx, seg in enumerate(segments):
            try:
                img_index = seg.get("image_page_index")
                dur = float(seg.get("duration", 2.0))
                start = float(seg.get("start_time", 0.0))
                coords = seg.get("crop_coordinates", [0, 0, 1000, 1000])
                anim = seg.get("animation_type", "static_zoom")

                if img_index not in local_images:
                    print(f"[WARN] segment {idx} missing image")
                    continue

                clip = generate_cinematic_clip(
                    image_path=local_images[img_index],
                    coords_1000=coords,
                    clip_duration=dur,
                    animation_type=anim
                )

                clip = clip.set_start(start)
                video_clips.append(clip)
                clips_to_close.append(clip)

            except Exception as e:
                print(f"[ERROR] segment {idx}: {e}")

        if not video_clips:
            raise RuntimeError("No video clips were generated.")

        print("--- [RENDER] Compositing final ---")
        final_video = CompositeVideoClip(video_clips, size=VIDEO_RESOLUTION)
        final_video = final_video.set_audio(audio_clip)
        final_video.duration = audio_clip.duration
        clips_to_close.append(final_video)

        out_name = f"{manga_name.replace(' ', '_')}.mp4"
        out_path = os.path.join(temp_dir, out_name)
        
        compressed_path = out_path.replace(".mp4", "_compressed.mp4")


        print("--- [RENDER] Writing MP4 ---")
        final_video.write_videofile(
            compressed_path,
            fps=VIDEO_FPS,
            codec="libx264",
            audio_codec="aac",
            bitrate="3000k",   # LOWER BITRATE = SMALLER VIDEO
            threads=2,
            preset="ultrafast",
        )

        return compressed_path

    finally:
        for c in clips_to_close:
            try:
                c.close()
            except Exception:
                pass


# ================================================================
# PREVIEW GENERATOR (robust)
# ================================================================
def render_preview_sync(manga_name, audio_url, image_urls, duration, temp_dir):

    preview_out_dir = os.path.join(temp_dir, "preview")
    os.makedirs(preview_out_dir, exist_ok=True)

    preview_path = os.path.join(
        preview_out_dir,
        f"{manga_name.replace(' ', '_')}_preview_{int(time.time())}.mp4"
    )

    print("--- [PREVIEW] Loading images ---")
    usable = []

    for i, url in enumerate(image_urls[:5]):
        try:
            img_p = os.path.join(temp_dir, f"prev_{i}.jpg")
            download_file_sync(url, img_p)
            usable.append(img_p)
        except Exception as e:
            print(f"[PREVIEW] img {i} failed: {e}")

    # ---- Build slideshow ----
    if usable:
        per = max(0.5, float(duration) / len(usable))
        clips = [ImageClip(u).set_duration(per).resize(width=480) for u in usable]
        slideshow = concatenate_videoclips(clips, method="compose")
    else:
        slideshow = ColorClip(size=(480, 270), color=(15, 15, 15)).set_duration(duration)

    # ---- Attach audio safely (no 'with' usage) ----
    audio_local = os.path.join(temp_dir, "preview_audio.mp3")

    snippet = None
    audio_clip = None
    try:
        download_file_sync(audio_url, audio_local)
        audio_clip = AudioFileClip(audio_local)
        if not getattr(audio_clip, "fps", None):
            audio_clip = audio_clip.set_fps(44100)

        snippet = audio_clip.subclip(0, min(duration, audio_clip.duration))
        slideshow = slideshow.set_audio(snippet)

    except Exception as e:
        print(f"[PREVIEW] No audio: {e}")

    # ---- Write video ----
    slideshow.write_videofile(
        preview_path,
        fps=12,
        codec="libx264",
        audio_codec="aac",
        bitrate="500k",
        preset="ultrafast",
        threads=1,
        verbose=False,
        logger=None,
    )

    # Cleanup
    try:
        slideshow.close()
        if snippet:
            snippet.close()
        if audio_clip:
            audio_clip.close()
    except Exception:
        pass

    return preview_path


# ================================================================
# Background: final render + upload
# ================================================================
def _render_and_upload_full_job(manga_name, audio_url, image_urls, segments, temp_dir, job_id):

    try:
        print(f"--- [JOB {job_id}] Starting full render ---")

        final_path = render_video_sync(manga_name, audio_url, image_urls, segments, temp_dir)

        # NEW — Compress before uploading
        compressed_path = os.path.join(temp_dir, "compressed_final.mp4")
        final_path = compress_video(final_path, compressed_path, crf=28)


        dest = f"videos/{job_id}/{os.path.basename(final_path)}"


        # NOTE: this function is synchronous; call it directly in background task.
        try:
            uploaded_url = upload_local_file_to_supabase(final_path, dest, "video/mp4")
            print(f"[JOB {job_id}] Final video uploaded: {uploaded_url}")

            write_status(job_id, {
                "status": "completed",
                "preview_url": None,
                "video_url": uploaded_url,
                "message": "Final video ready."
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
        print(f"[JOB {job_id}] ERROR during final render: {exc}")
        traceback.print_exc()

        write_status(job_id, {
            "status": "error",
            "message": str(exc),
            "preview_url": None,
            "video_url": None
        })

    finally:
        try:
            shutil.rmtree(temp_dir)
            print(f"[CLEANUP] Removed temp dir: {temp_dir}")
        except Exception as e:
            print(f"[CLEANUP ERROR] {e}")


# ================================================================
# API Endpoints
# ================================================================
@router.get("/video_status/{job_id}")
def get_video_status(job_id: str):
    path = os.path.join(STATUS_DIR, f"{job_id}.json")

    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Job not found")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@router.post("/generate_video")
async def generate_video_endpoint(
    request: VideoGenerationRequest,
    background_tasks: BackgroundTasks,
):

    job_id = str(uuid.uuid4())
    temp_dir = os.path.join(tempfile.gettempdir(), f"job_{job_id}")
    os.makedirs(temp_dir, exist_ok=True)

    try:
        print(f"--- [JOB {job_id}] Creating preview ---")

        preview_path = await run_in_threadpool(
            render_preview_sync,
            request.manga_name,
            request.audio_url,
            request.image_urls,
            5,
            temp_dir,
        )

        preview_dest = f"previews/{job_id}/{os.path.basename(preview_path)}"
        preview_url = await run_in_threadpool(
            upload_local_file_to_supabase,
            preview_path,
            preview_dest,
            "video/mp4",
        )

        write_status(job_id, {
            "status": "processing",
            "preview_url": preview_url,
            "video_url": None,
            "message": "Preview ready; final rendering..."
        })

        # schedule background final render (runs synchronously in background context)
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
            "message": "Preview generated, full video rendering..."
        }

    except Exception as exc:
        traceback.print_exc()

        write_status(job_id, {
            "status": "error",
            "preview_url": None,
            "video_url": None,
            "message": f"Preview failed: {exc}"
        })

        raise HTTPException(status_code=500, detail=f"Failed to start rendering: {exc}")
