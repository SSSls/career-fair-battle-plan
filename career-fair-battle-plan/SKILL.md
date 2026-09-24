---
name: career-fair-battle-plan
description: Use when a job seeker needs to prioritize employers, roles, Handshake events, virtual sessions, or career-fair conversations under limited time, especially across career changes, adjacent-field moves, sponsorship constraints, or uncertain target areas.
---

# Career Fair Battle Plan

## Core principle

Optimize scarce fair time, not generic application worthiness. Keep three layers separate: an LLM understands and writes, Jev makes atomic typed judgments, and code applies weights, hard rules, capacity, and permissions.

## Workflow

1. **Run intake and access gating.** Follow [references/intake-and-access.md](references/intake-and-access.md). Collect the CV/background, school, goals, constraints, and fair metadata; run `assess_intake.py`. Any live Handshake fetch requires user login plus read-only authorization, even if a page appears public. Uploaded exports do not.
2. **Build the candidate profile.** Produce the contract in [references/data-contracts.md](references/data-contracts.md). Keep demonstrated fit separate from stated preference: prior work does not prove the user wants more of it. Do not stereotype from school, degree, major, nationality, or career-change status.
3. **Checkpoint.** Show `candidate_profile` and the proposed area set. If `approved` is not explicitly true, stop and ask the user to correct or approve it. Do not research, judge, or rank yet.
4. **Ingest the fair.** For Handshake and other event sources, follow [references/research-and-events.md](references/research-and-events.md). The unit of analysis is `company × role`, not company alone. Apply obvious eligibility and relevance filters before deep research.
5. **Build evidence records.** Every material claim carries a URL or supplied-artifact reference, publisher, publication date when available, access date, and `yes | no | unknown`. Distinguish exact-role sponsorship from company history, confirmed HC from a mere job page, and official exact-role salary from secondary estimates.
6. **Ask Jev atomic questions.** Read [references/jev-judgments.md](references/jev-judgments.md). Send an approved condensed profile, top relevant roles, and evidence—not the full resume. Batch independent questions sharing a state in one `system_one` call. Record the provider and model. If Jev is unavailable, never imply it ran; return `READY_FOR_JEV`, or use a clearly labeled fallback only after the user agrees.
7. **Rank in code.** Create the JSON input from the contract and run:

   ```bash
   python3 scripts/rank_battle_plan.py input.json -o battle_plan.json
   ```

   Do not override its hard demotions, capacity, uncertainty flags, or tiers by prose intuition. Adjust weights/configuration and rerun instead.
8. **Generate the battle plan.** For `MUST_VISIT` and `IF_TIME`, provide cited reasons, the matched role/area, a short pitch, 2–3 tailored booth questions in English and Chinese, and verified session actions. Include `APPLY_ONLINE`, `SKIP`, review flags, and a time-feasible visit order.

## Permission boundary

The user must log in themselves. Never request passwords, handle MFA/CAPTCHAs, bypass authentication, or inspect hidden private endpoints. Authenticated access is visible and read-only. Registration, waitlists, email, messages, applications, uploads, or profile edits require explicit confirmation immediately before execution. Never fabricate booth times, available slots, recruiter names, hiring claims, or completed actions.

## Output contract

Return these sections in order: approved profile version; assumptions and unknowns; tier summary; time-boxed route; company-role action cards; `APPLY_ONLINE`; review queue; sources; next actions requiring confirmation.
