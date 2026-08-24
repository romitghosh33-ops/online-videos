"""
Text-to-speech voiceover generation.

Reads a script JSON produced by script_generator, synthesizes one audio
clip per scene's voiceover line, and concatenates them into a single
narration track with a short pause between scenes.

Backends:
  - "elevenlabs": cloud TTS, higher quality, needs ELEVENLABS_API_KEY. Also
    the only backend capable of actual sung/melodic delivery if your
    ElevenLabs voice/model supports it -- this repo does not attempt to
    fake singing on top of it.
  - "offline": shells out to the system `espeak` (or `espeak-ng`) binary --
    local, no network/API key, lower quality. Good default so the pipeline
    is runnable out of the box.

`sing=True` on the offline backend is a best-effort approximation, not real
singing synthesis: it selects a female-sounding espeak voice variant and
cycles espeak's pitch parameter (-p) line-to-line through a small melodic
contour, so consecutive lines land at noticeably different pitches instead
of a flat monotone. It will not carry an actual tune or rhythm -- espeak
has no melody/note-length control. For real singing, use the elevenlabs
backend with a voice/model that supports it, or record a human vocalist.

Requires ffmpeg on PATH for pydub to read/write mp3 (falls back to wav
otherwise -- see README).
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Optional

import requests
from pydub import AudioSegment

from src.config import config

SCENE_GAP_MS = 400

# espeak female-sounding voice variant (formant-shifted, not a distinct
# recorded voice -- espeak has no true female voice bank).
FEMALE_VOICE = "en-us+f3"

# Cycled pitch (espeak -p, 0-99) per line to fake melodic movement across a
# sung passage. Loosely shaped like a simple nursery-rhyme phrase: rises,
# holds, falls, resolves.
SING_PITCH_CONTOUR = [45, 58, 70, 62, 50, 64, 56, 48]


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


def _synthesize_offline(text: str, out_path: Path, voice: Optional[str] = None, pitch: int = 50) -> None:
    binary = shutil.which("espeak") or shutil.which("espeak-ng")
    if not binary:
        raise RuntimeError(
            "TTS_BACKEND=offline requires 'espeak' or 'espeak-ng' to be "
            "installed and on PATH (e.g. `apt-get install espeak` on "
            "Debian/Ubuntu, `brew install espeak` on macOS)."
        )
    cmd = [binary, "-s", "150"]  # -s 150 = slower, clearer for kids' content
    if voice:
        cmd += ["-v", voice]
    cmd += ["-p", str(pitch), "-w", str(out_path), text]
    subprocess.run(cmd, check=True, capture_output=True)


def synthesize_scene(
    text: str,
    out_path: Path,
    backend: Optional[str] = None,
    voice: Optional[str] = None,
    pitch: int = 50,
) -> Path:
    backend = backend or config.TTS_BACKEND
    if backend == "elevenlabs":
        if not (config.ELEVENLABS_API_KEY and config.ELEVENLABS_VOICE_ID):
            raise RuntimeError(
                "TTS_BACKEND=elevenlabs requires ELEVENLABS_API_KEY and "
                "ELEVENLABS_VOICE_ID to be set."
            )
        _synthesize_elevenlabs(text, out_path)
    elif backend == "offline":
        _synthesize_offline(text, out_path, voice=voice, pitch=pitch)
    else:
        raise ValueError(f"Unknown TTS_BACKEND: {backend}")
    return out_path


def generate_voiceover(
    script_path: str,
    out_dir: Optional[str] = None,
    voice: Optional[str] = None,
    sing: bool = False,
) -> Path:
    """
    Generate one audio file per scene plus a concatenated full track.

    voice: espeak voice string (offline backend only), e.g. "en-us+f3" for
        a female-sounding voice. Defaults to FEMALE_VOICE when sing=True,
        otherwise the system default voice.
    sing: cycle pitch per scene through SING_PITCH_CONTOUR to approximate a
        melodic delivery (offline backend only -- see module docstring for
        what this can and can't do).

    Returns the path to the full track.
    """
    script = json.loads(Path(script_path).read_text())
    out_dir = Path(out_dir or config.OUTPUT_DIR) / "audio" / _slug(script["title"])
    out_dir.mkdir(parents=True, exist_ok=True)

    if sing and voice is None:
        voice = FEMALE_VOICE

    combined = AudioSegment.silent(duration=0)
    for i, scene in enumerate(script["scenes"]):
        text = scene["voiceover"]
        if text.startswith("[") and text.endswith("]"):
            # Placeholder lines (e.g. "[ORIGINAL SONG PLACEHOLDER: ...]") are
            # not synthesized -- they mark a spot for a composed song/music,
            # not narration.
            print(f"Skipping scene {scene['scene_number']} (non-VO placeholder): {text}")
            continue

        pitch = SING_PITCH_CONTOUR[i % len(SING_PITCH_CONTOUR)] if sing else 50
        scene_path = out_dir / f"scene-{scene['scene_number']:02d}.wav"
        synthesize_scene(text, scene_path, voice=voice, pitch=pitch)
        clip = AudioSegment.from_file(scene_path)
        combined += clip + AudioSegment.silent(duration=SCENE_GAP_MS)
        print(f"Synthesized scene {scene['scene_number']} -> {scene_path} (voice={voice}, pitch={pitch})")

    full_path = out_dir / "full_narration.wav"
    combined.export(full_path, format="wav")
    print(f"Full narration track: {full_path} ({len(combined) / 1000:.1f}s)")
    return full_path


def _slug(title: str) -> str:
    slug = title.lower().replace(" ", "-").replace("'", "")
    return "".join(c for c in slug if c.isalnum() or c == "-")
