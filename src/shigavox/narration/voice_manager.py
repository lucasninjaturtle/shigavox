from shigavox.narration.character import GenderHint


class VoiceManager:
    def __init__(self) -> None:
        self.voice_map: dict[str, str] = {
            "narrator": "am_michael",
        }

        self.male_voices = [
            "am_fenrir",
            "am_adam",
        ]

        self.female_voices = [
            "af_bella",
            "af_sarah",
            "af_nicole",
        ]

        self.unknown_voices = [
            "am_fenrir",
            "af_bella",
            "am_adam",
            "af_sarah",
        ]

    def get_voice(
        self,
        speaker: str,
        gender_hint: GenderHint = "unknown",
    ) -> str:
        normalized = speaker.strip().lower()

        if normalized in self.voice_map:
            return self.voice_map[normalized]

        voice = self._assign_voice(
            gender_hint=gender_hint,
        )

        self.voice_map[normalized] = voice

        return voice

    def _assign_voice(
        self,
        gender_hint: GenderHint,
    ) -> str:
        if gender_hint == "male":
            pool = self.male_voices

        elif gender_hint == "female":
            pool = self.female_voices

        else:
            pool = self.unknown_voices

        used_voices = set(self.voice_map.values())

        for voice in pool:
            if voice not in used_voices:
                return voice

        return pool[0]
