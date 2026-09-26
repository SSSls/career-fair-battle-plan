---
name: career-fair-battle-plan
description: Use when a job seeker needs to prioritize employers, exact roles, sessions, or career-fair conversations under limited time, including career changes, adjacent moves, sponsorship constraints, public previews, and authenticated read-only fair sources.
---

# Career Fair Battle Plan

Optimize scarce fair time, not generic application worthiness. Keep facts, model judgments, and deterministic policy separate.

## Route the workflow

1. Read [references/intake-and-access.md](references/intake-and-access.md). Collect CV/background, school, goals, work authorization, sponsorship need, location/salary constraints, and fair source. Run `assess_intake.py`.
2. Build the candidate contract in [references/data-contracts.md](references/data-contracts.md). Separate demonstrated fit, stated preference, pivot areas, and avoid areas. Never infer preferences or eligibility from school, major, nationality, or career-change status.
3. **Stop for profile approval.** Show the profile and proposed area set. Do not ingest, research, call Jev, or rank until `approved` is explicitly true.
4. Read [references/source-adapters.md](references/source-adapters.md) and [references/research-and-events.md](references/research-and-events.md). Normalize only visible or supplied data. Use `company × exact role` when available; weaker employer cards remain preliminary leads.
5. Read [references/decision-states.md](references/decision-states.md). Preserve `STOP`, `PARTIAL`, or `FULL`, independent confidence fields, and every cap/review flag. Unknown access is never schedulable.
6. Apply deterministic hard filters before semantic evaluation. Exact-role ineligibility, explicit opt-out, duplicates, and unavailable visit routes do not need Jev.
7. For surviving questions, read [references/jev-judgments.md](references/jev-judgments.md). Use `plan_jev_requests.py`, send only the approved condensed state, validate every result with `validate_jev_results.py`, and label provenance `live`, `fixture`, `fallback`, or `cache`. Never claim Jev ran unless a validated live result proves it.
8. Run `rank_battle_plan.py`. Do not override hard reasons, confidence gates, capacity, or conflicts in prose; change inputs/config and rerun.
9. Produce a fair-day plan: cited reason, exact role/area, short pitch, bilingual questions, review flags, `MUST_VISIT`, `IF_TIME`, `APPLY_ONLINE`, `SKIP`, and only verified route slots.

## Permission boundary

The user enters credentials and completes MFA/CAPTCHAs. Read-only authorization covers visible inspection only. Never use hidden endpoints or store credentials. Registration, waitlists, messages, applications, uploads, saves, follows, emails, and profile edits require separate confirmation immediately before execution. A public preview may support preliminary matching without registration; it does not prove full employer coverage, exact jobs, or session availability.

## Output order

Approved profile version; source/access state; assumptions and unknowns; decision state and confidence; preliminary priorities or final tiers; verified route; company-role action cards; review queue; sources; actions requiring confirmation.
