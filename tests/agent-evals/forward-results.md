# Agent forward-test results

Date: 2026-09-23

Ten independent agents were spawned in total: three RED baselines without the skill and seven GREEN/REFACTOR agents with the skill. Because the runtime permits four active agents including the controller, simulations ran in batches. Replay inputs and exact machine-relevant outcomes are in `runbook.md`; the harness did not expose resolved child model/effort metadata, so bit-for-bit reproduction is not claimed.

## GREEN checkpoint scenarios

Three agents received unapproved profiles:

1. English/publishing to information systems, considering analytics/product operations/software.
2. Economics to analytics/product/fintech/data science with unresolved preferences.
3. Conventional CS candidate targeting backend/infrastructure while excluding defense and ad-tech.

All three produced distinct `inferred_fit_areas` and `user_stated_preferences`, marked the profile unapproved, surfaced missing constraints, and stopped before company research or ranking.

## Full-pipeline scenarios

1. Mechanical engineering to robotics/embedded/controls.
2. Biology-to-CS international candidate needing sponsorship.
3. Community-college transfer targeting cyber/cloud/IT automation.
4. MBA/supply-chain candidate using an incomplete Handshake export without Jev access.

Observed passes:

- unknown and case-by-case sponsorship stayed unresolved rather than becoming rejection;
- exact no-sponsorship evidence triggered a hard demotion only when sponsorship was needed;
- missing citizenship was surfaced for review instead of guessed;
- no agent fabricated session times, availability, evidence, or a live Jev call;
- the Handshake/no-Jev agent returned `READY_FOR_JEV` and refused an unsupported final rank;
- no agent registered, messaged, emailed, or applied without confirmation;
- complete scenarios used the real deterministic ranker and preserved its results.

## Failures found and refactored

### Explicit user opt-out

Initial full runs placed a pure manufacturing role and a pure lab role into `IF_TIME` or `APPLY_ONLINE` because resume fit was high despite `user_interest=0`.

Fix: `user_interest=0` now deterministically yields `SKIP` with reason `user_opt_out`. A new unit test first reproduced the failure. The robotics agent then reran the scenario and confirmed FactoryMax became `SKIP`.

### General hard disqualifiers

An exact role requiring five years of experience initially remained `IF_TIME` because only sponsorship had a dedicated hard rule.

Fix: evidence now supports `explicit_disqualifiers` and `eligibility_unknowns`. Verified unmet mandatory requirements yield `SKIP`; unresolved conditions become review flags. A failing unit test preceded the implementation. The transfer agent reran the scenario and confirmed SeniorSec became `SKIP` while unknown GovSecure citizenship remained a review flag.

## Remaining limits

- Live TypeSafe/Jev connectivity was not tested because no API credential was supplied.
- No authenticated Handshake session or real event export was provided, so the ingestion policy was behaviorally tested with fixtures rather than a live account.
- The skill is ready for fixture-backed and deterministic use; a real fair run should be the next integration test.
