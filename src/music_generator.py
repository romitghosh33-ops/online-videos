"""
Procedural background music generator.

Synthesizes a short, original, royalty-free instrumental loop (bell/xylophone
timbre over a C-major-pentatonic melody) using pure sine-wave synthesis --
no samples, no external audio files, nothing that could carry someone
else's copyright. Intended as a placeholder music bed for rough-cut videos,
not a finished score.

No dependency beyond numpy + the stdlib `wave` module (deliberately avoids
scipy/pydub here so this module works standalone).
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional
import wave

import numpy as np

SAMPLE_RATE = 44100

# C major pentatonic, C4..C6 (safe, cheerful-sounding scale for kids' content)
SCALE_HZ = {
    "C4": 261.63, "D4": 293.66, "E4": 329.63, "G4": 392.00, "A4": 440.00,
    "C5": 523.25, "D5": 587.33, "E5": 659.25, "G5": 783.99,
}

# A simple 8-step melodic pattern, repeated for `bars` bars. Deliberately
# plain/generic (rises then resolves) so it reads as "a cheerful little
# tune" without echoing any specific existing nursery rhyme's melody.
DEFAULT_PATTERN = ["C4", "D4", "E4", "G4", "E4", "D4", "C4", "E4"]


def _bell_tone(freq: float, duration: float, sample_rate: int = SAMPLE_RATE) -> np.ndarray:
    """A single note: fundamental + two quiet harmonics, exponential decay envelope."""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    envelope = np.exp(-3.5 * t / duration)
    wave_signal = (
        1.00 * np.sin(2 * np.pi * freq * t)
        + 0.35 * np.sin(2 * np.pi * freq * 2 * t)
        + 0.15 * np.sin(2 * np.pi * freq * 3 * t)
    )
    return wave_signal * envelope


def generate_bell_melody(
    out_path: str,
    bars: int = 4,
    tempo_bpm: int = 120,
    pattern: Optional[list[str]] = None,
    amplitude: float = 0.22,
) -> Path:
    """
    Renders `bars` repetitions of `pattern` (one note per beat, 4 beats/bar)
    as a WAV file at out_path. Returns the path.
    """
    pattern = pattern or DEFAULT_PATTERN
    beat_seconds = 60.0 / tempo_bpm
    notes = pattern * bars

    buffer = np.concatenate([_bell_tone(SCALE_HZ[note], beat_seconds) for note in notes])
    buffer = buffer * amplitude
    buffer = np.clip(buffer, -1.0, 1.0)
    pcm = (buffer * 32767).astype(np.int16)

    out_path_p = Path(out_path)
    out_path_p.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out_path_p), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm.tobytes())

    print(f"Generated {len(notes)}-note melody ({len(pcm) / SAMPLE_RATE:.1f}s) -> {out_path_p}")
    return out_path_p
