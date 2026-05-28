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
| `prompts-test/` | archive candidate | Legacy/duplicate prompt assets (partial copies under `aerw/`, `sach/`) |
| `alex.txt` | remove candidate | Empty noise file (0 bytes) |
| `amtshilfe-urteil.plugin` | archive candidate | Non-core artifact (~4.6 MB zip); browser/plugin bundle, not part of pipeline |
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

## Verification (2026-05-28)

Command: `ls` (worktree root)

Observed entries: `alex.txt`, `amtshilfe-urteil.plugin`, `data`, `docs`, `experiments`, `lexperto-repo-cleanup-handoff.md`, `LICENSE`, `pixi.lock`, `pixi.toml`, `prompts`, `prompts-test`, `pyproject.toml`, `README.md`, `scripts`, `src`, `tests`

- All required inventory paths with explicit dispositions are accounted for.
- `test_temp/` and `run_logs/` are absent from root; dispositions stand for future or ignored artifacts.
- Dotfiles/directories (`.cursor/`, `.git`, `.pixi/`, `.pytest_cache/`) are local/tooling and excluded from public root presentation targets.
