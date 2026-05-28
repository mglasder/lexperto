# Sachverhalt Core Migration Design

Date: 2026-05-28  
Scope: Moderate  
Primary Goal: Make Sachverhalt draft generation a first-class `src` capability with provider-interchangeable OpenAI/Claude support.

## 1) Goal

Migrate the Sachverhalt drafting use case from `experiments/` into a coherent core path under `src/`, callable via Pixi, while preserving the existing drafting logic and legal writing intent from the experiment implementation.

The migrated path must support both OpenAI and Claude through a single model-selection interface.

## 2) Why This Change

Current repository behavior is split:

- `experiments/experiment.py` can generate a Sachverhalt draft but is standalone and OpenAI-specific.
- `src/` contains the main architecture for extraction/annotation but not the drafting entrypoint.

This makes project intent unclear and prevents a single canonical run path for drafting in the core system.

## 3) In Scope

- Add a new core Sachverhalt drafting module in `src/`.
- Preserve key prompting and generation behavior from the experiment logic.
- Enable interchangeable OpenAI/Claude model usage via `LLM_MODEL`.
- Add Pixi task(s) for straightforward execution.
- Update documentation to make this the primary drafting path.

## 4) Out of Scope

- Migration of abstract considerations (`Erwägungen`) in this iteration.
- Multi-agent orchestration from `experiments/lexperto.py`.
- Vector-store research integration and relevance-decider logic.
- Full production hardening beyond current prototype standards.

## 5) Architecture and Components

### 5.1 New core entrypoint

Create `src/sachverhalt_draft.py` as the canonical drafting module.

Responsibilities:

- Parse CLI arguments:
  - required: `--verfuegung`
  - optional: `--beschwerde`
  - optional: `--output`
  - optional: `--model` (overrides env)
- Load environment variables.
- Resolve runtime model provider from:
  1. `--model` if provided
  2. `LLM_MODEL` environment variable
  3. safe default (`openai:gpt-4.1-mini`)
- Read input content from `.txt` and `.docx`.
- Build the Sachverhalt prompt with the same intent as current experiment logic.
- Call `init_chat_model(...)` and produce draft text.
- Save output in `data/output/` with deterministic timestamped naming.

### 5.2 Prompt and data flow

Pipeline for the new module:

1. Load Verfügung text.
2. Optionally load Beschwerde text.
3. Optionally load example templates from `data/templates/` (if present).
4. Construct one explicit drafting instruction prompt.
5. Invoke model once for final draft.
6. Persist output file and print concise run summary.

### 5.3 Model-provider interchangeability

Use `langchain` `init_chat_model` so the same flow supports:

- OpenAI models via `LLM_MODEL=openai:...` and `OPENAI_API_KEY`
- Claude models via `LLM_MODEL=anthropic:...` and `ANTHROPIC_API_KEY`

No provider-specific branching in drafting business logic.

## 6) Pixi and CLI Surface

Add dedicated Pixi tasks for core drafting usage:

- `draft-sachverhalt`: generic task using explicit CLI args.
- `draft-sachverhalt-sample`: convenience task wired to existing local sample input files.

Expected result:

- A single reproducible command path for users and reviewers.
- No dependency on `experiments/` to run the core use case.

## 7) Error Handling and Reliability

The new module must fail fast with explicit errors for:

- missing required input file
- unsupported input extension
- empty input content
- missing provider credentials for selected model family
- model invocation failures

Reliability requirements:

- Ensure output directory exists before writing.
- Keep output naming deterministic and timestamped.
- Log model id, input paths, and output path.

## 8) Testing Strategy

### 8.1 Unit tests

- file-loading behavior (`.txt`, `.docx`, unsupported extension, missing file)
- prompt construction behavior (with/without Beschwerde, with/without examples)
- output path generation behavior

### 8.2 Integration-style test

- mock model invocation to verify full run path:
  - loads input
  - builds prompt
  - writes output
  - reports location

### 8.3 Manual provider verification

- one OpenAI run via Pixi task
- one Claude run via Pixi task
- confirm both generate output artifact in `data/output/`

## 9) Documentation Changes

Update `README.md` to make Sachverhalt drafting in `src/` the primary path:

- add explicit "Drafting (Sachverhalt)" section
- include OpenAI and Claude examples
- include exact Pixi commands
- mark experiment script as legacy/exploratory

## 10) Migration Policy for Existing Experiment Script

Do not delete `experiments/experiment.py` in this phase.

Policy:

- Keep it for reference/backward compatibility.
- Reduce confusion by documenting it as non-canonical.
- Route all main instructions to the new `src` entrypoint.

## 11) Success Criteria

Migration is complete when:

- Sachverhalt draft generation is runnable from `src` via Pixi.
- OpenAI and Claude are both supported through `LLM_MODEL` without code changes.
- README points to `src` drafting path as the main project purpose.
- Existing experiment logic intent is preserved in the new core prompting flow.
