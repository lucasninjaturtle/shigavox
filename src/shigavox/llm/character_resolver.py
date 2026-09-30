import json
from textwrap import dedent

from pydantic import BaseModel

from shigavox.llm.ollama_client import OllamaClient


class CharacterResolution(BaseModel):
    canonical_name: str
    aliases: list[str]


class CharacterResolver:
    def __init__(self) -> None:
        self.llm = OllamaClient()

    def resolve(
        self,
        detected_speaker: str,
        context: str,
        known_characters: list[str],
    ) -> CharacterResolution:
        known = (
            "\n".join(f"- {character}" for character in known_characters)
            if known_characters
            else "none"
        )

        system_prompt = dedent(
            """
            You resolve literary character references
            into canonical character names.

            Rules:

            - Return one canonical character name.

            - When the reference clearly refers to an existing
              known character, return that character's canonical
              name exactly as provided.

            - Do not invent a new identity when an existing known
              character clearly fits the context.

            - Aliases must only contain stable names, titles,
              nicknames, or descriptions that identify the same
              character.

            - Never store generic pronouns as aliases.

              Examples that must NOT be aliases:
              - he
              - she
              - him
              - her
              - they
              - them
              - it

            - Do not store generic descriptions as permanent
              aliases unless they uniquely and consistently refer
              to that character.

            - Pronouns may help determine the canonical character
              from context, but they must not appear in aliases.

            - Do not rewrite the literary text.

            - Return JSON only.
            """
        ).strip()

        user_prompt = dedent(
            f"""
            Detected speaker:
            {detected_speaker}

            Context:
            {context}

            Known characters:
            {known}

            Return:

            {{
              "canonical_name": "Character Name",
              "aliases": [
                "stable alias"
              ]
            }}
            """
        ).strip()

        response = self.llm.chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        data = json.loads(response)

        result = CharacterResolution.model_validate(data)

        result.aliases = [
            alias
            for alias in result.aliases
            if alias.strip().lower()
            not in {
                "he",
                "she",
                "him",
                "her",
                "they",
                "them",
                "it",
            }
        ]

        return result
