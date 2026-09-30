from dataclasses import dataclass
from typing import Literal


@dataclass
class NarrationSegment:
    type: Literal["narration", "dialogue"]
    speaker: str
    voice: str
    text: str
    emotion: str | None = None
    speed: float = 1.0
    speaker_confidence: float | None = None
