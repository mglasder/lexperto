# Lexperto

Lexperto is a prototype focused on generating a **Sachverhalt draft** from legal input documents with interchangeable OpenAI/Claude model backends.

## Motivation

Drafting and reviewing legal reasoning is repetitive and structure-heavy. Lexperto explores whether LLM-assisted pipelines can reduce manual overhead by turning long rulings into structured, machine-readable intermediate representations.

## Status

**Status: Prototype**

- Research/engineering exploration in progress
- No institutional deployment
- Not a production legal system

## What To Run First (Sachverhalt Draft)

Install and set up:

```bash
pixi install
cp .env.example .env
```

Choose provider/model:

```bash
export LLM_MODEL="openai:gpt-4.1-mini"
# or
export LLM_MODEL="anthropic:claude-opus-4-7"
```

Run drafting tasks:

```bash
pixi run draft-sachverhalt-sample
```

Example with real data (direct CLI use):

```bash
export OPENAI_API_KEY="anthropic:claude-opus-4-7"
             
pixi run python -m src.sachverhalt_draft \
  --verfuegung data/input/Verfuegung_Clean_Format.docx \
  --beschwerde data/input/Beschwerde_Clean_Format.docx \
  --output data/output/sachverhalt_real_case.txt
```

## Environment Variables

See `.env.example` for the full list.

Minimum for OpenAI path:

- `OPENAI_API_KEY`
- `LLM_MODEL=openai:...`

Minimum for Claude path:

- `ANTHROPIC_API_KEY`
- `LLM_MODEL=anthropic:...`

Optional drafting override:

- `SACHVERHALT_DRAFT_MODEL` (used only by `src/sachverhalt_draft.py`)

Optional:

- `LANGSMITH_API_KEY` (only required if you want to pull prompts from LangSmith)
- `EXTRACTION_PROMPT_PATH`, `PARSING_PROMPT_PATH`, `PARAGRAPHS_PROMPT_PATH`, `ANNOTATION_PROMPT_PATH` (local prompt overrides)

## Other Components (Smaller Scope)

Besides the core drafting path, the repository also contains extraction/annotation utilities for processing existing rulings:

- section extraction (`src/extraction.py`)
- paragraph structuring (`src/structuring.py`)
- paragraph annotation (`src/annotation.py`)

These components are useful for schema-oriented analysis workflows and prototype experimentation, but they are not the primary run path for drafting.

## Repository Map

- `src/sachverhalt_draft.py`: canonical Sachverhalt drafting entrypoint
- `src/`: secondary extraction/annotation/structuring pipeline modules
- `tests/`: regression and behavior checks
- `prompts/`: local prompt assets and overrides
- `experiments/`: exploratory scripts (non-stable by design)
- `docs/`: project notes, plans, and architecture-oriented documentation

## Setup (Pixi)

```bash
pixi install
```

Copy environment template:

```bash
cp .env.example .env
```

Run commands inside the Pixi environment:

```bash
pixi shell
```

## Quick checks

Run a local smoke check (no external API calls):

```bash
pixi run smoke
```

Run targeted tests for the structuring core:

```bash
pixi run test-quick
```

Run the full test suite:

```bash
pixi run test
```

## Data note

The `data` directory contains a prototype sample.

