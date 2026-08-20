from pathlib import Path

from shigavox.parsers.epub import EpubParser
from shigavox.services.chapter_exporter import ChapterExporter


def main() -> None:
    book_path = Path("input-books/alice.epub")
    output_path = Path("output/alice")

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

    ChapterExporter.export(chapters, output_path)

    print(f"\nExported to: {output_path}")