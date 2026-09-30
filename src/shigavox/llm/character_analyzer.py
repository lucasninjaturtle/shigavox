import json
from textwrap import dedent
from typing import Literal

from pydantic import BaseModel, Field

from shigavox.llm.ollama_client import OllamaClient

GenderHint = Literal[
    "male",
    "female",
    "unknown",
]


class CharacterCandidate(BaseModel):
    name: str
    aliases: list[str] = Field(
        default_factory=list,
    )
    gender_hint: GenderHint = "unknown"
    traits: list[str] = Field(
        default_factory=list,
    )


class CharacterAnalysis(BaseModel):
    characters: list[CharacterCandidate]


class CharacterAnalyzer:
    def __init__(
        self,
        language: str | None = None,
    ) -> None:
        self.llm = OllamaClient()
        self.language = language

    def analyze(
        self,
        text: str,
        known_characters: list[str] | None = None,
    ) -> CharacterAnalysis:
        known_characters = known_characters or []

        known = (
            "\n".join(f"- {character}" for character in known_characters)
            if known_characters
            else "none"
        )

        language = self.language if self.language else "unknown or mixed"

        system_prompt = dedent(
            """
            You analyze characters in literary books
            for audiobook casting.

            The literary text may be written in any language.

            Identify characters that appear or speak
            in the provided text.

            Rules:

            - Return canonical character names.

            - Do not include the narrator as a character.

            - Do not invent characters.

            - If a character matches one from the known
              character list, use exactly that canonical name.

            - Do not translate canonical character names.

            - Be conservative when merging identities.

            - Only add an alias when the text clearly establishes
              that both names refer to the same character.

            - Never use generic pronouns as permanent aliases.

            - This applies to pronouns in any language.

            - Pronouns and temporary descriptions may help identify
              a character from context, but they must not become
              permanent aliases unless they function as a stable
              title or identifier.

            - Do not merge two named characters unless the text
              clearly establishes they are the same character.

            - Interpret names, pronouns, titles, descriptions,
              and grammatical references according to the language
              of the original literary text.

            gender_hint:

            - Must be male, female or unknown.

            - Infer it only when the text provides reasonable
              linguistic or contextual evidence.

            - Use unknown when uncertain.

            - Do not guess gender from a name alone when the text
              does not support the inference.

            traits:

            - Traits are used only for audiobook voice casting.

            - Include only characteristics that could affect how
              the character should sound.

            - Prefer traits such as:
              calm, anxious, timid, confident, authoritative,
              energetic, slow, fast-paced, soft-spoken, loud,
              serious, playful, sarcastic, formal, informal,
              melancholic, cheerful, aggressive, gentle,
              nervous, mysterious, eccentric.

            - Do not include plot facts, actions, physical events,
              crimes, locations or temporary situations.

            - Do not include temporary physical states unless they
              clearly represent a persistent speaking style.

            - Keep the list short.

            - Prefer at most 5 useful traits per character.

            Do not rewrite or translate the book text.

            Return JSON only.
            """
        ).strip()

        user_prompt = dedent(
            f"""
            Book language:
            {language}

            Known characters from previous chapters:
            {known}

            Text:
            {text}

            Analyze the characters using the language
            and context of the original text.

            Return JSON with this structure:

            {{
              "characters": [
                {{
                  "name": "Character Name",
                  "aliases": ["Stable Alias"],
                  "gender_hint": "male",
                  "traits": ["anxious", "formal"]
                }}
              ]
            }}
            """
        ).strip()

        response = self.llm.chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        data = json.loads(response)

        return CharacterAnalysis.model_validate(data)
