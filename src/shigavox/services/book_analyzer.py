from pathlib import Path

from shigavox.llm.character_analyzer import CharacterAnalyzer
from shigavox.narration.character_registry import CharacterRegistry
from shigavox.narration.voice_casting import VoiceCasting
from shigavox.parsers.epub import EpubParser


class BookAnalyzer:
    def analyze(
        self,
        book_path: str | Path,
        output_path: str | Path,
    ) -> CharacterRegistry:
        parser = EpubParser(book_path)

        language = parser.get_language()

        chapters = parser.parse()

        if not chapters:
            raise RuntimeError("No chapters found.")

        character_analyzer = CharacterAnalyzer(language=language)

        registry = CharacterRegistry(language=language)

        print(f"\nBook language: {language or 'unknown'}")

        print(f"\nAnalyzing {len(chapters)} chapters...\n")

        for chapter in chapters:
            print(f"[{chapter.index:02}/{len(chapters):02}] {chapter.title}")

            known_characters = [character.name for character in registry.all()]

            analysis = character_analyzer.analyze(
                text=chapter.text,
                known_characters=(known_characters),
            )

            for candidate in analysis.characters:
                registry.register(
                    name=candidate.name,
                    aliases=(candidate.aliases),
                    gender_hint=(candidate.gender_hint),
                    traits=(candidate.traits),
                )

        print("\nAssigning voices...\n")

        voice_casting = VoiceCasting()

        for character in registry.all():
            voice_casting.assign(character)

            print(f"{character.name}: {character.gender_hint} → {character.voice}")

        registry.save(output_path)

        return registry
