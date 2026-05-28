# Repository Inventory

Date: 2026-05-28

Baseline inventory of the repository root before presentation cleanup. Each item has a disposition for Task 4 hygiene actions.

## Root Items

| Path | Disposition | Notes |
|------|-------------|-------|
| `README.md` | keep | Project entrypoint |
| `docs/` | keep | Documentation |
| `src/` | keep | Core pipeline |
| `tests/` | keep | Verification |
| `prompts/` | keep | Active prompt assets |
| `prompts-test/` | archived to `archive/prompts-test/` | Legacy/duplicate prompt assets moved out of root to reduce presentation noise while preserving reversibility |
| `alex.txt` | removed | Empty 0-byte root noise file with no project function |
| `amtshilfe-urteil.plugin` | archived to `archive/amtshilfe-urteil.plugin` | Non-core browser/plugin bundle kept for reversibility but removed from root surface |
| `test_temp/` | evaluate/remove if generated artifact | Not present at root (2026-05-28); treat as generated/temporary if recreated |
| `run_logs/` | evaluate/remove if generated artifact | Not present at root (2026-05-28); listed in `.gitignore` — generated runtime logs |

## Additional Root Items (not cleanup candidates)

| Path | Disposition | Notes |
|------|-------------|-------|
| `data/` | keep | Sample schemas and templates; footprint review deferred |
| `experiments/` | keep | Exploratory scripts; mark as non-stable in README |
| `scripts/` | keep | Project utilities |
| `lexperto-repo-cleanup-handoff.md` | keep | Cleanup context for agents/reviewers |
| `LICENSE` | keep | License file |
| `pixi.toml` | keep | Pixi environment and task definitions |
| `pixi.lock` | keep | Locked dependency snapshot |
| `pyproject.toml` | keep | Python project metadata |
| `.env.example` | keep | Environment variable template |
| `.gitignore` | keep | Ignore rules (includes `run_logs/`, `.pytest_cache/`, etc.) |

## Verification (2026-05-28, pre-cleanup)

Command: `ls` (worktree root)

Observed entries: `alex.txt`, `amtshilfe-urteil.plugin`, `data`, `docs`, `experiments`, `lexperto-repo-cleanup-handoff.md`, `LICENSE`, `pixi.lock`, `pixi.toml`, `prompts`, `prompts-test`, `pyproject.toml`, `README.md`, `scripts`, `src`, `tests`

- All required inventory paths with explicit dispositions are accounted for.
- `test_temp/` and `run_logs/` are absent from root; dispositions stand for future or ignored artifacts.
- Dotfiles/directories (`.cursor/`, `.git`, `.pixi/`, `.pytest_cache/`) are local/tooling and excluded from public root presentation targets.

## Executed Hygiene Actions (Task 4)

1. Created `archive/README.md` to document archive purpose and non-core artifact policy.
2. Moved `prompts-test/` to `archive/prompts-test/`.
3. Moved `amtshilfe-urteil.plugin` to `archive/amtshilfe-urteil.plugin`.
4. Removed `alex.txt` (empty file).

Rationale: Keep top-level repository focused on core project assets while keeping non-core artifacts recoverable via archive placement.

## Verification (2026-05-28, post-cleanup)

Command: `ls` (worktree root), then `ls archive`

Observed root entries: `archive`, `data`, `docs`, `experiments`, `lexperto-repo-cleanup-handoff.md`, `LICENSE`, `pixi.lock`, `pixi.toml`, `prompts`, `pyproject.toml`, `README.md`, `scripts`, `src`, `tests`

Observed archive entries: `README.md`, `amtshilfe-urteil.plugin`, `prompts-test`

- Root no longer contains `alex.txt`, `prompts-test/`, or `amtshilfe-urteil.plugin`.
- Archived artifacts remain recoverable and documented.
