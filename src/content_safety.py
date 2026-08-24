"""
Lightweight IP-safety guard for generated scripts.

This is a best-effort screen, NOT legal advice. It flags obvious overlaps
with well-known kids' media brands (character names, show names, and a few
copyrighted/trademarked song titles) so a human can review before anything
goes into production. Passing this check does not guarantee a script is
free of copyright or trademark risk -- always have a human read the final
script and, for anything you're unsure about, consult a lawyer.

Extend BLOCKED_TERMS as you come across more names to watch for.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

BLOCKED_TERMS = [
    # Existing kids' show characters / franchises
    "cocomelon", "jj", "peppa pig", "george pig", "bluey", "bingo (bluey)",
    "paw patrol", "chase", "marshall", "skye", "blippi", "ms rachel",
    "elmo", "sesame street", "big bird", "cookie monster", "mickey mouse",
    "minnie mouse", "spongebob", "dora the explorer", "diego",
    "thomas the tank engine", "barney the dinosaur", "teletubbies",
    "baby shark", "pinkfong", "masha and the bear", "octonauts",
    "daniel tiger", "caillou", "curious george", "winnie the pooh",
    "paddington bear", "peppa",
    # Copyrighted specific recordings/arrangements to avoid re-using verbatim
    "baby shark doo doo", "wheels on the bus (cocomelon)",
]

# Compile once: word-boundary, case-insensitive matches.
_PATTERNS = [
    (term, re.compile(r"(?<!\w)" + re.escape(term) + r"(?!\w)", re.IGNORECASE))
    for term in BLOCKED_TERMS
]


@dataclass
class SafetyReport:
    clean: bool
    matches: list[str] = field(default_factory=list)

    def summary(self) -> str:
        if self.clean:
            return "No known trademark/character overlaps detected."
        lines = ["Potential IP overlap detected -- review before publishing:"]
        for m in self.matches:
            lines.append(f"  - '{m}' matches a known kids'-media term/brand")
        lines.append(
            "This is a heuristic check only. Absence of a match does not "
            "mean the script is legally clear; presence of a match does not "
            "automatically mean it's infringing -- read it yourself."
        )
        return "\n".join(lines)


def check_text(text: str) -> SafetyReport:
    """Scan arbitrary text (script, title, channel name) for blocked terms."""
    matches = [term for term, pattern in _PATTERNS if pattern.search(text)]
    return SafetyReport(clean=len(matches) == 0, matches=matches)


def check_script(script: dict) -> SafetyReport:
    """Scan a generated script dict (see script_generator.Script) as a whole."""
    parts = [script.get("title", ""), script.get("character", "")]
    for scene in script.get("scenes", []):
        parts.append(scene.get("voiceover", ""))
        parts.append(scene.get("visual", ""))
    return check_text("\n".join(parts))
