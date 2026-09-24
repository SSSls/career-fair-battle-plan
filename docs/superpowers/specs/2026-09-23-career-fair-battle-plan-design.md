# Career Fair Battle Plan Skill Design

## Goal

Build a public, reusable Codex skill that turns an approved candidate profile, a career-fair employer list, role evidence, and fair-time constraints into an evidence-backed visit and application plan. The scarce resource is fair time, so the primary decision is where to spend minutes, not merely whether a role is worth applying to.

## Users and success

The skill must work for career switchers, adjacent-field moves, conventional candidates, international candidates, and candidates exploring several directions. It succeeds when it:

- preserves the user's stated interests instead of inferring desire from resume history;
- exposes unknown facts and low-confidence judgments;
- separates company facts, Jev judgments, and deterministic policy;
- produces a feasible visit order plus `APPLY_ONLINE` opportunities;
- never performs registration, messaging, or applications without confirmation.

## Workflow

1. Parse candidate materials into demonstrated strengths, inferred fit areas, stated preferences, pivots, avoid areas, and hard constraints.
2. Show the profile and stop until the user approves or corrects it.
3. Ingest event and employer information from supplied files, public pages, or a user-authorized authenticated browser session. Do not bypass authentication or invent unavailable Handshake data.
4. Apply cheap deterministic filters, then research only plausible employers and roles. Store each claim with source URL, publication/access dates, status, and source quality.
5. Evaluate each `company x role` pair with one Jev request containing independent Choice, Score, and Noul questions. Jev never calculates the final tier.
6. Feed typed judgments to deterministic code that applies weights, hard constraints, uncertainty gates, and fair capacity.
7. Use a generative model only for explanations, bilingual booth questions, pitches, and follow-up drafts for selected opportunities.

## Judgment model

Jev scores `role_fit`, `evidence_strength`, `conversation_leverage`, and `information_gain` on explicit five-level rubrics. It chooses `best_area` from the approved user-specific area set plus `other`. Noul questions cover sharply defined yes/no claims such as whether supplied evidence supports entry-level accessibility.

Choice and Score use returned confidence. Noul uncertainty is derived from proximity to 0.5. Missing source evidence remains `unknown` and is not converted into a negative fact.

## Deterministic policy

The ranker normalizes Score answers, applies configurable weights, and computes capacity from duration, reserves, and minutes per visit. Explicit role-level disqualifiers may hard-demote an opportunity. Missing or historical sponsorship evidence may not.

Output tiers are:

- `MUST_VISIT`: highest-value visits within a conservative fraction of capacity;
- `IF_TIME`: useful backups within remaining capacity;
- `APPLY_ONLINE`: worthwhile role, but booth time has low incremental value;
- `SKIP`: blocked or currently too weak.

Every low-confidence or evidence-unknown item is surfaced for review.

## Artifacts

- `SKILL.md`: routing and essential workflow.
- `references/data-contracts.md`: candidate, evidence, and judgment shapes.
- `references/jev-judgments.md`: official primitive usage and rubrics.
- `references/research-and-events.md`: source hierarchy and Handshake boundaries.
- `scripts/rank_battle_plan.py`: standard-library deterministic ranker.
- `examples/`: anonymized input and generated deterministic output.
- `tests/`: behavior tests for ranking, capacity, uncertainty, and authorization boundaries.

## Privacy and permissions

The default Jev state uses an approved condensed profile, not the full resume. Protected traits are not scoring inputs. API keys stay in environment variables. Read-only research is allowed; registration, email, applications, and other external mutations require explicit confirmation immediately before execution.

## Validation

Use test-first development for the ranker, the bundled skill validator, static JSON/example checks, and ten independent agent simulations. Simulations cover career switching, adjacent-field moves, uncertain preferences, different schools and fair formats, sponsorship ambiguity, missing Handshake details, and time pressure.
