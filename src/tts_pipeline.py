"""
Text-to-speech voiceover generation.

Reads a script JSON produced by script_generator, synthesizes one audio
clip per scene's voiceover line, and concatenates them into a single
narration track with a short pause between scenes.

Backends:
  - "elevenlabs": cloud TTS, higher quality, needs ELEVENLABS_API_KEY.
  - "offline": pyttsx3 (local, no network/API key, lower quality). Good
    default so the pipeline is runnable out of the box.

Requires ffmpeg on PATH for pydub to read/write mp3 (falls back to wav
otherwise -- see README).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import requests
from pydub import AudioSegment

from src.config import config

SCENE_GAP_MS = 400


def _synthesize_elevenlabs(text: str, out_path: Path) -> None:
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{config.ELEVENLABS_VOICE_ID}"
    headers = {
        "xi-api-key": config.ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.6, "similarity_boost": 0.8},
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    out_path.write_bytes(resp.content)


def _synthesize_offline(text: str, out_path: Path) -> None:
    import pyttsx3

    engine = pyttsx3.init()
    engine.setProperty("rate", 150)  # slower, clearer for kids' content
    engine.save_to_file(text, str(out_path))
    engine.runAndWait()


def synthesize_scene(text: str, out_path: Path, backend: Optional[str] = None) -> Path:
    backend = backend or config.TTS_BACKEND
    if backend == "elevenlabs":
        if not (config.ELEVENLABS_API_KEY and config.ELEVENLABS_VOICE_ID):
            raise RuntimeError(
                "TTS_BACKEND=elevenlabs requires ELEVENLABS_API_KEY and "
                "ELEVENLABS_VOICE_ID to be set."
            )
        _synthesize_elevenlabs(text, out_path)
    elif backend == "offline":
        _synthesize_offline(text, out_path)
    else:
        raise ValueError(f"Unknown TTS_BACKEND: {backend}")
    return out_path


def generate_voiceover(script_path: str, out_dir: Optional[str] = None) -> Path:
    """
    Generate one audio file per scene plus a concatenated full track.
    Returns the path to the full track.
    """
    script = json.loads(Path(script_path).read_text())
    out_dir = Path(out_dir or config.OUTPUT_DIR) / "audio" / _slug(script["title"])
    out_dir.mkdir(parents=True, exist_ok=True)

    combined = AudioSegment.silent(duration=0)
    for scene in script["scenes"]:
        text = scene["voiceover"]
        if text.startswith("[") and text.endswith("]"):
            # Placeholder lines (e.g. "[ORIGINAL SONG PLACEHOLDER: ...]") are
            # not synthesized -- they mark a spot for a composed song/music,
            # not narration.
            print(f"Skipping scene {scene['scene_number']} (non-VO placeholder): {text}")
            continue

        scene_path = out_dir / f"scene-{scene['scene_number']:02d}.wav"
        synthesize_scene(text, scene_path)
        clip = AudioSegment.from_file(scene_path)
        combined += clip + AudioSegment.silent(duration=SCENE_GAP_MS)
        print(f"Synthesized scene {scene['scene_number']} -> {scene_path}")

    full_path = out_dir / "full_narration.wav"
    combined.export(full_path, format="wav")
    print(f"Full narration track: {full_path} ({len(combined) / 1000:.1f}s)")
    return full_path


def _slug(title: str) -> str:
    slug = title.lower().replace(" ", "-").replace("'", "")
    return "".join(c for c in slug if c.isalnum() or c == "-")
