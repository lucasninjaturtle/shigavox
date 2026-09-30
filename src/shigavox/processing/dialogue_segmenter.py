import re
from dataclasses import dataclass
from typing import Literal


@dataclass
class TextSegment:
    type: Literal["narration", "dialogue"]
    text: str


class DialogueSegmenter:
    QUOTE_PATTERN = re.compile(
        r"“(?P<curly>[^”]+)”"
        r'|"(?P<straight>[^"]+)"'
        r"|«(?P<guillemet>[^»]+)»"
    )

    def segment(
        self,
        text: str,
    ) -> list[TextSegment]:
        segments: list[TextSegment] = []

        cursor = 0

        for match in self.QUOTE_PATTERN.finditer(text):
            narration = text[cursor : match.start()].strip()

            if narration:
                segments.extend(self._split_narration(narration))

            dialogue = self._extract_dialogue(match)

            if dialogue:
                segments.append(
                    TextSegment(
                        type="dialogue",
                        text=dialogue,
                    )
                )

            cursor = match.end()

        remaining = text[cursor:].strip()

        if remaining:
            segments.extend(self._split_narration(remaining))

        return segments

    @staticmethod
    def _extract_dialogue(
        match: re.Match[str],
    ) -> str:
        for group_name in (
            "curly",
            "straight",
            "guillemet",
        ):
            value = match.group(group_name)

            if value is not None:
                return value.strip()

        return ""

    @staticmethod
    def _split_narration(
        text: str,
    ) -> list[TextSegment]:
        paragraphs = [
            paragraph.strip()
            for paragraph in re.split(
                r"\n\s*\n",
                text,
            )
            if paragraph.strip()
        ]

        return [
            TextSegment(
                type="narration",
                text=paragraph,
            )
            for paragraph in paragraphs
        ]
