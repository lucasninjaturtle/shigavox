import re
from dataclasses import dataclass
from typing import ClassVar, Literal

from shigavox.narration.character_registry import CharacterRegistry


@dataclass(frozen=True)
class AttributionLanguageRules:
    speech_verbs: tuple[str, ...]
    articles: tuple[str, ...]


@dataclass(frozen=True)
class AttributionMatch:
    speaker: str
    start: int
    end: int


ContextDirection = Literal[
    "before",
    "after",
]


class SpeakerAttributionResolver:
    LANGUAGE_RULES: ClassVar[dict[str, AttributionLanguageRules]] = {
        "en": AttributionLanguageRules(
            speech_verbs=(
                "said",
                "replied",
                "asked",
                "cried",
                "shouted",
                "whispered",
                "muttered",
                "exclaimed",
                "sighed",
                "added",
                "continued",
                "remarked",
                "called",
                "thought",
                "answered",
                "grumbled",
                "pleaded",
                "interrupted",
                "began",
                "went on",
            ),
            articles=("the",),
        ),
        "es": AttributionLanguageRules(
            speech_verbs=(
                "dijo",
                "respondió",
                "preguntó",
                "gritó",
                "susurró",
                "murmuró",
                "exclamó",
                "suspiró",
                "añadió",
                "continuó",
                "comentó",
                "llamó",
                "pensó",
                "contestó",
                "gruñó",
                "suplicó",
                "interrumpió",
                "comenzó",
                "prosiguió",
            ),
            articles=(
                "el",
                "la",
                "los",
                "las",
            ),
        ),
        "pt": AttributionLanguageRules(
            speech_verbs=(
                "disse",
                "respondeu",
                "perguntou",
                "gritou",
                "sussurrou",
                "murmurou",
                "exclamou",
                "suspirou",
                "acrescentou",
                "continuou",
                "comentou",
                "chamou",
                "pensou",
                "resmungou",
                "implorou",
                "interrompeu",
                "começou",
                "prosseguiu",
            ),
            articles=(
                "o",
                "a",
                "os",
                "as",
            ),
        ),
    }

    def __init__(
        self,
        language: str = "en",
    ) -> None:
        self.language = language

    def resolve(
        self,
        context_before: str,
        context_after: str,
        registry: CharacterRegistry,
    ) -> str | None:
        rules = self.LANGUAGE_RULES.get(self.language)

        if rules is None:
            return None

        after_speaker = self._resolve_from_text(
            text=context_after,
            registry=registry,
            rules=rules,
            direction="after",
        )

        if after_speaker:
            return after_speaker

        before_speaker = self._resolve_from_text(
            text=context_before,
            registry=registry,
            rules=rules,
            direction="before",
        )

        return before_speaker

    def _resolve_from_text(
        self,
        text: str,
        registry: CharacterRegistry,
        rules: AttributionLanguageRules,
        direction: ContextDirection,
    ) -> str | None:
        normalized = self._normalize(text)

        if not normalized:
            return None

        verbs = self._build_alternatives(rules.speech_verbs)

        articles = self._build_alternatives(rules.articles)

        matches: list[AttributionMatch] = []

        for character in registry.all():
            names = {
                character.name,
                *character.aliases,
            }

            for name in names:
                escaped_name = re.escape(name)

                patterns = (
                    self._name_then_verb_pattern(
                        escaped_name=escaped_name,
                        verbs=verbs,
                    ),
                    self._verb_then_name_pattern(
                        escaped_name=escaped_name,
                        verbs=verbs,
                        articles=articles,
                    ),
                )

                for pattern in patterns:
                    for match in re.finditer(
                        pattern,
                        normalized,
                        flags=re.IGNORECASE,
                    ):
                        matches.append(
                            AttributionMatch(
                                speaker=character.name,
                                start=match.start(),
                                end=match.end(),
                            )
                        )

        if not matches:
            return None

        best_match = self._select_nearest_match(
            matches=matches,
            direction=direction,
        )

        return best_match.speaker

    @staticmethod
    def _select_nearest_match(
        matches: list[AttributionMatch],
        direction: ContextDirection,
    ) -> AttributionMatch:
        if direction == "after":
            return min(
                matches,
                key=lambda match: (
                    match.start,
                    match.end,
                ),
            )

        return max(
            matches,
            key=lambda match: (
                match.end,
                match.start,
            ),
        )

    @staticmethod
    def _name_then_verb_pattern(
        escaped_name: str,
        verbs: str,
    ) -> str:
        return (
            rf"\b{escaped_name}\b"
            rf"(?:\s+\w+){{0,2}}"
            rf"\s+\b(?:{verbs})\b"
        )

    @staticmethod
    def _verb_then_name_pattern(
        escaped_name: str,
        verbs: str,
        articles: str,
    ) -> str:
        optional_article = rf"(?:(?:{articles})\s+)?" if articles else ""

        return (
            rf"\b(?:{verbs})\b"
            rf"\s+"
            rf"{optional_article}"
            rf"\b{escaped_name}\b"
        )

    @staticmethod
    def _build_alternatives(
        values: tuple[str, ...],
    ) -> str:
        ordered = sorted(
            values,
            key=len,
            reverse=True,
        )

        return "|".join(re.escape(value) for value in ordered)

    @staticmethod
    def _normalize(
        text: str,
    ) -> str:
        return " ".join(text.strip().split())
