"""
Procedural cartoon renderer for the "Bounce" character.

Draws each frame with PIL/numpy -- no external art or AI image-generation
model involved -- so the pipeline can produce an actual simple animated
character instead of a plain color card + caption. This is deliberately
geometric/placeholder-grade (circles and ellipses, not real animation), but
it IS an original character design (round orange-and-white rabbit,
oversized ears, striped scarf) built specifically to avoid resembling any
existing kids' media character -- see content_safety.py for the IP-safety
screen this whole toolkit runs scripts through.

It also parses simple counting words out of each scene's text (e.g. "one
carrot", "three, four, five") so the on-screen carrot count actually
reflects what the voiceover is saying at that point, rather than being a
generic animation unrelated to the script.
"""

from __future__ import annotations

import math
import re

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from moviepy import VideoClip

_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",  # macOS
    "C:\\Windows\\Fonts\\arialbd.ttf",  # Windows
]


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    for path in _FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()  # tiny, but always available


_NUMERAL_FONT = _load_font(72)

WIDTH, HEIGHT = 1280, 720
SKY_COLOR = (176, 226, 255)
GROUND_COLOR = (198, 232, 173)
GROUND_Y = int(HEIGHT * 0.68)

BODY_COLOR = (247, 170, 90)
BELLY_COLOR = (255, 235, 210)
SCARF_COLORS = [(220, 70, 70), (255, 255, 255)]
OUTLINE = (90, 55, 25)
CARROT_COLOR = (240, 130, 40)
LEAF_COLOR = (70, 150, 70)

NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
}


def _max_count_in_text(text: str) -> int:
    """Highest number-word mentioned in the scene's text, or 0 if none."""
    found = [NUMBER_WORDS[w] for w in re.findall(r"[a-zA-Z]+", text.lower()) if w in NUMBER_WORDS]
    return max(found) if found else 0


def _draw_frame(t: float, duration: float, scene_index: int, count_target: int) -> Image.Image:
    img = Image.new("RGB", (WIDTH, HEIGHT), SKY_COLOR)
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, GROUND_Y, WIDTH, HEIGHT], fill=GROUND_COLOR)
    draw.ellipse([WIDTH - 160, 40, WIDTH - 60, 140], fill=(255, 221, 120))  # sun

    # Hop cycle: a little bounce, phase offset per scene so consecutive
    # scenes don't all hop in lockstep.
    phase = (t + scene_index * 0.3) * (2 * math.pi / 1.2)
    hop = abs(math.sin(phase)) * 26
    cx = WIDTH * 0.28
    body_cy = GROUND_Y - 90 - hop

    ear_wave = math.sin(t * 3.0) * 8

    for side, dx in ((-1, -34), (1, 34)):
        ex = cx + dx + ear_wave * side
        draw.ellipse([ex - 22, body_cy - 150, ex + 22, body_cy - 40], fill=BODY_COLOR, outline=OUTLINE, width=4)
        draw.ellipse([ex - 12, body_cy - 135, ex + 12, body_cy - 60], fill=BELLY_COLOR)

    draw.ellipse([cx - 70, body_cy - 40, cx + 70, body_cy + 90], fill=BODY_COLOR, outline=OUTLINE, width=4)
    draw.ellipse([cx - 40, body_cy + 10, cx + 40, body_cy + 85], fill=BELLY_COLOR)

    scarf_y = body_cy - 20
    for i in range(6):
        color = SCARF_COLORS[i % 2]
        draw.rectangle([cx - 55 + i * 18, scarf_y, cx - 55 + (i + 1) * 18, scarf_y + 16], fill=color)

    draw.ellipse([cx - 28, body_cy - 12, cx - 4, body_cy + 8], fill=(30, 30, 30))
    draw.ellipse([cx + 4, body_cy - 12, cx + 28, body_cy + 8], fill=(30, 30, 30))
    draw.ellipse([cx - 8, body_cy + 6, cx + 8, body_cy + 18], fill=(240, 130, 140))

    if count_target > 0:
        reveal = max(1, min(count_target, int((t / max(duration, 0.01)) * count_target) + 1))
        start_x = WIDTH * 0.55
        for i in range(reveal):
            ccx = start_x + i * 46
            ccy = GROUND_Y - 20
            draw.polygon(
                [(ccx - 14, ccy), (ccx + 14, ccy), (ccx, ccy + 34)],
                fill=CARROT_COLOR, outline=OUTLINE,
            )
            draw.line([(ccx, ccy), (ccx - 6, ccy - 14)], fill=LEAF_COLOR, width=4)
            draw.line([(ccx, ccy), (ccx + 6, ccy - 14)], fill=LEAF_COLOR, width=4)
        draw.text((WIDTH - 130, GROUND_Y - 170), str(reveal), fill=OUTLINE, font=_NUMERAL_FONT)

    return img


def make_cartoon_clip(scene: dict, duration: float, scene_index: int) -> VideoClip:
    """Returns a moviepy VideoClip of the animated Bounce character for one scene."""
    text = f"{scene.get('visual', '')} {scene.get('voiceover', '')}"
    count_target = _max_count_in_text(text)

    def frame_function(t):
        return np.array(_draw_frame(t, duration, scene_index, count_target))

    return VideoClip(frame_function=frame_function, duration=duration)
