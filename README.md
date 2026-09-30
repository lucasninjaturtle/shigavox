# Shigavox

Shigavox is a local-first, open-source audiobook generation engine that converts books into chapter-based narrated audio using local AI and text-to-speech.

The project currently focuses on EPUB books. It extracts and cleans the book text, analyzes characters across the whole book, identifies dialogue speakers, assigns voices, analyzes delivery style, builds inspectable narration plans, and renders audio locally.

> **Core principle:** the LLM analyzes metadata and context, but it never rewrites the original book text. The deterministic parser owns the text.

## Quick Start

### Requirements

Shigavox currently expects:

- Python 3.12
- [uv](https://docs.astral.sh/uv/)
- [Ollama](https://ollama.com/)
- FFmpeg
- espeak-ng

On macOS:

```bash
brew install ffmpeg espeak-ng ollama
```

Install project dependencies:

```bash
uv sync
```

Download the local LLM used by Shigavox:

```bash
ollama pull qwen2.5:7b-instruct
```

You can confirm that Ollama can see the model with:

```bash
ollama list
```

### Analyze a book

The repository includes a public-domain Alice in Wonderland EPUB for testing:

```bash
uv run shigavox analyze input-books/alice.epub
```

The analyze command:

- reads the EPUB metadata;
- detects the book language;
- extracts and cleans chapter text;
- analyzes characters chapter by chapter using the local LLM;
- consolidates a canonical book-wide character registry;
- collects aliases, gender hints, and voice traits;
- assigns default voices;
- saves reusable metadata for later rendering.

### Render a chapter

After analyzing the book, render a specific chapter with:

```bash
uv run shigavox render input-books/alice.epub --chapter 7
```

The render command:

- loads the saved character registry;
- segments narration and dialogue;
- identifies dialogue speakers;
- applies deterministic speaker rules when possible;
- uses local AI for ambiguous attribution;
- applies a confidence threshold and narrator fallback;
- analyzes emotion and speaking speed;
- generates a narration plan;
- renders speech with Kokoro;
- writes chapter audio output.

## Commands

### `analyze`

```bash
uv run shigavox analyze <book.epub>
```

Runs the book-wide analysis phase. Character analysis is intentionally separate from rendering so the complete cast can be discovered before voice assignment and narration.

Example:

```bash
uv run shigavox analyze input-books/alice.epub
```

### `render`

```bash
uv run shigavox render <book.epub> --chapter <number>
```

Builds the narration plan for the selected chapter and renders its audio using the metadata produced by `analyze`.

Example:

```bash
uv run shigavox render input-books/alice.epub --chapter 7
```

## How Shigavox Works

```text
EPUB
  │
  ▼
Metadata + language detection
  │
  ▼
Chapter discovery
  │
  ▼
Text extraction + deterministic cleaning
  │
  ▼
Book-wide local AI character analysis
  │
  ▼
Canonical character registry
  │
  ▼
Automatic voice casting
  │
  ▼
Dialogue segmentation
  │
  ▼
Speaker attribution
  │
  ▼
Emotion + speaking-speed analysis
  │
  ▼
Inspectable narration plan
  │
  ▼
Kokoro TTS
  │
  ▼
Chapter audio
```

### 1. EPUB parsing and text extraction

Shigavox starts from the EPUB spine, discovers the actual reading order, extracts chapter content, removes irrelevant documents such as navigation or cover pages, and cleans the text deterministically.

The LLM does not edit this text.

This separation is important: AI can make mistakes when interpreting meaning, but it is never allowed to paraphrase, summarize, or replace the original book content.

### 2. Book-wide character analysis

Characters are not analyzed independently for every chapter render.

Shigavox first analyzes the whole book chapter by chapter and progressively builds a shared character registry:

```text
Chapter 1
   │
   ├─ discover characters
   ▼
Known character registry
   │
Chapter 2
   │
   ├─ reuse known characters
   ├─ discover new characters
   ▼
Updated registry
   │
  ...
   │
   ▼
Book-wide canonical cast
```

For each character, Shigavox can store information such as:

- canonical name;
- aliases;
- gender hint when supported by the text;
- voice-related traits;
- assigned TTS voice.

The analyzer is conservative: it should reuse known characters when appropriate, avoid inventing characters, avoid using generic pronouns as permanent aliases, and preserve the canonical names found in the book.

### 3. Character and voice selection

Once book analysis is complete, voices are assigned from the available TTS voice pool.

Voice casting happens after the full cast has been discovered so the project can make stable book-wide decisions instead of assigning voices independently chapter by chapter.

The generated character metadata is saved as JSON and can be inspected or edited before rendering.

### 4. Dialogue segmentation

During rendering, Shigavox separates narration from quoted dialogue while preserving the original text.

Currently supported quoted-dialogue forms include common curly quotes, straight quotes, and guillemets.

Spanish-style em-dash dialogue (`—`) requires dedicated parsing and is planned separately rather than being treated as a normal quotation mark.

### 5. Speaker attribution

Speaker identification uses multiple layers rather than blindly trusting the LLM:

```text
Explicit deterministic attribution
            │
            ▼
Deterministic dialogue continuation
            │
            ▼
Context-aware local LLM attribution
            │
            ▼
Confidence threshold
            │
            ▼
Narrator fallback when uncertain
```

#### Explicit deterministic attribution

Simple, strong literary signals are handled without AI whenever possible, for example a canonical character name directly associated with a speech verb.

The resolver is language-aware and currently contains explicit linguistic rules for English, Spanish, and Portuguese.

#### Dialogue continuation

When narration clearly indicates that the previous speaker is continuing, Shigavox can preserve that speaker without asking the LLM again.

This is useful for dialogue split by short narration or parenthetical interruptions.

#### Context-aware local AI attribution

When deterministic evidence is not enough, the local LLM receives:

- the current dialogue;
- relevant narration immediately before it;
- relevant narration immediately after it;
- the previous dialogue speaker as weak evidence;
- the known canonical book characters;
- the language of the book.

The model returns structured metadata containing a canonical speaker and a confidence value.

#### Confidence and narrator fallback

The current speaker-confidence threshold is `0.75`.

If the model cannot identify a known character confidently enough, Shigavox uses the narrator voice instead of forcing an unreliable character assignment.

The confidence value is a heuristic evidence score produced by the model. It is **not** a calibrated probability. A confidence of `0.90` does not mean that the answer has a mathematically verified 90% probability of being correct.

### 6. Delivery style analysis

Each narration or dialogue segment is also analyzed for delivery metadata such as:

- emotion;
- speaking speed.

The original text is still preserved exactly. The AI only decides how the segment should be spoken.

### 7. Narration plan

Before generating audio, Shigavox exports an inspectable JSON narration plan.

A typical segment contains data such as:

```json
{
  "index": 1,
  "type": "dialogue",
  "speaker": "Character Name",
  "speaker_confidence": 0.95,
  "voice": "voice_name",
  "emotion": "curious",
  "speed": 1.05,
  "text": "Original book text"
}
```

This makes the AI decisions visible and debuggable instead of hiding them inside the audio-generation step.

### 8. Text-to-speech rendering

The finalized narration plan is rendered locally with Kokoro.

Each segment uses its selected voice and speaking speed. Shigavox inserts pauses between segments and writes the chapter audio locally.

## Generated Files

Output is organized per book.

A typical structure looks like:

```text
output/
└── alice/
    ├── metadata/
    │   └── characters.json
    ├── plans/
    │   └── 007.json
    └── ...audio output...
```

### `metadata/characters.json`

Contains the reusable book-wide character registry, including:

- book language;
- narrator voice;
- canonical characters;
- aliases;
- gender hints;
- voice traits;
- assigned voices.

### `plans/<chapter>.json`

Contains the fully resolved narration plan for a chapter, including speaker attribution, confidence, voice, emotion, speed, and the untouched original segment text.

## Local AI

Shigavox is designed around local AI rather than mandatory cloud APIs.

The current LLM is:

```text
qwen2.5:7b-instruct
```

and it runs locally through Ollama.

The LLM is used for semantic analysis such as:

- character discovery;
- character metadata;
- speaker identification when deterministic rules are insufficient;
- narration style;
- emotion;
- speaking speed.

The LLM is **not** used to rewrite the book.

This local-first approach provides several benefits:

- book text does not need to be sent to an external AI provider;
- analysis can run offline after the required models are installed;
- generated metadata remains on the local machine;
- the project is not tied to a paid AI API;
- model behavior can be inspected and replaced independently of the parser and TTS engine.

## Features

- EPUB parsing
- chapter discovery from EPUB reading order
- deterministic text cleaning
- book-language detection
- local book-wide character analysis
- canonical character registry
- character aliases
- gender hints for casting
- voice-related character traits
- automatic voice assignment
- narrator voice
- dialogue segmentation
- deterministic speaker attribution
- dialogue-continuation handling
- local LLM speaker attribution
- confidence-based narrator fallback
- emotion analysis
- speaking-speed analysis
- inspectable narration-plan JSON
- chapter-by-chapter rendering
- local Kokoro TTS
- local-first AI architecture

## Language Support

The book language is read from EPUB metadata and propagated through the analysis and narration pipeline.

The architecture is designed to avoid assuming that every book is written in English.

Current deterministic attribution rules exist for:

- English (`en`)
- Spanish (`es`)
- Portuguese (`pt`)

The LLM-based semantic layer is language-aware and receives the book language as context.

TTS language and voice support depends on the voices and language support available in the installed TTS engine.

Spanish-style em-dash dialogue remains a planned parser improvement.

## Project Architecture

```text
src/shigavox/
├── audio/
├── llm/
├── models/
├── narration/
├── parsers/
├── processing/
├── services/
└── tts/
```

### `parsers/`

Reads books and converts source formats into Shigavox chapter models. EPUB is the current supported input format.

### `processing/`

Contains deterministic text-processing utilities such as dialogue segmentation, text cleaning, chunking, and normalization.

### `llm/`

Contains local-AI analysis services, including character analysis, speaker identification, and style analysis.

### `narration/`

Contains the character registry, voice casting, speaker attribution, narration segments, and narration planning logic.

### `tts/`

Contains the Kokoro integration and narration renderer.

### `services/`

Contains higher-level workflows such as book analysis, metadata export, chapter export, and narration-plan export.

### `models/`

Contains core project data models such as chapters.

## Technology Stack

### Core

- Python 3.12
- uv
- Pydantic

### Book processing

- EbookLib
- BeautifulSoup

### Local AI

- Ollama
- `qwen2.5:7b-instruct`

### Text-to-speech

- Kokoro
- espeak-ng
- NumPy
- SoundFile

### Audio

- FFmpeg

### API baseline

- FastAPI

### Development

- Ruff
- pytest

## Development

Format the source code:

```bash
uv run ruff format src/shigavox
```

Run Ruff checks and apply safe fixes:

```bash
uv run ruff check src/shigavox --fix
```

Tests are planned as the project stabilizes further.

## Included Test Book

The repository includes:

```text
input-books/alice.epub
```

as a reproducible test book so a new contributor can clone the project and immediately run the analysis and rendering pipeline.

The literary work *Alice's Adventures in Wonderland* by Lewis Carroll is in the public domain, but the redistribution status of a specific EPUB file depends on the source edition.

The exact source and redistribution information for the included EPUB must therefore be documented in [`input-books/README.md`](input-books/README.md).

User-provided books should not normally be committed to the repository.

## Current Limitations

- EPUB is the current primary input format.
- PDF support is planned.
- TXT support is planned.
- Spanish em-dash dialogue requires dedicated parsing.
- Multiple characters speaking simultaneously are not represented as a first-class narration type yet.
- Speaker confidence is heuristic rather than statistically calibrated.
- Voice casting currently depends on a limited local Kokoro voice pool.
- No graphical interface is available yet.
- Output quality depends partly on the selected local LLM and TTS voices.

## Roadmap

- [x] EPUB parsing
- [x] Chapter discovery
- [x] Book-language metadata
- [x] Local character analysis
- [x] Character registry
- [x] Automatic voice casting
- [x] Dialogue segmentation
- [x] Deterministic speaker attribution
- [x] Contextual local-AI speaker attribution
- [x] Confidence-based narrator fallback
- [x] Emotion and speed analysis
- [x] Narration-plan export
- [x] Chapter audio rendering
- [ ] Multiple-speaker dialogue
- [ ] Spanish em-dash dialogue
- [ ] PDF input
- [ ] TXT input
- [ ] Additional languages
- [ ] Better voice casting and voice previews
- [ ] Manual cast editor
- [ ] Character-specific voice tuning
- [ ] Resumable rendering
- [ ] GUI / richer API workflows

## Privacy

Shigavox is local-first.

When using the default local setup, book analysis and speech synthesis are performed on the user's machine. The project does not require sending book content to a hosted LLM API.

Users remain responsible for the copyright and licensing status of books they process.

## License

Shigavox is released under the MIT License.

See [`LICENSE`](LICENSE) for details.
