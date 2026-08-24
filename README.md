# Bounce Video Tools

AI-assisted production pipeline for a kids' educational video channel
("Bounce the Counting Bunny"). Takes a topic and produces: an original
script/storyboard → a voiceover track → a rough-cut assembled video, plus a
regenerable 90-day content calendar. Built to fit the workflow described in
[the planning docs](#background) below.

## What's here

| File | Purpose |
|---|---|
| `main.py` | CLI entry point tying everything together |
| `src/script_generator.py` | Generates an episode script/storyboard (JSON) from a topic. Uses Claude if `ANTHROPIC_API_KEY` is set, otherwise a deterministic offline template. |
| `src/content_safety.py` | Screens generated scripts against a blocklist of known kids'-media characters/shows before anything is saved. **Heuristic only — not legal advice.** |
| `src/tts_pipeline.py` | Synthesizes per-scene voiceover + a concatenated narration track (ElevenLabs or offline `pyttsx3`). |
| `src/video_assembler.py` | Assembles a rough-cut MP4 from the script + narration (+ optional images/video clips and background music). |
| `src/calendar_export.py` | Regenerates the 90-day content calendar as a formatted `.xlsx` (two sheets: Calendar, Milestones). |

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in API keys if you want cloud script-gen / TTS
```

`video_assembler.py` needs **ffmpeg** on your PATH (used by `moviepy`/`pydub`
to encode/decode media). `tts_pipeline.py`'s offline backend needs a system
TTS engine available to `pyttsx3` (e.g. `espeak` on Linux, built-in on
macOS/Windows).

Everything works with **no API keys at all** in offline/template mode — useful
for testing the pipeline end-to-end before paying for cloud script
generation or TTS.

## Usage

```bash
# 1. Generate a script for a new episode
python main.py generate-script --topic "counting to ten" --age 2-5 --duration 90
# -> output/scripts/bounce-learns-about-counting-to-ten.json
# (automatically screened for overlap with existing kids' media — see console output)

# 2. Re-check safety on any script later, e.g. after hand-editing it
python main.py check-safety output/scripts/bounce-learns-about-counting-to-ten.json

# 3. Generate voiceover audio
python main.py generate-audio output/scripts/bounce-learns-about-counting-to-ten.json
# -> output/audio/<slug>/scene-01.wav ... + full_narration.wav

# 4. Assemble a rough-cut video (plain color cards + captions if you don't
#    supply real art yet; drop scene-01.png / scene-01.mp4 etc. into
#    --assets-dir to use real visuals per scene)
python main.py assemble-video output/scripts/bounce-learns-about-counting-to-ten.json \
  --audio-dir output/audio/bounce-learns-about-counting-to-ten \
  --music path/to/royalty-free-bed.mp3
# -> output/video/<slug>.mp4

# 5. Regenerate the 90-day content calendar spreadsheet
python main.py export-calendar
# -> output/Bounce_90_Day_Content_Calendar.xlsx
```

## IP / compliance notes

- `content_safety.py` flags obvious name/title overlaps with existing kids'
  franchises (Cocomelon, Peppa Pig, Bluey, Paw Patrol, Blippi, Sesame
  Street, Disney characters, Baby Shark, etc.). A clean report is **not**
  legal clearance — always have a human read the final script, and use
  original/royalty-free music (traditional public-domain rhymes are fine as
  lyrics/melody, but a specific existing recording/arrangement is not).
- Scripts avoid "subscribe/comment" calls to action to stay
  COPPA/Made-for-Kids friendly — see `SYSTEM_PROMPT` in
  `script_generator.py` if you want to adjust the house style rules.
- This toolkit doesn't handle "Made for Kids" flagging, ad settings, or
  upload — that's done per-video in YouTube Studio.

## Background

This pipeline follows the production plan discussed for the channel: a
recurring original character ("Bounce"), a weekly cadence of 3 new episodes
+ 1 compilation, and a rotating set of learning themes (counting, colors,
shapes, alphabet, etc.) — see the "90-Day Calendar" and "Milestones" sheets
produced by `export-calendar`.
