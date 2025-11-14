# backend/app/utils/image_utils.py

from PIL import Image
from moviepy.editor import ImageClip, CompositeVideoClip, ColorClip
import moviepy.video.fx.all as vfx
import shutil
import os
from typing import Dict, List

TARGET_W, TARGET_H = 1080, 1920


def _assert_ffmpeg_exists():
    """Ensures ffmpeg exists; MoviePy will otherwise crash silently."""
    if not shutil.which("ffmpeg"):
        raise EnvironmentError(
            "❌ ffmpeg is not installed or not in PATH. Install it to enable video rendering."
        )


def generate_cinematic_clip(
    image_path: str,
    coords_1000: List[int],
    clip_duration: float,
    animation_type: str = "static_zoom",
) -> CompositeVideoClip:
    """
    Generates a cinematic clip with safe zoom/pan animations.
    Used by generate_video.py
    """

    _assert_ffmpeg_exists()

    if not os.path.exists(image_path):
        raise FileNotFoundError(f"❌ Image not found: {image_path}")

    if clip_duration <= 0:
        clip_duration = 0.1

    if not coords_1000 or len(coords_1000) != 4:
        coords_1000 = [0, 0, 1000, 1000]  # fallback

    # Load image
    base_clip = ImageClip(image_path, duration=clip_duration)
    w_orig, h_orig = base_clip.size

    # Convert normalized coords → pixel coords
    x1 = int((coords_1000[0] / 1000) * w_orig)
    y1 = int((coords_1000[1] / 1000) * h_orig)
    x2 = int((coords_1000[2] / 1000) * w_orig)
    y2 = int((coords_1000[3] / 1000) * h_orig)

    if x1 >= x2 or y1 >= y2:
        x1, y1, x2, y2 = 0, 0, w_orig, h_orig

    try:
        panel_clip = base_clip.fx(
            vfx.crop,
            x1=x1,
            y1=y1,
            x2=x2,
            y2=y2,
        )
    except Exception:
        panel_clip = base_clip

    panel_w, panel_h = panel_clip.size
    if panel_w < 10 or panel_h < 10:
        panel_clip = base_clip

    # Animation types
    if animation_type == "pan_down":
        if panel_h > TARGET_H:
            pan_distance = panel_h - TARGET_H
            panel_clip = panel_clip.set_position(
                lambda t: ("center", -1 * (t / clip_duration) * pan_distance)
            )
        else:
            panel_clip = panel_clip.set_position("center")

    elif animation_type == "focus_character":
        zoom_func = lambda t: 1.15 - 0.15 * (t / clip_duration)
        panel_clip = panel_clip.fx(vfx.resize, zoom_func).set_position("center")

    else:  # static zoom
        zoom_func = lambda t: 1.05 - 0.05 * (t / clip_duration)
        panel_clip = panel_clip.fx(vfx.resize, zoom_func).set_position("center")

    background = ColorClip(
        size=(TARGET_W, TARGET_H),
        color=(0, 0, 0),
        duration=clip_duration,
    )

    final_clip = CompositeVideoClip([background, panel_clip])

    try:
        base_clip.close()
    except:
        pass

    return final_clip


def validate_scene_data(scene: Dict, scene_index: int) -> bool:
    required_fields = ["image_page_index", "crop_coordinates", "duration", "animation_type"]

    for field in required_fields:
        if field not in scene:
            return False

    coords = scene["crop_coordinates"]
    if len(coords) != 4:
        return False

    return True
