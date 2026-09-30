# Input Books

This directory is used for local book inputs during Shigavox development and testing.

## Included test book

The public repository includes one test fixture:

```text
alice.epub
```

It is included so contributors can clone Shigavox and immediately test the full analysis and rendering pipeline without having to provide their own book first.

The literary work *Alice's Adventures in Wonderland* by Lewis Carroll is in the public domain.

However, a specific EPUB edition may contain formatting, metadata, illustrations, editorial material, or other content with separate licensing terms. Before publishing this repository, this file should document the exact source of the included `alice.epub` and confirm that redistribution of that specific EPUB is permitted.

## Source information

Fill this section with the exact information for the EPUB committed to the repository:

- **Title:** Alice's Adventures in Wonderland
- **Author:** Lewis Carroll
- **Source:** TODO - add the exact source URL or publisher/archive name
- **Edition:** TODO - identify the exact EPUB edition if available
- **Copyright / license status:** TODO - confirm that redistribution of this specific EPUB file is allowed
- **Purpose in this repository:** development and reproducible testing fixture

## Personal books

Do not commit personal, purchased, copyrighted, or otherwise non-redistributable books to this repository.

The recommended Git setup is to ignore all files in this directory except:

```text
README.md
alice.epub
```

That allows the public test fixture to stay versioned while keeping user-provided books private and untracked.

## Example commands

Analyze the included test book:

```bash
uv run shigavox analyze input-books/alice.epub
```

Render chapter 7:

```bash
uv run shigavox render input-books/alice.epub --chapter 7
```
