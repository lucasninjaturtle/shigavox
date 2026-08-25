import re
from pathlib import Path

from shigavox.audio.converter import AudioConverter
from shigavox.parsers.epub import EpubParser
from shigavox.services.chapter_exporter import ChapterExporter
from shigavox.tts.kokoro import KokoroTTS


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)

    return value.strip("-") or "chapter"


def main() -> None:
    book_path = Path("input-books/alice.epub")

    output_root = Path("output/alice")
    text_output = output_root / "text"
    audio_output = output_root / "audio"

    parser = EpubParser(book_path)
    chapters = parser.parse()

    print(f"\nChapters found: {len(chapters)}\n")

    for chapter in chapters:
        print(
            f"[{chapter.index:02}] "
            f"{chapter.title} "
            f"({chapter.source_file}) "
            f"- {len(chapter.text)} characters"
        )

    ChapterExporter.export(
        chapters,
        text_output,
    )

    print(f"\nText exported to: {text_output}")

    tts = KokoroTTS()

    for chapter in chapters:
        slug = slugify(chapter.title)

        base_name = f"{chapter.index:03}-{slug}"

        wav_path = audio_output / f"{base_name}.wav"
        mp3_path = audio_output / f"{base_name}.mp3"

        print(f"\nGenerating chapter {chapter.index}: {chapter.title}")

        tts.generate(
            text=chapter.text,
            output_path=wav_path,
        )

        print("Converting WAV to MP3...")

        AudioConverter.wav_to_mp3(
            input_path=wav_path,
            output_path=mp3_path,
        )

        wav_path.unlink()

        print(f"Generated: {mp3_path}")

    print("\nShigavox finished successfully.")


if __name__ == "__main__":
    main()
