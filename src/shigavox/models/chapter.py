from dataclasses import dataclass


@dataclass
class Chapter:
    index: int
    title: str
    text: str
    source_file: str
