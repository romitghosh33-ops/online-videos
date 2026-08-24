"""
Video assembly.

Combines, per scene:
  - a visual: an image/video you supply in an assets folder (named
    scene-01.png / scene-02.png / ... matching the script's scene numbers)
    takes priority; otherwise the procedural cartoon_renderer draws the
    Bounce character animated for that scene; if even that fails, falls
    back to a plain color card with the scene's "visual" description as
    on-screen text.
  - the scene's synthesized voiceover clip (from tts_pipeline), which sets
    that scene's on-screen duration
  - an optional looping background music track, mixed under the narration
    at reduced volume

...into a single MP4, matching the scene order in the script JSON.

This is a *rough-cut* assembler for previewing pacing and reviewing scripts
end-to-end, not a replacement for a real animation pipeline. Swap in real
animated clips per scene by pointing --assets-dir at rendered video files
named scene-01.mp4, scene-02.mp4, etc. (image and video assets can be
mixed).

Built against moviepy 2.x (`from moviepy import ...`, `with_*` / `resized` /
`subclipped` method names -- not the old 1.x `moviepy.editor` API).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from moviepy import (
    AudioFileClip,
    ColorClip,
    CompositeAudioClip,
    CompositeVideoClip,
    ImageClip,
    TextClip,
    VideoFileClip,
    concatenate_audioclips,
    concatenate_videoclips,
)

from src.cartoon_renderer import make_cartoon_clip
from src.config import config

VIDEO_SIZE = (1280, 720)
FALLBACK_COLORS = [
    (255, 214, 165),  # warm peach
    (198, 232, 173),  # soft green
    (167, 216, 245),  # sky blue
    (255, 236, 179),  # pale yellow
]


def _find_scene_asset(assets_dir: Optional[Path], scene_number: int):
    if not assets_dir:
        return None
    for ext in (".mp4", ".mov", ".png", ".jpg", ".jpeg"):
        candidate = assets_dir / f"scene-{scene_number:02d}{ext}"
        if candidate.exists():
            return candidate
    return None


def _build_scene_clip(scene: dict, duration: float, assets_dir: Optional[Path]):
    asset_path = _find_scene_asset(assets_dir, scene["scene_number"])

    if asset_path and asset_path.suffix in (".mp4", ".mov"):
        raw = VideoFileClip(str(asset_path))
        clip = raw.subclipped(0, min(duration, raw.duration))
        return clip.resized(VIDEO_SIZE).with_duration(duration)

    if asset_path and asset_path.suffix in (".png", ".jpg", ".jpeg"):
        return ImageClip(str(asset_path)).resized(VIDEO_SIZE).with_duration(duration)

    if not asset_path:
        try:
            return make_cartoon_clip(scene, duration, scene["scene_number"])
        except Exception as exc:  # pragma: no cover - defensive fallback
            print(f"cartoon_renderer failed for scene {scene['scene_number']} ({exc}); using caption card.")

    # Last-resort fallback: plain color card + the visual description as
    # text, so you can still review pacing/timing.
    color = FALLBACK_COLORS[scene["scene_number"] % len(FALLBACK_COLORS)]
    bg = ColorClip(size=VIDEO_SIZE, color=color).with_duration(duration)
    caption = (
        TextClip(
            text=scene["visual"],
            font_size=36,
            color="black",
            size=(VIDEO_SIZE[0] - 160, None),
            method="caption",
        )
        .with_duration(duration)
        .with_position("center")
    )
    return CompositeVideoClip([bg, caption])


def assemble_video(
    script_path: str,
    audio_dir: str,
    assets_dir: Optional[str] = None,
    music_path: Optional[str] = None,
    out_path: Optional[str] = None,
) -> Path:
    script = json.loads(Path(script_path).read_text())
    audio_dir_p = Path(audio_dir)
    assets_dir_p = Path(assets_dir) if assets_dir else None

    scene_clips = []
    for scene in script["scenes"]:
        scene_audio_path = audio_dir_p / f"scene-{scene['scene_number']:02d}.wav"
        if scene_audio_path.exists():
            audio_clip = AudioFileClip(str(scene_audio_path))
            duration = audio_clip.duration
        else:
            # Song/placeholder scenes with no synthesized VO: fall back to
            # the script's planned duration.
            audio_clip = None
            duration = scene.get("duration_seconds", 5)

        visual_clip = _build_scene_clip(scene, duration, assets_dir_p)
        if audio_clip is not None:
            visual_clip = visual_clip.with_audio(audio_clip)
        scene_clips.append(visual_clip)

    final = concatenate_videoclips(scene_clips, method="compose")

    if music_path:
        music = AudioFileClip(music_path).with_volume_scaled(0.15)
        loops_needed = int(final.duration // music.duration) + 1
        music = concatenate_audioclips([music] * max(loops_needed, 1)).subclipped(0, final.duration)
        final_audio = CompositeAudioClip([final.audio, music]) if final.audio else music
        final = final.with_audio(final_audio)

    out_dir = Path(config.OUTPUT_DIR) / "video"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path_p = Path(out_path) if out_path else out_dir / f"{_slug(script['title'])}.mp4"
    out_path_p.parent.mkdir(parents=True, exist_ok=True)

    final.write_videofile(str(out_path_p), fps=24, codec="libx264", audio_codec="aac")
    print(f"Assembled video: {out_path_p}")
    return out_path_p


def _slug(title: str) -> str:
    slug = title.lower().replace(" ", "-").replace("'", "")
    return "".join(c for c in slug if c.isalnum() or c == "-")
