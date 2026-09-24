# Baseline agent results (without the skill)

Date: 2026-09-23

## Scenarios

1. International biology-to-CS career switcher at a three-hour virtual fair.
2. Mechanical-engineering student moving into robotics/embedded/controls at a two-hour in-person fair.
3. Sophomore at a regional university exploring frontend, SWE, cybersecurity, and product-adjacent work from an incomplete Handshake export.

## Observed baseline behavior

All three agents produced plausible prose rankings and useful pitches. None produced a reusable approved profile, typed evidence records, atomic judgments, or deterministic inputs that another run could reproduce.

Recurring failures:

- proceeded directly to ranking instead of stopping for candidate-profile correction;
- mixed sourced facts, assumptions, and model judgments in the same rationale;
- did not attach dates, source quality, or explicit `unknown` states to hiring and sponsorship claims;
- treated schedules as prose assumptions instead of verified constraints;
- did not expose a separate low-confidence review queue;
- used company-level rankings even though future inputs may contain several roles per employer;
- could recommend registration or follow-up without a structured confirmation boundary;
- did not calculate tier capacity from fair duration and visit cost;
- had no machine-readable artifact for changing weights without repeating model work.

These failures define the minimum behavior the skill must add. The skill should preserve the baseline agents' useful tailored positioning and questions while making the decision path auditable and repeatable.
