import argparse
import re
from pathlib import Path

from shigavox.audio.converter import AudioConverter
from shigavox.narration.character_registry import CharacterRegistry
from shigavox.narration.planner import NarrationPlanner
from shigavox.parsers.epub import EpubParser
from shigavox.services.book_analyzer import BookAnalyzer
from shigavox.services.narration_plan_exporter import NarrationPlanExporter
from shigavox.tts.narration_renderer import NarrationRenderer


def analyze_book(
    book_path: Path,
) -> None:
    book_name = book_path.stem

    metadata_path = Path("output") / book_name / "metadata" / "characters.json"

    analyzer = BookAnalyzer()

    registry = analyzer.analyze(
        book_path=book_path,
        output_path=metadata_path,
    )

    print(f"\nBook language: {registry.language or 'unknown'}")

    print("\nCharacters detected:\n")

    for character in registry.all():
        print(
            f"{character.name}\n"
            f"  gender: {character.gender_hint}\n"
            f"  voice: {character.voice}\n"
            f"  traits: "
            f"{', '.join(character.traits) or '-'}"
        )

    print(f"\nCharacter metadata saved to:\n{metadata_path}")


def render_book(
    book_path: Path,
    chapter_number: int | None = None,
) -> None:
    book_name = book_path.stem

    output_root = Path("output") / book_name

    metadata_path = output_root / "metadata" / "characters.json"

    if not metadata_path.exists():
        raise RuntimeError(
            "Character metadata not found.\n"
            "Run analyze first:\n\n"
            f"uv run shigavox analyze "
            f"{book_path}"
        )

    registry = CharacterRegistry.load(metadata_path)

    print(f"\nLoaded character metadata from:\n{metadata_path}")

    print(f"\nBook language: {registry.language or 'unknown'}")

    print(f"\nNarrator: {registry.narrator_voice}")

    print("\nCasting:\n")

    for character in registry.all():
        print(f"{character.name} → {character.voice}")

    parser = EpubParser(book_path)

    chapters = parser.parse()

    if not chapters:
        raise RuntimeError("No chapters found.")

    if chapter_number is not None:
        if chapter_number < 1 or chapter_number > len(chapters):
            raise ValueError(
                f"Invalid chapter: {chapter_number}. Book has {len(chapters)} chapters."
            )

        chapters_to_render = [chapters[chapter_number - 1]]

    else:
        chapters_to_render = chapters

    audio_output = output_root / "ai-audio"

    audio_output.mkdir(
        parents=True,
        exist_ok=True,
    )

    planner = NarrationPlanner(
        character_registry=registry,
    )

    renderer = NarrationRenderer()

    if chapter_number is not None:
        print(f"\nRendering chapter {chapter_number} only...\n")

    else:
        print(f"\nRendering {len(chapters_to_render)} chapters...\n")

    for chapter in chapters_to_render:
        print(f"\nChapter {chapter.index:02}/{len(chapters):02}: {chapter.title}")

        print("Building narration plan...")

        plan = planner.plan(chapter.text)

        plans_output = output_root / "plans"

        plan_path = plans_output / f"{chapter.index:03}.json"

        NarrationPlanExporter.export(
            segments=plan,
            output_path=plan_path,
        )

        print(f"Narration plan saved to: {plan_path}")

        print(f"Narration segments: {len(plan)}")

        uncertain_dialogues = 0

        for index, segment in enumerate(
            plan,
            start=1,
        ):
            preview = segment.text.replace(
                "\n",
                " ",
            )

            if len(preview) > 80:
                preview = f"{preview[:80]}..."

            confidence = (
                f"{segment.speaker_confidence:.2f}"
                if (segment.speaker_confidence is not None)
                else "-"
            )

            if segment.type == "dialogue" and segment.speaker == "narrator":
                uncertain_dialogues += 1

            print(
                f"[{index:03}/"
                f"{len(plan):03}] "
                f"{segment.speaker} "
                f"({segment.voice}) "
                f"confidence="
                f"{confidence} "
                f"emotion="
                f"{segment.emotion} "
                f"speed="
                f"{segment.speed:.2f} "
                f'→ "{preview}"'
            )

        dialogue_count = sum(1 for segment in plan if segment.type == "dialogue")

        print("\nSpeaker attribution summary:")

        print(f"  dialogues: {dialogue_count}")

        print(f"  narrator fallbacks: {uncertain_dialogues}")

        if dialogue_count:
            fallback_percentage = uncertain_dialogues / dialogue_count * 100

            print(f"  fallback rate: {fallback_percentage:.1f}%")

        slug = _slugify(chapter.title)

        base_name = f"{chapter.index:03}-{slug}-ai"

        wav_path = audio_output / f"{base_name}.wav"

        mp3_path = audio_output / f"{base_name}.mp3"

        print("\nRendering audio...")

        renderer.render(
            segments=plan,
            output_path=wav_path,
        )

        print("\nConverting to MP3...")

        AudioConverter.wav_to_mp3(
            input_path=wav_path,
            output_path=mp3_path,
        )

        wav_path.unlink()

        print(f"\nGenerated: {mp3_path}")

    print("\nShigavox audiobook finished successfully.")


def _slugify(
    value: str,
) -> str:
    value = value.lower()

    value = re.sub(
        r"[^a-z0-9]+",
        "-",
        value,
    )

    return value.strip("-") or "chapter"


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="shigavox",
        description=("Local-first AI audiobook generator"),
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    analyze_parser = subparsers.add_parser(
        "analyze",
        help=("Analyze book characters"),
    )

    analyze_parser.add_argument(
        "book",
        type=Path,
    )

    render_parser = subparsers.add_parser(
        "render",
        help="Render audiobook",
    )

    render_parser.add_argument(
        "book",
        type=Path,
    )

    render_parser.add_argument(
        "--chapter",
        type=int,
        help=("Render only the selected chapter number"),
    )

    args = parser.parse_args()

    if args.command == "analyze":
        analyze_book(args.book)

    elif args.command == "render":
        render_book(
            book_path=args.book,
            chapter_number=(args.chapter),
        )


if __name__ == "__main__":
    main()
