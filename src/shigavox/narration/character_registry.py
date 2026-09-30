import json
from pathlib import Path
from typing import ClassVar

from shigavox.narration.character import Character, GenderHint


class CharacterRegistry:
    ALLOWED_VOICE_TRAITS: ClassVar[set[str]] = {
        "aggressive",
        "anxious",
        "authoritative",
        "bold",
        "calm",
        "cheerful",
        "confident",
        "curious",
        "eccentric",
        "energetic",
        "fast-paced",
        "formal",
        "gentle",
        "informal",
        "loud",
        "melancholic",
        "mysterious",
        "nervous",
        "playful",
        "sarcastic",
        "serious",
        "slow",
        "soft-spoken",
        "timid",
    }

    MAX_TRAITS: ClassVar[int] = 5

    def __init__(
        self,
        narrator_voice: str = "am_michael",
        language: str | None = None,
    ) -> None:
        self.characters: dict[str, Character] = {}
        self.narrator_voice = narrator_voice
        self.language = language

    def register(
        self,
        name: str,
        aliases: list[str] | None = None,
        gender_hint: GenderHint = "unknown",
        traits: list[str] | None = None,
        voice: str | None = None,
    ) -> Character:
        normalized_name = self._normalize_identity(name)

        if not normalized_name:
            raise ValueError("Character name cannot be empty.")

        existing = self.resolve(name)

        if existing:
            character = existing

        else:
            character = Character(
                name=name.strip(),
            )

            self.characters[normalized_name] = character

        character.aliases.add(normalized_name)

        if aliases:
            for alias in aliases:
                normalized_alias = self._normalize_identity(alias)

                if normalized_alias:
                    character.aliases.add(normalized_alias)

        if character.gender_hint == "unknown" and gender_hint != "unknown":
            character.gender_hint = gender_hint

        if traits:
            self._merge_traits(
                character=character,
                traits=traits,
            )

        if voice is not None:
            character.voice = voice

        return character

    def resolve(
        self,
        speaker: str,
    ) -> Character | None:
        normalized = self._normalize_identity(speaker)

        if not normalized:
            return None

        character = self.characters.get(normalized)

        if character:
            return character

        for character in self.characters.values():
            if normalized in character.aliases:
                return character

        return None

    def all(
        self,
    ) -> list[Character]:
        return list(self.characters.values())

    def save(
        self,
        path: str | Path,
    ) -> None:
        output_path = Path(path)

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        data = {
            "book": {
                "language": self.language,
            },
            "narrator": {
                "voice": self.narrator_voice,
            },
            "characters": [
                {
                    "name": character.name,
                    "aliases": sorted(character.aliases),
                    "gender_hint": (character.gender_hint),
                    "traits": (character.traits),
                    "voice": (character.voice),
                }
                for character in self.all()
            ],
        }

        output_path.write_text(
            json.dumps(
                data,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    @classmethod
    def load(
        cls,
        path: str | Path,
    ) -> "CharacterRegistry":
        input_path = Path(path)

        if not input_path.exists():
            raise FileNotFoundError(f"Character metadata not found: {input_path}")

        data = json.loads(
            input_path.read_text(
                encoding="utf-8",
            )
        )

        language = data.get(
            "book",
            {},
        ).get("language")

        narrator_voice = data.get(
            "narrator",
            {},
        ).get(
            "voice",
            "am_michael",
        )

        registry = cls(
            narrator_voice=narrator_voice,
            language=language,
        )

        for item in data.get(
            "characters",
            [],
        ):
            registry.register(
                name=item["name"],
                aliases=item.get(
                    "aliases",
                    [],
                ),
                gender_hint=item.get(
                    "gender_hint",
                    "unknown",
                ),
                traits=item.get(
                    "traits",
                    [],
                ),
                voice=item.get(
                    "voice",
                ),
            )

        return registry

    def _merge_traits(
        self,
        character: Character,
        traits: list[str],
    ) -> None:
        for trait in traits:
            normalized = trait.strip().lower()

            if normalized not in self.ALLOWED_VOICE_TRAITS:
                continue

            if normalized in character.traits:
                continue

            if len(character.traits) >= self.MAX_TRAITS:
                break

            character.traits.append(normalized)

    @staticmethod
    def _normalize_identity(
        value: str,
    ) -> str:
        return " ".join(value.strip().lower().split())
