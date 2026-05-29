# Sachverhalt Core Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a canonical `src` Sachverhalt drafting entrypoint runnable via Pixi with interchangeable OpenAI/Claude model support while preserving experiment drafting logic.

**Architecture:** Introduce a focused `src/sachverhalt_draft.py` module with explicit boundaries: input loading, prompt assembly, model invocation, output persistence, and CLI. Reuse existing utility patterns where stable, and add deterministic tests around file loading, prompt construction, model selection, and end-to-end output behavior. Update Pixi and README so `src` becomes the primary drafting surface and `experiments/experiment.py` is documented as legacy.

**Tech Stack:** Python 3.11+, `langchain` `init_chat_model`, `python-dotenv`, `python-docx`, `pytest`, Pixi tasks

---

## File Structure Map

- Create: `src/sachverhalt_draft.py` — canonical Sachverhalt drafting module and CLI.
- Create: `tests/test_sachverhalt_draft.py` — unit/integration-style tests for the new module.
- Modify: `pixi.toml` — add drafting tasks and syntax-check coverage.
- Modify: `.env.example` — add optional drafting model override variable documentation.
- Modify: `README.md` — add canonical drafting usage section and mark experiment path as legacy.

### Task 1: Add failing tests for `src` drafting module contract

**Files:**
- Create: `tests/test_sachverhalt_draft.py`
- Modify: none
- Test: `tests/test_sachverhalt_draft.py`

- [ ] **Step 1: Write failing tests for file loading, prompt build, model resolve, and output naming**

```python
from pathlib import Path
import pytest

from src.sachverhalt_draft import (
    read_input_text,
    build_sachverhalt_prompt,
    resolve_model_name,
    build_output_path,
)


def test_read_input_text_supports_txt(tmp_path: Path):
    input_file = tmp_path / "verfuegung.txt"
    input_file.write_text("Verfuegung Inhalt", encoding="utf-8")
    assert "Verfuegung Inhalt" in read_input_text(input_file)


def test_read_input_text_rejects_unsupported_extension(tmp_path: Path):
    input_file = tmp_path / "verfuegung.md"
    input_file.write_text("x", encoding="utf-8")
    with pytest.raises(ValueError, match="Unsupported input format"):
        read_input_text(input_file)


def test_build_prompt_contains_required_sections():
    prompt = build_sachverhalt_prompt(
        verfuegung_text="VERFUEGUNG A",
        beschwerde_text="BESCHWERDE B",
        example_order_text="EXAMPLE ORDER",
        example_ruling_text="EXAMPLE RULING",
    )
    assert "AKTUELLE VERFÜGUNG" in prompt
    assert "DOKUMENT" in prompt
    assert "BEISPIEL VERFÜGUNG" in prompt
    assert "BEISPIEL SACHVERHALT" in prompt


def test_resolve_model_name_cli_overrides_env(monkeypatch):
    monkeypatch.setenv("LLM_MODEL", "openai:gpt-4.1-mini")
    assert (
        resolve_model_name(cli_model="anthropic:claude-3-7-sonnet-latest")
        == "anthropic:claude-3-7-sonnet-latest"
    )


def test_build_output_path_uses_input_stem(tmp_path: Path):
    out = build_output_path(
        output_arg=None,
        verfuegung_path=Path("data/input/1_verfuegung_sachverhalt.txt"),
        output_dir=tmp_path,
        timestamp="20260528_123000",
    )
    assert out.name == "sachverhalt_1_verfuegung_sachverhalt_20260528_123000.txt"
```

- [ ] **Step 2: Run tests to confirm failure before implementation**

Run: `pytest tests/test_sachverhalt_draft.py -v`  
Expected: FAIL due to missing `src.sachverhalt_draft` module/functions.

- [ ] **Step 3: Commit failing-test baseline**

```bash
git add tests/test_sachverhalt_draft.py
git commit -m "test: add contract tests for core sachverhalt drafting module"
```

### Task 2: Implement `src/sachverhalt_draft.py` with provider-interchangeable model invocation

**Files:**
- Create: `src/sachverhalt_draft.py`
- Modify: none
- Test: `tests/test_sachverhalt_draft.py`

- [ ] **Step 1: Implement module skeleton with dataclass config and public functions**

