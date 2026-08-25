import subprocess
from pathlib import Path


class AudioConverter:
    @staticmethod
    def wav_to_mp3(
        input_path: str | Path,
        output_path: str | Path,
    ) -> None:
        input_path = Path(input_path)
        output_path = Path(output_path)

        if not input_path.exists():
            raise FileNotFoundError(f"WAV file not found: {input_path}")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(input_path),
                "-codec:a",
                "libmp3lame",
                "-q:a",
                "2",
                str(output_path),
            ],
            check=True,
        )
