import re


class TextCleaner:
    @staticmethod
    def clean(text: str) -> str:
        text = text.replace("\xa0", " ")

        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        text = "\n\n".join(lines)

        # Normalize repeated spaces
        text = re.sub(r"[ \t]+", " ", text)

        # Remove spaces after opening quotes
        text = re.sub(r'([“‘"\']) +', r"\1", text)

        # Remove spaces before closing quotes
        text = re.sub(r' +([”’"\'])', r"\1", text)

        # Remove spaces before punctuation
        text = re.sub(r" +([,.;:!?])", r"\1", text)

        # Keep paragraph separation clean
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()