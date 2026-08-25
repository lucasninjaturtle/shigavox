import re


class TextChunker:
    def __init__(self, max_chars: int = 1200) -> None:
        self.max_chars = max_chars

    def chunk(self, text: str) -> list[str]:
        paragraphs = [
            paragraph.strip() for paragraph in text.split("\n\n") if paragraph.strip()
        ]

        chunks: list[str] = []
        current_chunk = ""

        for paragraph in paragraphs:
            if len(paragraph) > self.max_chars:
                sentences = self._split_sentences(paragraph)

                for sentence in sentences:
                    current_chunk = self._append_text(
                        current_chunk,
                        sentence,
                        chunks,
                    )
            else:
                current_chunk = self._append_text(
                    current_chunk,
                    paragraph,
                    chunks,
                )

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def _append_text(
        self,
        current_chunk: str,
        text: str,
        chunks: list[str],
    ) -> str:
        if not current_chunk:
            return text

        candidate = f"{current_chunk}\n\n{text}"

        if len(candidate) <= self.max_chars:
            return candidate

        chunks.append(current_chunk)

        return text

    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        sentences = re.split(
            r"(?<=[.!?])\s+",
            text,
        )

        return [sentence.strip() for sentence in sentences if sentence.strip()]
