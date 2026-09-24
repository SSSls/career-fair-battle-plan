# Career Fair Battle Plan Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create and behaviorally validate a reusable Jev-powered career-fair strategy skill.

**Architecture:** A compact SKILL.md routes to focused references. Jev produces typed atomic judgments; a dependency-free Python script owns normalization, hard constraints, uncertainty gates, capacity, and tiers. Agent simulations validate the human checkpoint and output behavior.

**Tech Stack:** Markdown, JSON, Python 3 standard library, `unittest`, TypeSafe Jev API contract.

**Spec:** `docs/superpowers/specs/2026-09-23-career-fair-battle-plan-design.md`

## Global Constraints

- No user-specific school, major, visa status, or career path is hardcoded.
- Full resumes are not sent to Jev by default.
- Missing evidence stays unknown.
- External actions require user confirmation.
- Final tiers are calculated in code, not by Jev or prose judgment.

## Review Focus

- Explicit no-sponsorship evidence must block only candidates who need sponsorship.
- Unknown sponsorship must not become a rejection.
- Fair capacity must be derived from time rather than fixed employer counts.
- High role fit with low booth leverage must become `APPLY_ONLINE`.
- Noul uncertainty and Choice/Score confidence must be handled differently.

---

### Task 1: Baseline behavioral tests

**Files:**
- Create: `tests/agent-evals/baseline-results.md`

- [ ] Run three agents without the skill on varied candidate/fair scenarios.
- [ ] Record observed omissions and unsafe assumptions.

### Task 2: Deterministic ranker

**Files:**
- Create: `tests/test_rank_battle_plan.py`
- Create: `career-fair-battle-plan/scripts/rank_battle_plan.py`

**Interfaces:**
- Consumes: a JSON object containing `candidate_profile`, `fair`, and `opportunities`.
- Produces: `build_battle_plan(document: dict) -> dict` and a JSON CLI.

- [ ] Write tests for approval, sponsorship, uncertainty, capacity, and online-only routing.
- [ ] Run tests and confirm expected missing-module failure.
- [ ] Implement the smallest dependency-free ranker that satisfies the contracts.
- [ ] Run the focused test and full suite.

### Task 3: Skill and references

**Files:**
- Create: `career-fair-battle-plan/SKILL.md`
- Create: `career-fair-battle-plan/references/data-contracts.md`
- Create: `career-fair-battle-plan/references/jev-judgments.md`
- Create: `career-fair-battle-plan/references/research-and-events.md`
- Create: `career-fair-battle-plan/agents/openai.yaml`

- [ ] Encode the profile checkpoint and output contract from baseline failures.
- [ ] Document Jev primitives and confidence handling from live official docs.
- [ ] Document evidence provenance, Handshake boundaries, and external-action confirmation.
- [ ] Validate the skill package.

### Task 4: Open-source example and usage

**Files:**
- Create: `career-fair-battle-plan/examples/sample_input.json`
- Create: `career-fair-battle-plan/examples/sample_output.json`
- Create: `README.md`
- Create: `.gitignore`

- [ ] Add a fully anonymized, non-person-specific example.
- [ ] Generate output with the real ranker.
- [ ] Document local use, privacy, and the unverified live-API boundary.

### Task 5: Agent forward tests and refactor

**Files:**
- Create: `tests/agent-evals/forward-results.md`

- [ ] Run seven independent agents with the skill across different backgrounds and fairs.
- [ ] Inspect every response for checkpoint, evidence, uncertainty, tier, and authorization compliance.
- [ ] Patch only failures supported by observed behavior.
- [ ] Re-run validation and all automated tests.
