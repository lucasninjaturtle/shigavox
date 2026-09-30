from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline

from shigavox.narration.segment import NarrationSegment
from shigavox.processing.roman_numeral_normalizer import RomanNumeralNormalizer


class NarrationRenderer:
    SAMPLE_RATE = 24000

    def __init__(
        self,
        lang_code: str = "a",
        short_pause_ms: int = 180,
        paragraph_pause_ms: int = 400,
    ) -> None:
        self.pipeline = KPipeline(lang_code=lang_code)
        self.short_pause_ms = short_pause_ms
        self.paragraph_pause_ms = paragraph_pause_ms

    def render(
        self,
        segments: list[NarrationSegment],
        output_path: str | Path,
    ) -> None:
        output_path = Path(output_path)

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        audio_parts: list[np.ndarray] = []

        print(f"\nRendering {len(segments)} narration segments...\n")

        for index, segment in enumerate(
            segments,
            start=1,
        ):
            confidence = (
                f"{segment.speaker_confidence:.2f}"
                if segment.speaker_confidence is not None
                else "-"
            )

            print(
                f"[{index:02}/{len(segments):02}] "
                f"{segment.speaker} "
                f"({segment.voice}) "
                f"confidence={confidence} "
                f"emotion={segment.emotion} "
                f"speed={segment.speed:.2f}"
            )

            tts_text = RomanNumeralNormalizer.normalize(segment.text)

            generator = self.pipeline(
                tts_text,
                voice=segment.voice,
                speed=segment.speed,
            )

            segment_audio_parts: list[np.ndarray] = []

            for _, _, audio in generator:
                segment_audio_parts.append(audio)

            if not segment_audio_parts:
                continue

            segment_audio = np.concatenate(segment_audio_parts)

            audio_parts.append(segment_audio)

            if index < len(segments):
                next_segment = segments[index]

                pause_ms = self._get_pause_ms(
                    current=segment,
                    next_segment=next_segment,
                )

                audio_parts.append(self._silence(pause_ms))

        if not audio_parts:
            raise RuntimeError("No audio generated.")

        final_audio = np.concatenate(audio_parts)

        sf.write(
            output_path,
            final_audio,
            self.SAMPLE_RATE,
        )

    def _get_pause_ms(
        self,
        current: NarrationSegment,
        next_segment: NarrationSegment,
    ) -> int:
        if current.type == "narration" and next_segment.type == "narration":
            return self.paragraph_pause_ms

        return self.short_pause_ms

    def _silence(
        self,
        duration_ms: int,
    ) -> np.ndarray:
        samples = int(self.SAMPLE_RATE * duration_ms / 1000)

        return np.zeros(
            samples,
            dtype=np.float32,
        )
