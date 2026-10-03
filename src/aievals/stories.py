from __future__ import annotations

import re
from dataclasses import dataclass

from . import STORIES

AC_ID = re.compile(r"\*\*(S\d+-AC\d+)\*\*")


@dataclass(frozen=True)
class Story:
    id: str  # "S2"
    slug: str  # "S2-volume-discount"
    text: str
    criteria: tuple[str, ...]

    @property
    def test_file(self) -> str:
        return f"test_{self.id.lower()}.py"


def load() -> list[Story]:
    out = []
    for path in sorted(STORIES.glob("S*.md")):
        text = path.read_text()
        out.append(Story(path.stem.split("-")[0], path.stem, text, tuple(AC_ID.findall(text))))
    return out


def api() -> str:
    return (STORIES / "API.md").read_text()


def all_criteria() -> list[str]:
    return [ac for s in load() for ac in s.criteria]
