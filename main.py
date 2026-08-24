#!/usr/bin/env python3
"""
CLI entry point for the Bounce video production toolkit.

Usage:
    python main.py generate-script --topic "counting to ten" [--age 2-5] [--duration 90] [--character Bounce]
    python main.py check-safety path/to/script.json
    python main.py generate-audio path/to/script.json [--sing] [--voice en-us+f3]
    python main.py generate-music --out path/to/theme.wav [--bars 4] [--tempo 120]
    python main.py assemble-video path/to/script.json --audio-dir output/audio/<slug> [--assets-dir path] [--music path]
    python main.py export-calendar

Run `python main.py <command> --help` for per-command options.
"""

import argparse
import json
import sys
from pathlib import Path

from src.calendar_export import generate_calendar_workbook
from src.content_safety import check_script
from src.music_generator import generate_bell_melody
from src.script_generator import generate_script, save_script
from src.tts_pipeline import generate_voiceover
from src.video_assembler import assemble_video


def cmd_generate_script(args):
    script = generate_script(
        topic=args.topic,
        age_range=args.age,
        duration_seconds=args.duration,
        character=args.character,
    )
    save_script(script, out_dir=args.out_dir)


def cmd_check_safety(args):
    data = json.loads(Path(args.script_path).read_text())
    report = check_script(data)
    print(report.summary())
    sys.exit(0 if report.clean else 1)


def cmd_generate_audio(args):
    generate_voiceover(args.script_path, out_dir=args.out_dir, voice=args.voice, sing=args.sing)


def cmd_generate_music(args):
    generate_bell_melody(args.out, bars=args.bars, tempo_bpm=args.tempo)


def cmd_assemble_video(args):
    assemble_video(
        script_path=args.script_path,
        audio_dir=args.audio_dir,
        assets_dir=args.assets_dir,
        music_path=args.music,
        out_path=args.out,
    )


def cmd_export_calendar(args):
    generate_calendar_workbook(out_path=args.out)


def main():
    parser = argparse.ArgumentParser(description="Bounce video production toolkit")
    sub = parser.add_subparsers(dest="command", required=True)

    p_script = sub.add_parser("generate-script", help="Generate an episode script/storyboard")
    p_script.add_argument("--topic", required=True, help='e.g. "counting to ten", "the color red"')
    p_script.add_argument("--age", default=None, help="e.g. 2-5 (defaults to DEFAULT_AGE_RANGE)")
    p_script.add_argument("--duration", type=int, default=None, help="target seconds (defaults to DEFAULT_DURATION_SECONDS)")
    p_script.add_argument("--character", default=None, help="defaults to CHARACTER_NAME")
    p_script.add_argument("--out-dir", default=None, help="defaults to OUTPUT_DIR")
    p_script.set_defaults(func=cmd_generate_script)

    p_safety = sub.add_parser("check-safety", help="Re-run the IP-safety screen on a saved script")
    p_safety.add_argument("script_path")
    p_safety.set_defaults(func=cmd_check_safety)

    p_audio = sub.add_parser("generate-audio", help="Synthesize per-scene voiceover + full narration track")
    p_audio.add_argument("script_path")
    p_audio.add_argument("--out-dir", default=None)
    p_audio.add_argument("--voice", default=None, help="espeak voice, e.g. en-us+f3 for female-sounding (offline backend only)")
    p_audio.add_argument("--sing", action="store_true", help="cycle pitch per line to approximate a sung melody (offline backend only, best-effort)")
    p_audio.set_defaults(func=cmd_generate_audio)

    p_music = sub.add_parser("generate-music", help="Synthesize an original background music loop (no samples, no copied melodies)")
    p_music.add_argument("--out", required=True)
    p_music.add_argument("--bars", type=int, default=4)
    p_music.add_argument("--tempo", type=int, default=120)
    p_music.set_defaults(func=cmd_generate_music)

    p_video = sub.add_parser("assemble-video", help="Assemble the rough-cut video from script + audio (+ optional visuals/music)")
    p_video.add_argument("script_path")
    p_video.add_argument("--audio-dir", required=True, help="dir produced by generate-audio, e.g. output/audio/<slug>")
    p_video.add_argument("--assets-dir", default=None, help="optional dir of scene-01.png / scene-01.mp4 etc.")
    p_video.add_argument("--music", default=None, help="optional background music file")
    p_video.add_argument("--out", default=None)
    p_video.set_defaults(func=cmd_assemble_video)

    p_cal = sub.add_parser("export-calendar", help="Regenerate the 90-day content calendar .xlsx")
    p_cal.add_argument("--out", default=None)
    p_cal.set_defaults(func=cmd_export_calendar)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
