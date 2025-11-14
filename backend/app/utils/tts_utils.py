"""
Ultra-Stable Text-to-Speech Generator for Manga Narration
---------------------------------------------------------
Optimized for:
 - Windows + ffmpeg
 - Hinglish/Hindi narration
 - Accurate scene timings
 - Long dialogues (auto-chunked)
 - Error-free caching
"""

import os
import time
import hashlib
import shutil
from typing import List

from gtts import gTTS
from pydub import AudioSegment

from app.config import TTS_CACHE_DIR



# ============================================================
# 1. FFmpeg Safety Check (Windows Compatible)
# ============================================================
def _assert_ffmpeg_exists():
    if not shutil.which("ffmpeg"):
        raise EnvironmentError(
            "❌ FFmpeg not found!\n"
            "Install FFmpeg (Windows build): https://www.gyan.dev/ffmpeg/builds/\n"
            "Then add to PATH."
        )


# ============================================================
# 2. Normalize Text → Better Cache Keys
# ============================================================
def _normalize(text: str) -> str:
    text = text.replace("\n", " ").strip()
    return " ".join(text.split())


# ============================================================
# 3. Get Audio Duration Safely
# ============================================================
def _duration(path: str) -> float:
    try:
        audio = AudioSegment.from_mp3(path)
        return round(len(audio) / 1000, 2)
    except:
        return 0.0


# ============================================================
# 4. Split Long Text Automatically
#    gTTS fails silently beyond ~200 chars
# ============================================================
def _chunk_text(text: str, limit: int = 180) -> List[str]:
    words = text.split()
    chunks = []
    current = []

    for w in words:
        current.append(w)
        if len(" ".join(current)) > limit:
            chunks.append(" ".join(current))
            current = []

    if current:
        chunks.append(" ".join(current))

    return chunks


# ============================================================
# 5. Save gTTS Audio with Retries
# ============================================================
def _safe_tts_to_file(text: str, path: str) -> float:
    retries = 3

    for i in range(1, retries + 1):
        try:
            tts = gTTS(text=text, lang="hi", slow=False)
            tts.save(path)
            duration = _duration(path)
            if duration > 0.2:
                return duration
            print(f"⚠ Empty or corrupted audio on attempt {i}")
        except Exception as e:
            print(f"⚠ TTS error on attempt {i}: {e}")

        time.sleep(1)

    return 0.0


# ============================================================
# 6. MAIN FUNCTION — Stable, Chunked, Cached TTS
# ============================================================
def generate_narration_audio(text: str) -> tuple[str, float]:
    """
    Generates narration from Hinglish text:
       ✔ Auto-chunks long text
       ✔ ffmpeg-safe
       ✔ Fully cached (scene-level)
       ✔ Accurate duration (pydub)
    """

    _assert_ffmpeg_exists()

    os.makedirs(TTS_CACHE_DIR, exist_ok=True)

    # Clean the text
    clean_text = _normalize(text)

    # Cache key
    text_hash = hashlib.md5(clean_text.encode()).hexdigest()
    final_path = os.path.join(TTS_CACHE_DIR, f"{text_hash}.mp3")

    # ------------------------------------------------------------
    # STEP 1 — Return valid cached audio
    # ------------------------------------------------------------
    if os.path.exists(final_path):
        dur = _duration(final_path)
        if dur > 0.2:
            print(f"✔ Cached narration ({dur}s)")
            return final_path, dur
        else:
            print("⚠ Cached file corrupted → regenerating...")
            try:
                os.remove(final_path)
            except:
                pass

    # ------------------------------------------------------------
    # STEP 2 — Generate new narration
    # ------------------------------------------------------------
    print(f"🎤 Generating TTS: '{clean_text[:50]}...'")

    chunks = _chunk_text(clean_text)
    chunk_paths = []
    total_duration = 0.0

    # Generate each chunk
    for idx, chunk in enumerate(chunks):
        chunk_file = os.path.join(TTS_CACHE_DIR, f"{text_hash}_part{idx}.mp3")

        dur = _safe_tts_to_file(chunk, chunk_file)
        if dur == 0.0:
            print(f"❌ Chunk {idx} failed — skipping...")
            continue

        chunk_paths.append(chunk_file)
        total_duration += dur

    if not chunk_paths:
        print("❌ gTTS failed completely — creating fallback silence.")
        fallback = os.path.join(TTS_CACHE_DIR, f"{text_hash}_fallback.mp3")
        AudioSegment.silent(duration=800).export(fallback, format="mp3")
        return fallback, 0.8

    # ------------------------------------------------------------
    # STEP 3 — Merge all chunks → final MP3 file
    # ------------------------------------------------------------
    final_audio = AudioSegment.empty()

    for cp in chunk_paths:
        part_audio = AudioSegment.from_mp3(cp)
        final_audio += part_audio

    final_audio.export(final_path, format="mp3")

    # Cleanup temporary parts
    for cp in chunk_paths:
        try:
            os.remove(cp)
        except:
            pass

    print(f"✔ Final TTS generated → {total_duration}s")

    return final_path, round(total_duration, 2)
