import json
from textwrap import dedent

from pydantic import BaseModel

from shigavox.llm.ollama_client import OllamaClient


class DialogueSegment(BaseModel):
    speaker: str
    text: str


class DialogueAnalysis(BaseModel):
    segments: list[DialogueSegment]


class DialogueAnalyzer:
    def __init__(self) -> None:
        self.llm = OllamaClient()

    def analyze(self, text: str) -> list[DialogueSegment]:
        system_prompt = dedent(
            """
            You are a literary dialogue segmentation engine.

            Split the provided passage into sequential speaker segments.

            STRICT RULES:
            - Never rewrite the original text.
            - Never summarize the original text.
            - Never correct grammar or punctuation.
            - Never remove words.
            - Never add words.
            - Preserve the exact wording and order of the source.
            - Text outside quotation marks belongs to the narrator.
            - Text inside quotation marks belongs to the speaking character.
            - Dialogue attribution such as "said Alice", "thought Alice",
              or "replied the Rabbit" ALWAYS belongs to the narrator.
            - If narrator text interrupts dialogue, split it into separate segments.
            - Return JSON only.
            """
        ).strip()

        user_prompt = dedent(
            f"""
            Segment this passage:

            {text}

            Return an object with this structure:

            {{
              "segments": [
                {{
                  "speaker": "narrator",
                  "text": "exact text from source"
                }}
              ]
            }}
            """
        ).strip()

        response = self.llm.chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        print("\nRaw Ollama response:")
        print(response)

        data = json.loads(response)

        analysis = DialogueAnalysis.model_validate(data)

        return analysis.segments
