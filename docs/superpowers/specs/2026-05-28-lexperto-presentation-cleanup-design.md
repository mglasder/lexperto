# Lexperto Presentation Cleanup Design

Date: 2026-05-28  
Scope: Moderate  
Audience: Hiring reviewers and technical collaborators (balanced)

## 1) Goal

Improve repository presentation so `lexperto` is clearly credible and easy to evaluate in a short review while remaining useful for technical collaborators.

This design prioritizes low-risk, presentation-first changes and avoids broad behavioral refactors.

## 2) Desired Outcome

The cleanup is complete when:

- A reviewer can understand what the project does in under 2-5 minutes.
- A collaborator can quickly find setup, run paths, and architecture context.
- Repository root appears intentional (no confusing or noisy artifacts).
- Prototype status and limitations are explicit and accurate.
- Claims in documentation match current runnable reality.

## 3) Non-Goals

- No core pipeline redesign.
- No feature expansion unrelated to repository presentation.
- No broad test suite overhaul.
- No dependency architecture rewrite.

## 4) Approach

Use a presentation-first cleanup with selective artifact polish:

1. Tighten README scanability for two audiences.
2. Clean root-level noise and improve repository structure clarity.
3. Add a small docs entrypoint and lightweight architecture visual.
4. Keep changes reversible and low-risk.

## 5) Planned Change Set

### 5.1 README improvements

- Add a compact section for hiring reviewers ("2-minute scan").
- Add a technical collaborator section with setup/test orientation.
- Clarify stable vs exploratory areas (`src/`, `tests/`, `experiments/`).
- Ensure quick paths are explicit:
  - Reviewer path (fast confidence check)
  - Developer path (full setup + tests)

### 5.2 Repository hygiene

- Resolve obvious top-level noise (including currently untracked plugin artifact) by removing or archiving with clear naming.
- Keep root focused on intentional, project-facing files.
- Avoid destructive cleanup where intent is unclear; prefer explicit archival.

### 5.3 Docs orientation

- Add `docs/README.md` as a navigation index to key docs.
- Add a minimal architecture diagram (Mermaid) for quick structural understanding.

### 5.4 Data and exploratory framing

- Keep exploratory material but mark it clearly as non-stable.
- Keep sample data framing concise and presentation-safe.
- Avoid claims that imply legal correctness or production deployment.

## 6) Execution Order

1. Baseline inventory of root files and cleanup candidates.
2. Finalize README structure first to anchor all wording.
3. Apply hygiene edits (remove/archive noise).
4. Add docs index and architecture Mermaid.
5. Perform consistency pass across updated docs.
6. Verify documented paths/commands are coherent.

## 7) Risks and Mitigations

### Risk: useful files removed during cleanup
- Mitigation: archive uncertain artifacts instead of deleting.

### Risk: documentation overclaims capability
- Mitigation: validate every claim against current code and commands.

### Risk: audience mismatch (too shallow vs too technical)
- Mitigation: separate reviewer and collaborator pathways in README.

## 8) Validation Plan

- Confirm README sections are scannable and internally consistent.
- Confirm docs links resolve and navigation is obvious.
- Confirm one fast reviewer command path and one developer path are documented clearly.
- Run at least one documented quick path before completion claim.

## 9) Deliverables

- Updated `README.md` with dual-audience presentation.
- Cleaned top-level repository surface.
- New `docs/README.md` index.
- New lightweight architecture Mermaid doc.

## 10) Success Criteria

Success is reached when a hiring reviewer can quickly assess technical credibility and a collaborator can start productively without ambiguity, using only top-level documentation.