```python
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class DraftRunConfig:
    verfuegung_path: Path
    beschwerde_path: Optional[Path]
    output_path: Path
    model_name: str
```

- [ ] **Step 2: Implement input readers and prompt builder preserving experiment logic intent**

```python
def build_sachverhalt_prompt(
    verfuegung_text: str,
    beschwerde_text: Optional[str],
    example_order_text: Optional[str],
    example_ruling_text: Optional[str],
) -> str:
    prompt = (
        "Du bist ein erfahrener Richter am deutschen Amtsgericht. "
        "Formuliere den Sachverhalt fuer ein Urteil basierend auf der gegebenen Verfuegung. "
        "Verwende einen sachlichen, neutralen Stil ohne Wertungen oder Beurteilungen."
    )
    if example_order_text and example_ruling_text:
        prompt += (
            f"\n\nBEISPIEL VERFUEGUNG:\n{example_order_text}\n\n"
            f"BEISPIEL SACHVERHALT:\n{example_ruling_text}\n\n---\n"
        )
    prompt += f"\nAKTUELLE VERFUEGUNG:\n{verfuegung_text}\n"
    if beschwerde_text:
        prompt += f"\nDOKUMENT:\n{beschwerde_text}\n"
    prompt += (
        '\nVerfasse nun einen Sachverhalt fuer diese Verfuegung. '
        'Beginne mit "SACHVERHALT" und beschraenke dich auf die relevanten Fakten.'
    )
    return prompt
```

- [ ] **Step 3: Implement model resolution and provider credential checks**

```python
def resolve_model_name(cli_model: Optional[str]) -> str:
    if cli_model:
        return cli_model
    return os.getenv("LLM_MODEL", "openai:gpt-4.1-mini")


def validate_provider_credentials(model_name: str) -> None:
    if model_name.startswith("openai:") and not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is required for openai:* models")
    if model_name.startswith("anthropic:") and not os.getenv("ANTHROPIC_API_KEY"):
        raise RuntimeError("ANTHROPIC_API_KEY is required for anthropic:* models")
```

- [ ] **Step 4: Implement generation and output persistence with `init_chat_model`**

```python
def generate_sachverhalt(prompt: str, model_name: str) -> str:
    model = init_chat_model(model_name, temperature=0.3)
    response = model.invoke(prompt)
    content = getattr(response, "content", "")
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("Model returned empty content")
    return content.strip()
```

- [ ] **Step 5: Implement CLI entrypoint with args and run summary**

```python
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verfuegung", required=True)
    parser.add_argument("--beschwerde")
    parser.add_argument("--output")
    parser.add_argument("--model")
    args = parser.parse_args()
    run_cli(args)
```

- [ ] **Step 6: Run tests to verify pass**

Run: `pytest tests/test_sachverhalt_draft.py -v`  
Expected: PASS for all tests from Task 1.

- [ ] **Step 7: Commit implementation**

```bash
git add src/sachverhalt_draft.py tests/test_sachverhalt_draft.py
git commit -m "feat: add core src sachverhalt drafting entrypoint with model routing"
```

### Task 3: Add integration-style test coverage with mocked model invocation

**Files:**
- Modify: `tests/test_sachverhalt_draft.py`
- Test: `tests/test_sachverhalt_draft.py`

- [ ] **Step 1: Add a mocked end-to-end CLI run test**

```python
def test_run_cli_writes_output(monkeypatch, tmp_path: Path):
    from src import sachverhalt_draft as module

    verf = tmp_path / "verf.txt"
    verf.write_text("V", encoding="utf-8")
    out = tmp_path / "out.txt"

    class DummyModel:
        def invoke(self, prompt):
            class Resp:
                content = "SACHVERHALT\nGenerated content"
            return Resp()

    monkeypatch.setenv("OPENAI_API_KEY", "test")
    monkeypatch.setattr(module, "init_chat_model", lambda *args, **kwargs: DummyModel())

    module.run_with_paths(
        verfuegung_path=verf,
        beschwerde_path=None,
        output_path=out,
        model_name="openai:gpt-4.1-mini",
    )
    assert out.exists()
    assert "SACHVERHALT" in out.read_text(encoding="utf-8")
```

- [ ] **Step 2: Run targeted test file**

Run: `pytest tests/test_sachverhalt_draft.py -v`  
Expected: PASS with integration-style test included.

