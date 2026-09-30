import json
from pathlib import Path

from shigavox.narration.segment import NarrationSegment


class NarrationPlanExporter:
    @staticmethod
    def export(
        segments: list[NarrationSegment],
        output_path: str | Path,
    ) -> None:
        output_path = Path(output_path)

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        data = {
            "segments": [
                {
                    "index": index,
                    "type": segment.type,
                    "speaker": segment.speaker,
                    "speaker_confidence": segment.speaker_confidence,
                    "voice": segment.voice,
                    "emotion": segment.emotion,
                    "speed": segment.speed,
                    "text": segment.text,
                }
                for index, segment in enumerate(
                    segments,
                    start=1,
                )
            ]
        }

        output_path.write_text(
            json.dumps(
                data,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
