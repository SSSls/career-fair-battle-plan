# Decision states and confidence

Read this reference before turning source data into a priority or route.

## STOP / PARTIAL / FULL

- `STOP`: a required control is unresolved, such as profile approval, sponsorship need, login, or read-only authorization. Do not research or rank past that boundary.
- `PARTIAL`: useful evidence exists, but it cannot support a final route. Return preliminary priorities such as `HIGH_VERIFY_FIRST`, `MEDIUM_VERIFY`, `DISCOVERY_ONLY`, or `LOW_DISCOVERY` and list what must be verified.
- `FULL`: exact-role evidence is sufficient for scoring. A time slot is still allowed only when session/booth access is verified independently.

Never infer a stronger state from polished prose. `EMPLOYER_NAME`, `EMPLOYER_CARD`, and `TITLE_ONLY` cap match confidence at `0.35`, `0.49`, and `0.59`. Unresolved exact-role hard facts cap it at `0.79`. A verified route requires `SESSION_VERIFIED`, `visit_access=verified`, and `visit_access_confidence >= 0.80`.

## Independent confidence fields

Keep these values separate:

- `evidence_confidence`: strength and scope of the observed source;
- `match_confidence`: confidence in candidate-role fit after evidence-level caps;
- `visit_access_confidence`: confidence that a usable booth/session route exists;
- `decision_confidence`: the lower of evidence and match confidence;
- `route_ready`: deterministic boolean; confidence alone cannot make it true.

Surface `confidence_caps` and `review_flags`. Missing sponsorship, salary, headcount, role, or session facts remain unknown.

## Deterministic order

1. Stop for unapproved profile or unresolved sponsorship need.
2. Deduplicate opportunities.
3. Apply explicit opt-outs and exact-role hard failures.
4. Mark unavailable visit routes `APPLY_ONLINE` when otherwise relevant.
5. Use Jev only for surviving semantic questions.
6. Apply final weights, uncertainty caps, capacity, and fixed-session conflict handling.
7. Schedule only verified access. Unknown access yields `CHECK_SESSION`, never an invented appointment.