- [ ] **Step 3: Commit test enhancements**

```bash
git add tests/test_sachverhalt_draft.py
git commit -m "test: add mocked integration coverage for sachverhalt draft run path"
```

### Task 4: Wire Pixi tasks and syntax checks for canonical drafting usage

**Files:**
- Modify: `pixi.toml`
- Test: Pixi task command execution

- [ ] **Step 1: Add drafting tasks and include new module in syntax-check**

```toml
[tasks]
test = "pytest"
test-quick = "pytest tests/test_structuring.py"
syntax-check = "python -m py_compile src/extraction.py src/annotation.py src/sachverhalt_draft.py scripts/download_annotation_prompt.py"
smoke = "python scripts/smoke_check.py"
draft-sachverhalt = "python -m src.sachverhalt_draft --verfuegung data/input/1_verfuegung_sachverhalt.txt --beschwerde data/input/1_beschwerde_sachverhalt.txt"
draft-sachverhalt-sample = "python -m src.sachverhalt_draft --verfuegung data/input/1_verfuegung_sachverhalt.txt --beschwerde data/input/1_beschwerde_sachverhalt.txt --output data/output/sachverhalt_sample.txt"
```

- [ ] **Step 2: Run syntax and tests after task changes**

Run: `pixi run syntax-check && pytest tests/test_sachverhalt_draft.py -v`  
Expected: PASS for syntax-check and targeted tests.

- [ ] **Step 3: Commit Pixi wiring**

```bash
git add pixi.toml
git commit -m "chore: add pixi tasks for core sachverhalt drafting workflow"
```

### Task 5: Update env/docs to make `src` drafting the primary path

**Files:**
- Modify: `.env.example`
- Modify: `README.md`
- Test: docs command/link consistency checks

- [ ] **Step 1: Extend `.env.example` with optional drafting model override note**

```dotenv
# Optional override for sachverhalt drafting CLI (defaults to LLM_MODEL)
SACHVERHALT_DRAFT_MODEL=
```

- [ ] **Step 2: Update README drafting section with canonical `src` + Pixi path**

```markdown
## Drafting (Sachverhalt) - Core Path

Run the canonical drafting flow from `src`:

```bash
pixi run draft-sachverhalt
```

Provider selection:

```bash
export LLM_MODEL="openai:gpt-4.1-mini"
# or
export LLM_MODEL="anthropic:claude-3-7-sonnet-latest"
```

Legacy note: `experiments/experiment.py` is retained for reference but is no longer the primary path.
```

- [ ] **Step 3: Validate docs consistency for commands and provider notes**

Run: `rg "draft-sachverhalt|LLM_MODEL|anthropic:|openai:" README.md .env.example pixi.toml`  
Expected: all canonical commands and provider notes are present and consistent.

- [ ] **Step 4: Commit docs and env updates**

```bash
git add README.md .env.example
git commit -m "docs: promote src sachverhalt drafting as canonical project path"
```

### Task 6: Final verification across OpenAI/Claude configuration paths

**Files:**
- Modify: none (unless fixes are needed)
- Test: task execution and git status

- [ ] **Step 1: Run full relevant test and checks**

Run: `pytest tests/test_sachverhalt_draft.py -v && pixi run syntax-check`  
Expected: PASS with no failures.

- [ ] **Step 2: Verify OpenAI and Claude config gates without leaking secrets**

Run:  
`pixi run python -m src.sachverhalt_draft --verfuegung data/input/1_verfuegung_sachverhalt.txt --model openai:gpt-4.1-mini`  
Expected: clear credential error if `OPENAI_API_KEY` missing, otherwise output file written.

Run:  
`pixi run python -m src.sachverhalt_draft --verfuegung data/input/1_verfuegung_sachverhalt.txt --model anthropic:claude-3-7-sonnet-latest`  
Expected: clear credential error if `ANTHROPIC_API_KEY` missing, otherwise output file written.

- [ ] **Step 3: Run final status check**

Run: `git status --short`  
Expected: clean working tree.

- [ ] **Step 4: Final fix commit only if verification surfaced issues**

```bash
git add -A
git commit -m "fix: finalize sachverhalt core migration verification adjustments"
```

Expected: only required if verification uncovered issues.
