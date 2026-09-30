from shigavox.narration.character import Character, GenderHint


class VoiceCasting:
    def __init__(self) -> None:
        self.voice_pools: dict[GenderHint, list[str]] = {
            "male": [
                "am_fenrir",
                "am_adam",
            ],
            "female": [
                "af_bella",
                "af_sarah",
                "af_nicole",
            ],
            "unknown": [
                "am_fenrir",
                "af_bella",
                "am_adam",
                "af_sarah",
                "af_nicole",
            ],
        }

        self.voice_usage: dict[str, int] = {}

    def assign(self, character: Character) -> str:
        if character.voice:
            self._register_usage(character.voice)
            return character.voice

        pool = self.voice_pools[character.gender_hint]

        voice = min(
            pool,
            key=lambda candidate: (
                self.voice_usage.get(
                    candidate,
                    0,
                ),
                pool.index(candidate),
            ),
        )

        character.voice = voice

        self._register_usage(voice)

        return voice

    def _register_usage(
        self,
        voice: str,
    ) -> None:
        self.voice_usage[voice] = (
            self.voice_usage.get(
                voice,
                0,
            )
            + 1
        )
