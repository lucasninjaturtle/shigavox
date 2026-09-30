import json
from textwrap import dedent

from pydantic import BaseModel

from shigavox.llm.ollama_client import OllamaClient


class ReferenceResolution(BaseModel):
    canonical_name: str


class ReferenceResolver:
    def __init__(
        self,
        language: str | None = None,
    ) -> None:
        self.llm = OllamaClient()
        self.language = language

    def resolve(
        self,
        reference: str,
        dialogue: str,
        context_before: str,
        context_after: str,
        known_characters: list[str],
    ) -> str:
        if not known_characters:
            return reference

        known = "\n".join(f"- {character}" for character in known_characters)

        language = self.language if self.language else "unknown or mixed"

        system_prompt = dedent(
            """
            You resolve ambiguous literary character references.

            The literary text may be written in any language.

            Your task is to determine which known character an
            ambiguous reference refers to in the current context.

            A reference may be:
            - a pronoun
            - a title
            - a descriptive noun phrase
            - a role
            - a temporary description
            - another contextual reference to a character

            Examples include concepts such as:
            - third-person pronouns
            - "the man"
            - "the woman"
            - "the girl"
            - "the rabbit"
            - "the creature"

            These examples are conceptual only.

            Do not assume the text is English.

            Resolve references according to the grammar, vocabulary,
            and context of the language used in the literary text.

            Rules:

            - Choose only from the provided known characters.

            - Do not invent new characters.

            - Use the surrounding narration and dialogue.

            - Return the canonical character name exactly as provided
              in the known character list.

            - Do not translate canonical character names.

            - Do not translate or rewrite the book text.

            - A pronoun or description is contextual evidence, not a
              permanent alias.

            - If the reference cannot be resolved reliably, return
              the original reference unchanged.

            - Do not force a character assignment when the evidence
              is ambiguous.

            Return JSON only.
            """
        ).strip()

        user_prompt = dedent(
            f"""
            Book language:
            {language}

            Reference:
            {reference}

            Context before:
            {context_before}

            Dialogue:
            {dialogue}

            Context after:
            {context_after}

            Known characters:
            {known}

            Resolve the reference using the original language
            and literary context.

            Return:

            {{
              "canonical_name": "Character Name"
            }}
            """
        ).strip()

        response = self.llm.chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        data = json.loads(response)

        result = ReferenceResolution.model_validate(data)

        return result.canonical_name
