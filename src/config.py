"""
Central configuration for the Bounce video production toolkit.

All values are read from environment variables (loaded from a local .env
file via python-dotenv, if present). Nothing here is hardcoded so the
toolkit works the same way locally and in CI.
"""

import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    # --- Anthropic (script generation) ---
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5")

    # --- Text-to-speech backend ---
    # "elevenlabs" (cloud, needs ELEVENLABS_API_KEY) or "offline" (pyttsx3,
    # no network / no API key required, lower quality).
    TTS_BACKEND = os.getenv("TTS_BACKEND", "offline")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
    ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "")

    # --- Output locations ---
    OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")

    # --- Brand defaults (used by script_generator when no CLI flag is given) ---
    CHARACTER_NAME = os.getenv("CHARACTER_NAME", "Bounce")
    SHOW_NAME = os.getenv("SHOW_NAME", "Bounce the Counting Bunny")
    DEFAULT_AGE_RANGE = os.getenv("DEFAULT_AGE_RANGE", "2-5")
    DEFAULT_DURATION_SECONDS = int(os.getenv("DEFAULT_DURATION_SECONDS", "90"))


config = Config()
