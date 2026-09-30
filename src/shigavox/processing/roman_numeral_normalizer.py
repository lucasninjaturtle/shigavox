import re
from typing import ClassVar


class RomanNumeralNormalizer:
    ROMAN_VALUES: ClassVar[dict[str, int]] = {
        "I": 1,
        "V": 5,
        "X": 10,
        "L": 50,
        "C": 100,
        "D": 500,
        "M": 1000,
    }

    @classmethod
    def normalize(cls, text: str) -> str:
        stripped = text.strip()

        if not re.fullmatch(r"[IVXLCDM]+", stripped):
            return text

        return str(cls._to_int(stripped))

    @classmethod
    def _to_int(cls, value: str) -> int:
        total = 0
        previous = 0

        for char in reversed(value):
            current = cls.ROMAN_VALUES[char]

            if current < previous:
                total -= current
            else:
                total += current

            previous = current

        return total
