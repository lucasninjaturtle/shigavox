import json
from textwrap import dedent
from typing import Literal

from pydantic import BaseModel, Field

from shigavox.llm.ollama_client import OllamaClient

Emotion = Literal[
    "neutral",
    "curious",
    "happy",
    "sad",
    "angry",
    "afraid",
    "excited",
    "anxious",
    "authoritative",
    "mysterious",
]


class StyleAnalysis(BaseModel):
    emotion: Emotion
    speed: float = Field(
        ge=0.85,
        le=1.15,
    )


class StyleAnalyzer:
    def __init__(self) -> None:
        self.llm = OllamaClient()

    def analyze(
        self,
        text: str,
        speaker: str,
        segment_type: str,
    ) -> StyleAnalysis:
        system_prompt = dedent(
            """
            You are an audiobook voice director.

            Analyze how the text should be spoken.

            Choose exactly one emotion from:
            - neutral
            - curious
            - happy
            - sad
            - angry
            - afraid
            - excited
            - anxious
            - authoritative
            - mysterious

            Choose a speaking speed between 0.85 and 1.15.

            Guidelines:
            - neutral: around 1.00
            - sad or mysterious: slower, around 0.85-0.95
            - afraid or anxious: around 1.05-1.15
            - excited: around 1.05-1.15
            - angry: around 1.00-1.10
            - curious: around 1.00-1.08
            - authoritative: around 0.90-1.00

            Important:
            - Base the delivery primarily on the text itself.
            - Respect the segment type.
            - If the segment type is "dialogue", treat it as spoken
              dialogue even when the selected voice is the narrator.
            - The narrator may be used as a fallback when the actual
              character speaker could not be identified confidently.
            - Do not invent character identity from the text.
            - Do not rewrite the text.

            Return JSON only.
            """
        ).strip()

        user_prompt = dedent(
            f"""
            Speaker: {speaker}
            Segment type: {segment_type}

            Text:
            {text}

            Return:

            {{
              "emotion": "neutral",
              "speed": 1.0
            }}
            """
        ).strip()

        response = self.llm.chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        data = json.loads(response)

        return StyleAnalysis.model_validate(data)
