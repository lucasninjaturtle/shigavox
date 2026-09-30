from dataclasses import dataclass, field
from typing import Literal

GenderHint = Literal["male", "female", "unknown"]


@dataclass
class Character:
    name: str
    aliases: set[str] = field(default_factory=set)
    gender_hint: GenderHint = "unknown"
    traits: list[str] = field(default_factory=list)
    voice: str | None = None
