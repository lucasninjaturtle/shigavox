from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline

from shigavox.processing.text_chunker import TextChunker


class KokoroTTS:
    SAMPLE_RATE = 24000

    def __init__(
        self,
        lang_code: str = "a",
        voice: str = "af_heart",
        max_chunk_chars: int = 1200,
    ) -> None:
        self.pipeline = KPipeline(lang_code=lang_code)
        self.voice = voice
        self.chunker = TextChunker(max_chars=max_chunk_chars)

    def generate(
        self,
        text: str,
        output_path: str | Path,
    ) -> None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        chunks = self.chunker.chunk(text)

        if not chunks:
            raise ValueError("Cannot generate audio from empty text.")

        audio_parts = []

        print(f"\nGenerating audio from {len(chunks)} chunks...")

        for index, chunk in enumerate(chunks, start=1):
            print(f"  [{index:02}/{len(chunks):02}] {len(chunk)} characters")

            generator = self.pipeline(
                chunk,
                voice=self.voice,
            )

            for _, _, audio in generator:
                audio_parts.append(audio)

        if not audio_parts:
            raise RuntimeError("Kokoro did not generate any audio.")

        final_audio = np.concatenate(audio_parts)

        sf.write(
            output_path,
            final_audio,
            self.SAMPLE_RATE,
        )
