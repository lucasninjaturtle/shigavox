from pathlib import Path

from bs4 import BeautifulSoup
from ebooklib import epub

from shigavox.models.chapter import Chapter
from shigavox.processing.text_cleaner import TextCleaner

IGNORED_DOCUMENTS = {
    "colophon",
    "cover",
    "epigraph",
    "frontispiece",
    "halftitlepage",
    "imprint",
    "loi",
    "nav",
    "titlepage",
    "toc",
    "uncopyright",
}


class EpubParser:
    def __init__(
        self,
        file_path: str | Path,
    ) -> None:
        self.file_path = Path(file_path)

    def parse(self) -> list[Chapter]:
        book = self._read_book()

        chapters: list[Chapter] = []

        for item_id, _ in book.spine:
            item = book.get_item_with_id(item_id)

            if item is None:
                continue

            if self._should_ignore(item.file_name):
                continue

            soup = BeautifulSoup(
                item.get_content(),
                "html.parser",
            )

            raw_text = self._extract_text(soup)

            text = TextCleaner.clean(raw_text)

            if not text:
                continue

            chapters.append(
                Chapter(
                    index=(len(chapters) + 1),
                    title=(
                        self._extract_title(
                            soup,
                            item.file_name,
                        )
                    ),
                    text=text,
                    source_file=(item.file_name),
                )
            )

        return chapters

    def get_language(
        self,
    ) -> str | None:
        book = self._read_book()

        metadata = book.get_metadata(
            "DC",
            "language",
        )

        if not metadata:
            return None

        raw_language = metadata[0][0]

        if not raw_language:
            return None

        return self._normalize_language(raw_language)

    def _read_book(self):
        if not self.file_path.exists():
            raise FileNotFoundError(f"EPUB file not found: {self.file_path}")

        return epub.read_epub(str(self.file_path))

    @staticmethod
    def _normalize_language(
        value: str,
    ) -> str | None:
        normalized = value.strip().lower().replace("_", "-")

        if not normalized:
            return None

        return normalized.split(
            "-",
            maxsplit=1,
        )[0]

    @staticmethod
    def _should_ignore(
        file_name: str,
    ) -> bool:
        normalized = Path(file_name).stem.lower()

        return normalized in IGNORED_DOCUMENTS

    @staticmethod
    def _extract_text(
        soup: BeautifulSoup,
    ) -> str:
        blocks = soup.find_all(
            [
                "h1",
                "h2",
                "h3",
                "p",
                "blockquote",
            ]
        )

        paragraphs: list[str] = []

        for block in blocks:
            text = block.get_text(
                " ",
                strip=True,
            )

            if text:
                paragraphs.append(text)

        return "\n\n".join(paragraphs)

    @staticmethod
    def _extract_title(
        soup: BeautifulSoup,
        fallback: str,
    ) -> str:
        hgroup = soup.find("hgroup")

        if hgroup:
            parts = [
                element.get_text(
                    " ",
                    strip=True,
                )
                for element in hgroup.find_all(
                    [
                        "h1",
                        "h2",
                        "h3",
                        "p",
                    ],
                    recursive=False,
                )
                if element.get_text(
                    " ",
                    strip=True,
                )
            ]

            if parts:
                return " — ".join(parts)

        heading = soup.find(
            [
                "h1",
                "h2",
                "h3",
            ]
        )

        if heading:
            return heading.get_text(
                " ",
                strip=True,
            )

        if soup.title and soup.title.string:
            return soup.title.string.strip()

        return fallback
