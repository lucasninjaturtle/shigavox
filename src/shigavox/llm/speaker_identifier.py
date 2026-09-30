import json
from textwrap import dedent

from pydantic import BaseModel, Field

from shigavox.llm.ollama_client import OllamaClient


class SpeakerIdentification(BaseModel):
    speaker: str
    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )


class SpeakerIdentifier:
    def __init__(
        self,
        language: str | None = None,
    ) -> None:
        self.llm = OllamaClient()
        self.language = language

    def identify(
        self,
        dialogue: str,
        context_before: str = "",
        context_after: str = "",
        known_characters: list[str] | None = None,
        previous_speaker: str | None = None,
    ) -> SpeakerIdentification:
        known_characters = known_characters or []

        known = (
            "\n".join(f"- {character}" for character in known_characters)
            if known_characters
            else "none"
        )

        previous = previous_speaker or "none"

        language = self.language if self.language else "unknown or mixed"

        system_prompt = dedent(
            """
            You identify who is speaking quoted dialogue
            in literary text.

            The literary text may be written in any language.

            Analyze names, pronouns, grammatical references,
            titles, descriptions, dialogue tags, and narrative
            context according to the language of the original text.

            You must return:
            - the most likely canonical speaker
            - a confidence score between 0.0 and 1.0

            The confidence score represents how strongly
            the literary evidence supports the attribution.

            Confidence guidance:

            0.95 - 1.00
            Explicit and unambiguous speaker attribution.

            Examples of this kind of evidence include:
            - a named character directly attached to a speech verb
            - narration explicitly stating that a character speaks
            - narration explicitly stating that a character
              continues speaking

            0.80 - 0.94
            Strong contextual evidence, but not fully explicit.

            Examples include:
            - an unambiguous pronoun referring to a known character
            - narration clearly describing one character beginning,
              continuing, repeating, answering, or resuming speech
            - a clear continuation of an already established speaker

            0.65 - 0.79
            Reasonable inference, but meaningful ambiguity remains.

            0.40 - 0.64
            Weak evidence. Multiple speakers could plausibly fit.

            0.00 - 0.39
            The speaker cannot be determined reliably.

            Follow these rules in priority order:

            1. Explicit narrative attribution has highest priority.

               This includes more than simple patterns such as
               "said Character".

               Narration may establish the speaker through phrases
               meaning that a character:
               - said something
               - replied
               - asked
               - began speaking
               - continued speaking
               - went on speaking
               - repeated a question
               - resumed speaking
               - interrupted
               - answered

               Interpret these expressions according to the
               language of the original text.

            2. Resolve the grammatical subject of the surrounding
               narration carefully.

               A character does not need to appear immediately
               beside a speech verb.

               The narration may contain actions or modifiers
               between the character reference and the act of
               speaking.

            3. A character mentioned inside the dialogue is not
               automatically the speaker.

               Names, numbers, titles, places, or other words
               inside the quoted text must not be treated as
               speaker identity without narrative evidence.

            4. A character being addressed is not necessarily
               the speaker.

            5. Resolve pronouns and other references using the
               surrounding narration before guessing.

               Pronouns and references may differ by language.

            6. Do not assume that the protagonist or most frequent
               character is speaking.

            7. Previous speaker is only supporting evidence.

               Use previous speaker only when:
               - there is no stronger attribution,
               - there is no clear speaker change,
               - and the dialogue appears to continue the same
                 speech turn.

               Never allow previous speaker to override stronger
               narrative evidence.

            8. Narrative evidence that explicitly establishes a
               new speaker overrides conversational continuity.

            9. When known characters are provided, return exactly
               one canonical name from that list whenever the
               evidence supports it.

            10. Do not invent characters.

            11. Do not translate canonical character names.

            12. Do not select a character simply because their
                name appears near the dialogue.

            13. Do not give high confidence merely because one
                candidate seems more plausible than the others.

                High confidence requires strong textual evidence.

            14. When the evidence is ambiguous, lower confidence
                instead of forcing certainty.

            15. If the speaker genuinely cannot be determined,
                return "unknown".

            Do not rewrite or translate the dialogue.

            Return JSON only.
            """
        ).strip()

        user_prompt = dedent(
            f"""
            Book language:
            {language}

            Known canonical characters:
            {known}

            Previous dialogue speaker:
            {previous}

            Narration before the dialogue:
            {context_before}

            Dialogue:
            {dialogue}

            Narration after the dialogue:
            {context_after}

            Determine the speaker using this priority:

            explicit narrative attribution
            > grammatical/reference resolution
            > clear speech continuation
            > conversational continuity
            > dialogue content

            Return JSON:

            {{
              "speaker": "Canonical Character Name or unknown",
              "confidence": 0.0
            }}
            """
        ).strip()

        response = self.llm.chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        data = json.loads(response)

        result = SpeakerIdentification.model_validate(data)

        if (
            result.speaker != "unknown"
            and known_characters
            and result.speaker not in known_characters
        ):
            return SpeakerIdentification(
                speaker="unknown",
                confidence=min(
                    result.confidence,
                    0.39,
                ),
            )

        return result
