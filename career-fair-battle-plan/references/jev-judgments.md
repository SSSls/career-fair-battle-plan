# Jev judgments

Read this reference before building or interpreting a Jev request. Recheck the live official documentation before integration because the API is evolving:

- https://docs.typesafe.ai/introduction/quickstart
- https://docs.typesafe.ai/primitives
- https://docs.typesafe.ai/confidence
- https://docs.typesafe.ai/patterns/composite-scoring

## State

Use a structured object containing:

- `candidate`: approved condensed strengths, areas, goals, and relevant constraints;
- `opportunity`: company plus one exact role;
- `evidence`: compact claims with statuses and source quality.

Exclude name, contact information, street address, photo, age, gender, race, and other protected or irrelevant traits. Do not paste the full resume.

## Jev-first cost control

“Jev-first” means Jev is the default semantic judge after cheap deterministic work—not that every row receives a model call. First remove duplicates, explicit opt-outs, exact-role hard failures, and unavailable routes. Then run `plan_jev_requests.py`; it asks only questions whose answers are still needed. Blocked opportunities return `NOT_NEEDED` and incur no Jev cost.

This repository does not embed a Jev client or API key. A planned request is `READY_FOR_JEV`, not evidence that a call happened.

## One request, atomic questions

Build `best_area.criteria` dynamically from the approved union of inferred fit, stated preferences, and pivots, excluding avoided areas. Add `other`.

```json
{
  "model": "jev-latest",
  "state": {},
  "questions": {
    "best_area": {
      "type": "choice",
      "instructions": "Which approved candidate area best matches `opportunity` given `candidate` and `evidence`?",
      "criteria": {
        "backend-swe": "The approved backend software area.",
        "other": "No supplied area is a good match."
      }
    },
    "role_fit": {
      "type": "score",
      "instructions": "How directly does documented candidate capability match the role's core work?",
      "criteria": [
        "No relevant capability evidence.",
        "Only distant transferable evidence.",
        "Plausible partial match with material gaps.",
        "Strong match to most core work.",
        "Direct demonstrated match to the core work."
      ]
    },
    "evidence_strength": {
      "type": "score",
      "instructions": "How strong is the resume evidence supporting this match?",
      "criteria": [
        "No supporting evidence.",
        "Only coursework or an unsupported claim.",
        "One relevant but limited example.",
        "Multiple concrete relevant examples.",
        "Repeated relevant results with clear ownership and outcomes."
      ]
    },
    "conversation_leverage": {
      "type": "score",
      "instructions": "How much can a 15-minute fair conversation improve this candidate's outcome beyond applying online?",
      "criteria": [
        "No plausible incremental value.",
        "Mostly information available online.",
        "Some useful clarification or routing value.",
        "Strong opportunity to explain fit or resolve a material question.",
        "Conversation is unusually important to unlock or differentiate the candidacy."
      ]
    },
    "information_gain": {
      "type": "score",
      "instructions": "How much important unresolved information can this conversation realistically provide?",
      "criteria": [
        "No meaningful unresolved question.",
        "Minor questions only.",
        "One useful unresolved question.",
        "Several material questions affect the decision.",
        "The opportunity cannot be evaluated responsibly without direct clarification."
      ]
    },
    "entry_level_accessible": {
      "type": "noul",
      "instructions": "Does `evidence` support that this exact role is accessible at the candidate's documented career stage?"
    },
    "background_pathway_accessible": {
      "type": "noul",
      "instructions": "Do the explicit requirements allow the candidate to qualify through documented transferable skills rather than an assumed school or major stereotype?"
    },
    "sponsorship_evidence_supports_eligibility": {
      "type": "noul",
      "instructions": "Does current role-specific evidence support eligibility for a candidate who needs sponsorship?"
    }
  }
}
```

Ask the sponsorship question in the same request if convenient, but ignore it in code when sponsorship is not needed.

## Interpretation

- Choice/Score: flag `confidence < 0.60` for human review by default.
- Noul: flag `0.35 <= noul <= 0.65` as uncertain and values below `0.35` as confident negative judgments; Noul has no separate confidence.
- A critical low-confidence or negative judgment cannot produce `MUST_VISIT`; the ranker caps it at `IF_TIME` pending review. Only verified source evidence can create a hard disqualifier.
- The model's probability is not source evidence. Preserve the underlying fact as `unknown` when sources are silent.
- Never ask Jev for the final tier or a composite visit score. Run the deterministic ranker.

Record `provider`, resolved model version, request timestamp, and a hash of normalized state plus questions so results can be cached and audited.

## Validation, provenance, and cache

Run every response through `validate_jev_results.py`. `provenance` is mandatory and must be `live`, `fixture`, `fallback`, or `cache`. Only `live` may claim a provider/model; fixture and fallback must not. A cache hit must match the canonical SHA-256 request hash and be no older than seven days. Keep cache artifacts outside the Skill package (for example `.cache/career-fair-battle-plan/jev/`) and never commit CV data, credentials, or session content.

Record request/question counts, latency, retries, input/output tokens, and cost when available. A fallback is a labeled degraded mode, not Jev.
