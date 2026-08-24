"""
Episode script/storyboard generator.

Given a topic (e.g. "counting to 10", "the color red"), produces a
structured script in the same scene/VO/duration format used across the
"Bounce the Counting Bunny" episode template, as JSON.

Two modes:
  - API mode (default if ANTHROPIC_API_KEY is set): asks Claude to write an
    original script for the given topic, following the house style and the
    IP-safety constraints baked into the prompt.
  - Offline template mode (no API key): fills a simple deterministic
    template so the toolkit is still usable without network access, e.g.
    for testing the rest of the pipeline.

Every generated script is run through content_safety.check_script() before
being written to disk, and the report is saved alongside it.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

from src.config import config
from src.content_safety import check_script

SYSTEM_PROMPT = """\
You write original, COPPA-safe scripts for a children's educational video \
series. Follow these hard rules:

- Never reuse or closely imitate characters, names, songs, or specific \
  scenes from any existing kids' media franchise (e.g. Cocomelon, Peppa \
  Pig, Bluey, Paw Patrol, Blippi, Sesame Street, Baby Shark, Disney \
  properties). Genre and topic overlap (e.g. "a counting song") is fine; \
  copying their specific characters or creative expression is not.
- No calls to action directed at children (no "subscribe", "comment", \
  "click the bell").
- Keep language simple and age-appropriate for the given age range.
- Return ONLY valid JSON matching this schema, no prose outside the JSON:
  {
    "title": str,
    "character": str,
    "topic": str,
    "age_range": str,
    "total_duration_seconds": int,
    "scenes": [
      {"scene_number": int, "visual": str, "voiceover": str, "duration_seconds": int}
    ]
  }
"""


@dataclass
class Scene:
    scene_number: int
    visual: str
    voiceover: str
    duration_seconds: int


@dataclass
class Script:
    title: str
    character: str
    topic: str
    age_range: str
    total_duration_seconds: int
    scenes: list[Scene] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _generate_via_api(topic: str, age_range: str, duration_seconds: int, character: str) -> dict:
    import anthropic

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    user_prompt = (
        f"Write an episode script for a character named '{character}' about "
        f"the topic '{topic}'. Target age range: {age_range}. Target total "
        f"duration: about {duration_seconds} seconds, split into 5-8 scenes."
    )
    response = client.messages.create(
        model=config.ANTHROPIC_MODEL,
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    text = "".join(block.text for block in response.content if block.type == "text")
    return json.loads(text)


def _generate_offline_template(topic: str, age_range: str, duration_seconds: int, character: str) -> dict:
    """Deterministic fallback so the pipeline works without an API key."""
    per_scene = max(duration_seconds // 4, 10)
    return {
        "title": f"{character} Learns About {topic.title()}",
        "character": character,
        "topic": topic,
        "age_range": age_range,
        "total_duration_seconds": per_scene * 4,
        "scenes": [
            {
                "scene_number": 1,
                "visual": f"Wide shot: {character} hops into a bright meadow, waves at camera.",
                "voiceover": f"Hi friends! I'm {character}! Today let's learn about {topic}!",
                "duration_seconds": per_scene,
            },
            {
                "scene_number": 2,
                "visual": f"{character} points at a simple prop related to {topic}.",
                "voiceover": f"Look closely -- this is all about {topic}. Let's explore it together!",
                "duration_seconds": per_scene,
            },
            {
                "scene_number": 3,
                "visual": f"{character} demonstrates {topic} step by step with a cheerful song.",
                "voiceover": f"[ORIGINAL SONG PLACEHOLDER: simple, cheerful melody about {topic}]",
                "duration_seconds": per_scene,
            },
            {
                "scene_number": 4,
                "visual": f"{character} waves goodbye, no subscribe/comment call to action.",
                "voiceover": f"Great job learning about {topic} with me! Bye friends, see you next time!",
                "duration_seconds": per_scene,
            },
        ],
    }


def generate_script(
    topic: str,
    age_range: Optional[str] = None,
    duration_seconds: Optional[int] = None,
    character: Optional[str] = None,
) -> Script:
    age_range = age_range or config.DEFAULT_AGE_RANGE
    duration_seconds = duration_seconds or config.DEFAULT_DURATION_SECONDS
    character = character or config.CHARACTER_NAME

    if config.ANTHROPIC_API_KEY:
        data = _generate_via_api(topic, age_range, duration_seconds, character)
    else:
        data = _generate_offline_template(topic, age_range, duration_seconds, character)

    scenes = [Scene(**s) for s in data["scenes"]]
    return Script(
        title=data["title"],
        character=data["character"],
        topic=data["topic"],
        age_range=data["age_range"],
        total_duration_seconds=data["total_duration_seconds"],
        scenes=scenes,
    )


def save_script(script: Script, out_dir: Optional[str] = None) -> Path:
    out_dir = Path(out_dir or config.OUTPUT_DIR) / "scripts"
    out_dir.mkdir(parents=True, exist_ok=True)

    slug = script.title.lower().replace(" ", "-").replace("'", "")
    slug = "".join(c for c in slug if c.isalnum() or c == "-")
    path = out_dir / f"{slug}.json"

    report = check_script(script.to_dict())
    payload = script.to_dict()
    payload["_safety_report"] = {"clean": report.clean, "matches": report.matches}

    path.write_text(json.dumps(payload, indent=2))
    print(report.summary())
    print(f"Saved script to {path}")
    return path
