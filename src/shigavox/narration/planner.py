import re
from typing import ClassVar

from shigavox.llm.speaker_identifier import (
    SpeakerIdentification,
    SpeakerIdentifier,
)
from shigavox.llm.style_analyzer import StyleAnalyzer
from shigavox.narration.character_registry import CharacterRegistry
from shigavox.narration.segment import NarrationSegment
from shigavox.narration.speaker_attribution_resolver import (
    SpeakerAttributionResolver,
)
from shigavox.narration.voice_manager import VoiceManager
from shigavox.processing.dialogue_segmenter import DialogueSegmenter


class NarrationPlanner:
    SPEAKER_CONFIDENCE_THRESHOLD: ClassVar[float] = 0.75
    CONTINUATION_CONFIDENCE: ClassVar[float] = 0.90

    CONTINUATION_PATTERNS: ClassVar[dict[str, tuple[str, ...]]] = {
        "en": (
            r"^(?:he|she)\s+said\b",
            r"^(?:he|she)\s+replied\b",
            r"^(?:he|she)\s+asked\b",
            r"^(?:he|she)\s+cried\b",
            r"^(?:he|she)\s+shouted\b",
            r"^(?:he|she)\s+whispered\b",
            r"^(?:he|she)\s+muttered\b",
            r"^(?:he|she)\s+exclaimed\b",
            r"^(?:he|she)\s+sighed\b",
            r"^(?:he|she)\s+added\b",
            r"^(?:he|she)\s+continued\b",
            r"^(?:he|she)\s+remarked\b",
            r"^(?:he|she)\s+answered\b",
            r"^(?:he|she)\s+grumbled\b",
            r"^(?:he|she)\s+pleaded\b",
            r"^(?:he|she)\s+interrupted\b",
            r"^(?:he|she)\s+began\b",
            r"^(?:he|she)\s+went\s+on\b",
        ),
        "es": (
            r"^(?:él|ella)\s+dijo\b",
            r"^(?:él|ella)\s+respondió\b",
            r"^(?:él|ella)\s+preguntó\b",
            r"^(?:él|ella)\s+gritó\b",
            r"^(?:él|ella)\s+susurró\b",
            r"^(?:él|ella)\s+murmuró\b",
            r"^(?:él|ella)\s+exclamó\b",
            r"^(?:él|ella)\s+suspiró\b",
            r"^(?:él|ella)\s+añadió\b",
            r"^(?:él|ella)\s+continuó\b",
            r"^(?:él|ella)\s+comentó\b",
            r"^(?:él|ella)\s+contestó\b",
            r"^(?:él|ella)\s+interrumpió\b",
            r"^(?:él|ella)\s+comenzó\b",
            r"^(?:él|ella)\s+prosiguió\b",
        ),
        "pt": (
            r"^(?:ele|ela)\s+disse\b",
            r"^(?:ele|ela)\s+respondeu\b",
            r"^(?:ele|ela)\s+perguntou\b",
            r"^(?:ele|ela)\s+gritou\b",
            r"^(?:ele|ela)\s+sussurrou\b",
            r"^(?:ele|ela)\s+murmurou\b",
            r"^(?:ele|ela)\s+exclamou\b",
            r"^(?:ele|ela)\s+suspirou\b",
            r"^(?:ele|ela)\s+acrescentou\b",
            r"^(?:ele|ela)\s+continuou\b",
            r"^(?:ele|ela)\s+comentou\b",
            r"^(?:ele|ela)\s+interrompeu\b",
            r"^(?:ele|ela)\s+começou\b",
            r"^(?:ele|ela)\s+prosseguiu\b",
        ),
    }

    def __init__(
        self,
        character_registry: CharacterRegistry | None = None,
    ) -> None:
        self.character_registry = character_registry or CharacterRegistry()

        language = self.character_registry.language or ""

        self.segmenter = DialogueSegmenter()

        self.speaker_identifier = SpeakerIdentifier(language=language)

        self.style_analyzer = StyleAnalyzer()
        self.voice_manager = VoiceManager()

        self.speaker_attribution_resolver = SpeakerAttributionResolver(
            language=language
        )

    def plan(
        self,
        text: str,
    ) -> list[NarrationSegment]:
        text_segments = self.segmenter.segment(text)

        narration_segments: list[NarrationSegment] = []

        previous_speaker: str | None = None

        for index, segment in enumerate(text_segments):
            speaker_confidence: float | None = None

            if segment.type == "narration":
                speaker = "narrator"

            else:
                immediate_before = (
                    text_segments[index - 1].text
                    if (index > 0 and text_segments[index - 1].type == "narration")
                    else ""
                )

                immediate_after = (
                    text_segments[index + 1].text
                    if (
                        index + 1 < len(text_segments)
                        and text_segments[index + 1].type == "narration"
                    )
                    else ""
                )

                context_before = "\n\n".join(
                    item.text for item in text_segments[max(0, index - 2) : index]
                )

                context_after = immediate_after

                known_characters = [
                    character.name for character in self.character_registry.all()
                ]

                explicit_speaker = self.speaker_attribution_resolver.resolve(
                    context_before=immediate_before,
                    context_after=immediate_after,
                    registry=self.character_registry,
                )

                if explicit_speaker:
                    speaker = explicit_speaker
                    speaker_confidence = 1.0

                else:
                    continuation_speaker = self._resolve_continuation_speaker(
                        narration=immediate_before,
                        previous_speaker=previous_speaker,
                    )

                    if continuation_speaker:
                        speaker = continuation_speaker
                        speaker_confidence = self.CONTINUATION_CONFIDENCE

                    else:
                        identification = self.speaker_identifier.identify(
                            dialogue=segment.text,
                            context_before=context_before,
                            context_after=context_after,
                            known_characters=known_characters,
                            previous_speaker=previous_speaker,
                        )

                        speaker = self._resolve_identification(identification)

                        speaker_confidence = identification.confidence

                if speaker == "narrator":
                    previous_speaker = None

                else:
                    previous_speaker = speaker

            voice = self._get_voice(speaker)

            style = self.style_analyzer.analyze(
                text=segment.text,
                speaker=speaker,
                segment_type=segment.type,
            )

            narration_segments.append(
                NarrationSegment(
                    type=segment.type,
                    speaker=speaker,
                    voice=voice,
                    text=segment.text,
                    emotion=style.emotion,
                    speed=style.speed,
                    speaker_confidence=(speaker_confidence),
                )
            )

        return narration_segments

    def _resolve_continuation_speaker(
        self,
        narration: str,
        previous_speaker: str | None,
    ) -> str | None:
        if not previous_speaker:
            return None

        normalized = self._normalize_context(narration)

        if not normalized:
            return None

        if self._is_parenthetical_interruption(normalized):
            return previous_speaker

        language = self.character_registry.language or ""

        patterns = self.CONTINUATION_PATTERNS.get(
            language,
            (),
        )

        for pattern in patterns:
            if re.search(
                pattern,
                normalized,
                flags=re.IGNORECASE,
            ):
                return previous_speaker

        return None

    @staticmethod
    def _is_parenthetical_interruption(
        narration: str,
    ) -> bool:
        stripped = narration.strip()

        return stripped.startswith("(") and stripped.endswith(")")

    @staticmethod
    def _normalize_context(
        text: str,
    ) -> str:
        return " ".join(text.strip().split())

    def _resolve_identification(
        self,
        identification: SpeakerIdentification,
    ) -> str:
        if (
            identification.speaker == "unknown"
            or identification.confidence < self.SPEAKER_CONFIDENCE_THRESHOLD
        ):
            return "narrator"

        character = self.character_registry.resolve(identification.speaker)

        if character:
            return character.name

        return "narrator"

    def _get_voice(
        self,
        speaker: str,
    ) -> str:
        if speaker == "narrator":
            return self.character_registry.narrator_voice

        character = self.character_registry.resolve(speaker)

        if character and character.voice:
            return character.voice

        gender_hint = character.gender_hint if character else "unknown"

        return self.voice_manager.get_voice(
            speaker=speaker,
            gender_hint=gender_hint,
        )
