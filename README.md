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
| `src/tts_pipeline.py` | Synthesizes per-scene voiceover + a concatenated narration track. ElevenLabs, or offline `espeak` — `--sing` cycles pitch per line through a melodic contour on a female-sounding voice as a best-effort "singing" approximation (not real singing synthesis — see the module docstring for the honest limits). |
| `src/cartoon_renderer.py` | Procedurally draws (PIL, no external art/AI-image model) the animated "Bounce" character per scene — hop/wiggle animation, plus a carrot-count graphic parsed out of the scene's own text. This is the default visual when no real art/video asset is supplied. |
| `src/music_generator.py` | Synthesizes an original, royalty-free instrumental loop (pure sine-wave bell tones, no samples) for use as background music. |
| `src/video_assembler.py` | Assembles a rough-cut MP4 from the script + narration (+ cartoon character or your own art, + optional background music). |
| `src/calendar_export.py` | Regenerates the 90-day content calendar as a formatted `.xlsx` (two sheets: Calendar, Milestones). |

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in API keys if you want cloud script-gen / TTS
```

`video_assembler.py` needs **ffmpeg** on your PATH (used by `moviepy`/`pydub`
to encode/decode media: `apt-get install ffmpeg` on Debian/Ubuntu, `brew
install ffmpeg` on macOS). `tts_pipeline.py`'s offline backend shells out to
**`espeak`** (`apt-get install espeak` / `brew install espeak`) — no API key
needed, lower quality than `elevenlabs`.

Everything works with **no API keys at all** in offline/template mode —
verified end-to-end in this repo: `generate-script` (offline template) →
`generate-audio` (espeak) → `assemble-video` (moviepy 2.x + ffmpeg) all run
and produce real output before you pay for any cloud script generation or
TTS.

## Usage

```bash
# 1. Generate a script for a new episode
python main.py generate-script --topic "counting to ten" --age 2-5 --duration 90
# -> output/scripts/bounce-learns-about-counting-to-ten.json
# (automatically screened for overlap with existing kids' media — see console output)

# 2. Re-check safety on any script later, e.g. after hand-editing it
python main.py check-safety output/scripts/bounce-learns-about-counting-to-ten.json

# 3. Generate voiceover audio -- female voice, cycling pitch to approximate singing
python main.py generate-audio output/scripts/bounce-learns-about-counting-to-ten.json --sing
# -> output/audio/<slug>/scene-01.wav ... + full_narration.wav

# 4. Generate an original background music loop (no samples, no copied melodies)
python main.py generate-music --out output/music/theme.wav --bars 6 --tempo 110

# 5. Assemble the video: the animated Bounce cartoon renders automatically
#    per scene when you don't pass --assets-dir (drop scene-01.png /
#    scene-01.mp4 etc. into an assets dir to use your own art instead)
python main.py assemble-video output/scripts/bounce-learns-about-counting-to-ten.json \
  --audio-dir output/audio/bounce-learns-about-counting-to-ten \
  --music output/music/theme.wav
# -> output/video/<slug>.mp4

# 6. Regenerate the 90-day content calendar spreadsheet
python main.py export-calendar
# -> output/Bounce_90_Day_Content_Calendar.xlsx
```

## Example

`examples/scripts/ep1-ten-carrots.json` is a fully worked script in the
exact format `generate-script` produces — see `examples/README.md` to
generate audio/video from it directly without needing an API key first.

## Honest limits of "singing" and "cartoon"

Neither of these use a real generative-AI model (no singing-voice synth
like ElevenLabs Music, no image/video model for the character) — this repo
only has offline/procedural tools available:

- **"Singing"** = `espeak` female voice variant + per-line pitch cycling.
  It sounds like a robotic voice reading rhyming lyrics with some pitch
  variation, not an actual sung melody with rhythm/notes. For real
  singing, use `TTS_BACKEND=elevenlabs` with a voice/model that supports
  it, or record a human vocalist.
- **"Cartoon"** = `cartoon_renderer.py` draws simple geometric shapes (PIL)
  animated in code (hop, ear wiggle, carrot counter) — not real animation
  or AI-generated art. It's original and IP-safe by construction, but it's
  placeholder-grade. Swap in real art/animation via `--assets-dir` once you
  have it.

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
