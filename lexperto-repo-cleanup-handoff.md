# Lexperto Repo Cleanup Handoff

Goal: Make `mglasder/lexperto` public and credible enough to include in CV/application links.

---

## Current Assessment

### Verdict
- Includeable after fast cleanup (~1-2 hours), not in current state.
- Core technical work is real and relevant, but repo presentation/runability currently reads as prototype-in-progress.

### Strengths
- Clear project purpose: AI-assisted drafting workflow for court rulings.
- Good technical depth:
  - `src/` extraction + annotation pipeline
  - structured YAML prompt system (`prompts/`)
  - tests exist (`tests/`)
  - LangGraph/LangChain usage in core pipeline
- `.env` is ignored on current `main`.

### Main Issues Blocking Public Link
1. README quality
   - Generic framing, missing files referenced, and setup instructions not aligned to current repo reality.
   - No clear statement of scope, limitations, and prototype status.
2. Runability for outsiders
   - Runtime prompt dependency on LangSmith in core files.
   - Heavy pinned `requirements.txt`.
   - No clear `.env.example` for required env vars.
3. Public data sensitivity optics
   - Tracked `data/schemas/*` include real decision-derived outputs.
   - Even if legal/public, this should be minimized or clearly documented.
4. Hygiene/noise
   - `alex.txt` tracked but empty.
   - `prompts-test/` duplicates partial prompt assets.
   - `experiments/` includes scratch scripts with mixed quality.
5. CV/repo consistency
   - CV mentions Claude API; current code is mostly OpenAI/Azure OpenAI.
   - Keep claims aligned with what actually runs.

---

## Critical Safety Check Before Public

1. Secret exposure audit:
   - Verify whether any secrets were ever committed.
   - If yes, rotate immediately (OpenAI, Anthropic, LangSmith, Google, etc.).
2. Ensure `.env` is never tracked on public branch.
3. Scan for keys/tokens across history and current tree.

Suggested commands:
- `git log --all -- .env`
- `git log -S "OPENAI_API_KEY=" --all --oneline`
- `git log -S "sk-" --all --oneline`
- Optional: `gitleaks detect --source .`

---

## Minimum Viable Cleanup (Do This First)

Target: 60-90 minutes.

1. Rewrite `README.md`:
   - One-paragraph problem statement.
   - What the prototype does (facts section + legal reasoning section support).
   - Architecture (input docs -> extraction/annotation -> drafting components).
   - Stack (accurate, current).
   - Validation statement: prototype tested informally (not institutional deployment).
   - Limitations + non-production disclaimer.

2. Add `.env.example`:
   - Include only required variable names, no values.
   - Document optional vs required vars.

3. Remove obvious repo noise:
   - Delete `alex.txt`.
   - Remove/archive `prompts-test/` unless truly needed.
   - Keep `experiments/` but mark as exploratory in README.

4. Data footprint cleanup:
   - Keep only minimal sample data (prefer fake/anonymized).
   - If retaining decision-derived samples, add explicit README note that these are from public sources and used as research/prototype artifacts.

5. Add "status" section:
   - `Status: Prototype`
   - "No institutional deployment"
   - "Research/engineering exploration in progress"

6. Basic run path:
   - Provide one command that works for a reviewer (e.g., one test module that does not require private services).
   - Separate "API-enabled run" instructions clearly.

---

## Optional High-Impact Cleanup (If Time Allows)

Target: +30-60 minutes.

1. Create slim `requirements-min.txt` or clean direct dependencies in README.
2. Add architecture diagram (simple PNG or Mermaid).
3. Add 2-3 screenshots/GIF of flow (if web/plugin UI exists).
4. Introduce centralized model config (`LLM_MODEL` env var) in core pipeline.
5. If Claude support is claimed, ensure at least one real Claude-enabled path is implemented and smoke-tested.

---

## Claude API Claim Alignment

Current observation:
- Core code in `src/` uses LangChain `init_chat_model(...)` with OpenAI model strings.
- Anthropic deps exist in requirements, but no clear active Claude usage in core flow yet.

If claiming Claude API in CV/repo:
1. Parameterize model via env, e.g. `LLM_MODEL`.
2. Run at least one core path with a Claude model string.
3. Document this in README (OpenAI default + Claude-compatible mode).

If not implemented, do **not** claim Claude API usage yet.

---

## Suggested Public README Skeleton

1. Title + one-line summary
2. Why this exists (problem)
3. What it does (scope)
4. Architecture and components
5. Setup (minimal)
6. Running quick checks
7. Limitations and prototype status
8. Data note (public/anonymized samples)
9. Roadmap

---

## CV Consistency Checklist (Before Application Submission)

1. Repo link works publicly: `https://github.com/mglasder/lexperto`
2. Stack line in CV matches reality:
   - If Claude support added and tested: mention Claude API.
   - If not: keep OpenAI/Azure OpenAI only.
3. Prototype caveat is consistent across CV and README.
4. Avoid over-claiming deployment/adoption.

---

## Deliverable Definition for Cleanup Agent

The execution is complete when:
- Repo is publicly shareable without obvious red flags.
- README is clear and credible for hiring review.
- No exposed secrets in current tree/history without rotation plan.
- CV-relevant claims (stack + validation scope) are accurate.
- Reviewer can run at least one meaningful command successfully.

