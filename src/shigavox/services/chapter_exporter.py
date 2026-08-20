import re
from pathlib import Path

from shigavox.models.chapter import Chapter


class ChapterExporter:
    @staticmethod
    def export(chapters: list[Chapter], output_dir: str | Path) -> None:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        for chapter in chapters:
            title_slug = ChapterExporter._slugify(chapter.title)

            file_name = f"{chapter.index:03}-{title_slug}.txt"
            file_path = output_path / file_name

            file_path.write_text(chapter.text, encoding="utf-8")

    @staticmethod
    def _slugify(value: str) -> str:
        value = value.lower()
        value = re.sub(r"[^a-z0-9]+", "-", value)

        return value.strip("-") or "chapter"