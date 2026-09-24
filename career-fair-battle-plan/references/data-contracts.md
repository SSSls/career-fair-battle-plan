# Data contracts

Read this reference when creating or validating candidate, evidence, Jev, or ranker artifacts.

## Candidate profile

`inferred_fit_areas` describe evidence-backed fit. `user_stated_preferences` describe desire. Never merge them silently.

```json
{
  "profile_version": "2026-09-23T14:00:00Z",
  "approved": false,
  "education": [],
  "experience": [],
  "projects": [],
  "demonstrated_strengths": [
    {"skill": "Python", "evidence": ["Project A"]}
  ],
  "inferred_fit_areas": [
    {"area": "backend-swe", "evidence": ["API project"], "fit": "strong"}
  ],
  "user_stated_preferences": [],
  "pivot_areas": [],
  "avoid_areas": [],
  "hard_constraints": {
    "needs_sponsorship": null,
    "work_authorization": "unknown",
    "locations": [],
    "graduation_date": "unknown",
    "role_type": [],
    "salary": {"minimum": null, "currency": "USD", "hard_constraint": false},
    "headcount_importance": "medium"
  },
  "open_questions": []
}
```

The ranker accepts `needs_sponsorship` at `candidate_profile.needs_sponsorship` for a compact machine input. Copy it from the approved `hard_constraints` value; do not infer it.
The draft profile may use `null`, but the ranker requires an approved `true` or `false`; resolve it before final ranking.

`headcount_importance` is `low`, `medium`, or `high`. A salary floor blocks a role only when it is marked hard and an official exact-role range in the same currency proves the maximum is below it. Otherwise uncertainty becomes a review flag.

## Evidence record

One record supports one claim. `unknown` is a valid conclusion.

```json
{
  "claim_id": "company-role-sponsorship",
  "claim": "This exact role accepts candidates needing future sponsorship.",
  "status": "unknown",
  "source_url": "https://example.com/job/123",
  "artifact_reference": null,
  "publisher": "Example Company",
  "published_at": null,
  "accessed_at": "2026-09-23",
  "source_quality": "primary",
  "notes": "Role page is silent on sponsorship."
}
```

Allowed `source_quality`: `primary`, `government`, `reputable_secondary`, `anecdotal`, `unverified`.

## Ranker input

Scores use a five-level Jev rubric indexed `0` through `4`. Choice and Score carry confidence; Noul carries only a yes probability.

```json
{
  "candidate_profile": {
    "approved": true,
    "needs_sponsorship": false
  },
  "fair": {
    "duration_minutes": 180,
    "reserve_minutes": 30,
    "minutes_per_visit": 15
  },
  "weights": {
    "role_fit": 0.30,
    "evidence_strength": 0.15,
    "conversation_leverage": 0.25,
    "information_gain": 0.15,
    "user_interest": 0.15
  },
  "opportunities": [
    {
      "company": "Example Co",
      "role": "Software Intern",
      "user_interest": 0.9,
      "evidence_ids": ["example-role", "example-session"],
      "evidence": {
        "explicit_no_sponsorship": false,
        "explicit_disqualifiers": [],
        "eligibility_unknowns": [],
        "sponsorship_status": "unknown",
        "sponsorship": {
          "status": "unknown",
          "scope": "exact_role",
          "evidence_id": "example-role"
        },
        "headcount": {"status": "unknown", "evidence_id": null},
        "salary": {
          "min": null,
          "max": null,
          "currency": "USD",
          "source_type": "unknown",
          "evidence_id": null
        },
        "session_status": "verified",
        "visit_access": "verified",
        "fixed_session": {"start_minute": 30, "end_minute": 45}
      },
      "judgments": {
        "role_fit": {"type": "score", "score": 3.4, "confidence": 0.82},
        "evidence_strength": {"type": "score", "score": 3.0, "confidence": 0.76},
        "conversation_leverage": {"type": "score", "score": 3.5, "confidence": 0.81},
        "information_gain": {"type": "score", "score": 2.5, "confidence": 0.72},
        "best_area": {"type": "choice", "choice": "backend-swe", "confidence": 0.84},
        "entry_level_accessible": {"type": "noul", "noul": 0.88},
        "sponsorship_evidence_supports_eligibility": {"type": "noul", "noul": 0.5}
      }
    }
  ]
}
```

Set `user_interest` to `0` when the approved profile explicitly opts out of this exact role or area; the ranker treats that as `SKIP` even when resume fit is high. Put only verified, exact-role hard failures in `explicit_disqualifiers` (for example, an unmet mandatory citizenship, clearance, degree, or minimum-experience requirement). Put unresolved conditions in `eligibility_unknowns`; they are review flags, not rejections.

`visit_access` describes the usable visit channel after considering booth and session data: `verified`, `unknown`, or `unavailable`. A full 1:1 does not imply `unavailable` when a verified booth or group session remains. Use `fixed_session` only for a verified exclusive time, expressed as minutes from fair start. Overlapping fixed sessions are resolved by score and the lower opportunity is routed to `APPLY_ONLINE` with a conflict flag.

Every opportunity lists the `claim_id` values it uses in `evidence_ids`. Keep the full evidence records alongside the ranker input so the output can be traced back to sources.

Structured evidence IDs are also validated against `evidence_records`. Definite sponsorship or HC claims and any non-unknown salary source require an evidence ID. Sponsorship `scope` is `exact_role`, `company_current`, or `company_history`; only an exact-role `no` is a sponsorship hard stop. Headcount status is `confirmed`, `likely`, or `unknown`; only explicit `confirmed` evidence counts as confirmed HC. Salary `source_type` is `official_exact_role`, `official_company`, `secondary`, or `unknown`.

## Company-role action card

Each card contains:

- company, exact role, tier, visit score, and best approved area;
- one-line reason tied to evidence identifiers;
- gaps and review flags;
- a 20–30 second pitch grounded in candidate evidence;
- 2–3 English questions, each followed by a Chinese translation;
- session status: `verified`, `unverified`, `full`, or `unknown`;
- proposed external action and whether confirmation is required.
