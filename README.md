# Lexperto

Lexperto is a prototype for AI-assisted drafting support on Swiss Federal Administrative Court tax-information-exchange decisions. It focuses on extracting structured sections and paragraph hierarchies from court rulings and enriching them with legal annotations.

## Status

**Status: Prototype**

- Research/engineering exploration in progress
- No institutional deployment
- Not a production legal system

## Executive Summary

- **Value:** Lexperto explores faster drafting support by converting long tax-information-exchange rulings into structured legal artifacts.
- **Technical depth:** See `Architecture` and `Model Provider Support (OpenAI + Claude)` for pipeline stages, model routing, and outputs.
- **Quick check:** Run `pixi run smoke` for a local no-API pipeline sanity check.
- **Setup:** Run `pixi install`, then copy `.env.example` to `.env`.
- **Targeted tests:** `pixi run test-quick`
- **Full tests:** `pixi run test`
- **Stable core areas:** `src/extraction.py`, `src/structuring.py`, `src/annotation.py`, and `tests/`.
- **Exploratory area:** `experiments/` is intentionally non-stable.

## Motivation

Drafting and reviewing legal reasoning is repetitive and structure-heavy. Lexperto explores whether LLM-assisted pipelines can reduce manual overhead by turning long rulings into structured, machine-readable intermediate representations.

## Scope

Current prototype scope:

1. Extract core ruling sections (`Sachverhalt`, `Erwägungen`, `Entscheid`)
2. Parse section content into hierarchical paragraphs
3. Annotate paragraphs with compact legal titles and point-wise descriptions

Out of scope:

- End-to-end court workflow automation
- Guaranteed legal correctness
- Production reliability guarantees

## Architecture

High-level flow:

1. Input decision document (PDF/text)
2. Section extraction (`src/extraction.py`)
3. Paragraph structuring (`src/structuring.py`)
4. Paragraph annotation (`src/annotation.py`)
5. YAML/JSON artifacts for downstream analysis

## Repository Map

- `src/`: core extraction/annotation/structuring pipeline
- `tests/`: regression and behavior checks for core pipeline stages
- `prompts/`: local prompt assets and overrides
- `experiments/`: exploratory scripts (non-stable by design)
- `docs/`: project notes, plans, and architecture-oriented documentation

## Model Provider Support (OpenAI + Claude)

The core pipeline supports model selection via environment variable, e.g.:

```bash
export LLM_MODEL="openai:gpt-4.1-mini"
# or
export LLM_MODEL="anthropic:claude-3-7-sonnet-latest"
```

`LLM_MODEL` is read by both extraction and annotation pipelines through `langchain`'s `init_chat_model(...)`.

## Setup (Pixi)

```bash
pixi install
```

Copy environment template:

```bash
cp .env.example .env
```

## Environment variables

See `.env.example` for the full list.

Minimum for OpenAI path:

- `OPENAI_API_KEY`
- `LLM_MODEL=openai:...`

Minimum for Claude path:

- `ANTHROPIC_API_KEY`
- `LLM_MODEL=anthropic:...`

Optional:

- `LANGSMITH_API_KEY` (only required if you want to pull prompts from LangSmith)
- `EXTRACTION_PROMPT_PATH`, `PARSING_PROMPT_PATH`, `PARAGRAPHS_PROMPT_PATH`, `ANNOTATION_PROMPT_PATH` (local prompt overrides)

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

The `data/schemas/` directory contains a minimal set of representative prototype samples.

## Limitations

- LLM outputs may vary between runs/providers
- Prompt and schema design are still evolving
- Error handling and observability are prototype-level
- No claim of legal completeness or correctness

## Roadmap

- Improve deterministic parsing quality across varied ruling formats
- Expand provider-agnostic evaluation for OpenAI and Claude models
- Tighten test coverage around extraction and annotation edge cases

