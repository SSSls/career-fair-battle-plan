# Career Fair Battle Plan v2 Design

Date: 2026-09-25
Status: Approved for implementation on 2026-09-25
Repository: `SSSls/career-fair-battle-plan`

## 1. Objective

Upgrade the existing open-source Codex Skill into an evidence-scoped, cost-aware workflow that can make useful preliminary decisions before event registration, produce a verified fair-day route only when session access is known, and work across Handshake, official university pages, user uploads, visible LinkedIn/job pages, and employer career sites.

The upgrade must preserve the current product goal: optimize limited career-fair time rather than predict whether a candidate will receive an offer.

Success means:

1. A user can provide a CV, goals, constraints, and any available fair source.
2. The Skill proposes a profile and target areas, then waits for explicit approval.
3. Public or incomplete employer-card data can produce a clearly labeled preliminary research priority without fabricating exact-role facts.
4. A time-boxed route is produced only from verified visit access and session timing.
5. Jev is used only for unresolved semantic judgments that survive deterministic prefilters.
6. Every material decision exposes evidence scope, confidence, unknowns, and source references.
7. Live account tests remain visible, read-only, and never register, waitlist, message, apply, upload, or edit without a separate user confirmation immediately before that action.
8. English and Chinese documentation, examples, package ZIP, tests, and GitHub remain synchronized.

## 2. Scope and non-goals

### In scope

- Candidate-profile extraction and approval.
- Public-preview and authenticated-read-only source states.
- Registration state independent from login/access state.
- Official-school, Handshake-visible, user-upload, employer-careers, and visible job-page evidence.
- Preliminary research priority when exact roles or sessions are incomplete.
- Exact-role ranking when sufficient role evidence exists.
- Verified schedule construction when visit access is confirmed.
- Jev request planning, typed response validation, caching metadata, and cost telemetry.
- Fixture-backed and live read-only validation across multiple schools.

### Non-goals

- Password, MFA, CAPTCHA, cookie, or session-token handling.
- Hidden/private endpoint discovery, reverse engineering, or access-control bypass.
- Automatic registration, waitlisting, messaging, applying, following, saving, uploading, or profile editing.
- Treating historical H-1B/PERM records as current exact-role policy.
- Predicting interview or offer probability.
- Shipping a hosted SaaS, browser extension, database, or background crawler in v2.
- Claiming a real Jev call when only fixtures or fallback judgments were used.

## 3. Approaches considered

### A. Minimal policy patch

Add a `PARTIAL` flag and block unknown sessions from the scheduler.

Advantages: small diff and low regression risk.

Rejected as the full solution because it does not provide source adapters, dynamic Jev routing, evidence-scope confidence, multi-school testing, or a reusable no-registration workflow.

### B. Layered v2 inside the existing Skill — selected

Keep the repository as a portable Codex Skill using Python standard-library scripts and focused references. Add separate intake, source normalization, decision readiness, Jev planning, ranking, and scheduling layers.

Advantages: preserves installation simplicity, is auditable, supports fixture testing, and can be incrementally integrated with browser-visible sources.

Trade-off: source adapters produce normalized JSON rather than fully autonomous scraping for every platform.

### C. Hosted service or browser extension

Centralize account integrations, persistence, and scheduling in a web service.

Rejected for v2 because it introduces authentication storage, deployment, platform-policy, privacy, and maintenance requirements that are unnecessary for the current open-source Skill.

## 4. Architecture

The v2 pipeline has seven independent layers:

```text
Candidate intake and approval
        ↓
Access and registration state
        ↓
Source adapters → normalized evidence records
        ↓
Deterministic prefilter
        ↓
Dynamic Jev request plan for survivors
        ↓
Decision readiness + ranking
        ↓
Verified scheduler + action-card generation
```

Each layer accepts and emits JSON so it can be tested without a browser or live Jev service.

### 4.1 Candidate intake

Preserve the existing separation among:

- demonstrated strengths;
- inferred fit areas;
- user-stated preferences;
- pivot areas;
- avoid areas;
- hard constraints.

Ranking remains forbidden until `candidate_profile.approved=true`. Sponsorship, work authorization, salary hard floors, and user preference may never be inferred from nationality, school, major, or prior work.

### 4.2 Access and registration state

Replace the overloaded source/login interpretation with independent fields:

```json
{
  "source_mode": "UPLOAD | PUBLIC_WEB | PUBLIC_PREVIEW | AUTHENTICATED_READ_ONLY",
  "authentication_state": "NOT_REQUIRED | LOGGED_OUT | LOGGED_IN | UNKNOWN",
  "registration_state": "NOT_REQUIRED | NOT_REGISTERED | REGISTERED | UNKNOWN",
  "authorization_scope": "NONE | READ_ONLY",
  "mutation_allowed": false
}
```

Rules:

- `PUBLIC_PREVIEW` may ingest fields that are visibly public, including public Handshake previews.
- Live authenticated Handshake inspection requires `LOGGED_IN` and `READ_ONLY` authorization.
- `NOT_REGISTERED` does not block employer/title research.
- Registration status never grants mutation permission.
- Any registration or other external mutation requires a separate confirmation immediately before execution.

### 4.3 Evidence levels

Every opportunity declares the strongest evidence level reached:

```text
EMPLOYER_NAME
EMPLOYER_CARD
TITLE_ONLY
EXACT_ROLE
SESSION_VERIFIED
```

Evidence records add:

```json
{
  "scope": "event | employer_event_card | company_current | company_history | exact_role | exact_session",
  "field": "role | sponsorship | headcount | salary | eligibility | session",
  "status": "yes | no | unknown",
  "source_quality": "primary | government | reputable_secondary | anecdotal | unverified",
  "source_url": "https://example.edu/source",
  "artifact_reference": null,
  "published_at": null,
  "accessed_at": "YYYY-MM-DD",
  "freshness": "current | stale | unknown"
}
```

Employer-card work-authorization text receives `scope=employer_event_card`. It may affect research priority but cannot create exact-role eligibility or a hard sponsorship rejection.

## 5. Source adapters

Adapters normalize visible or supplied information; they do not bypass access controls.

### 5.1 Official school adapter

Input: public university career-services page.

Output:

- fair name, date, timezone, format, eligible populations;
- event platform and event URL;
- public employer list or featured employers when present;
- whether a login or school affiliation is required for richer data.

### 5.2 Handshake public-preview adapter

Input: visibly public event preview or a user-supplied snapshot/export.

Output:

- employer-card fields;
- visible job titles, school years, job types, work-authorization text;
- advertised session count;
- `session_time=unknown`, `session_availability=unknown`, and `visit_access=unknown` unless visibly confirmed.

### 5.3 Handshake authenticated-read-only adapter

Input: a browser tab where the user has logged in and granted read-only inspection.

Output only fields visible in the UI:

- participating employers and linked roles;
- eligibility filters;
- visible session time, type, status, and availability;
- registration state when visibly shown.

It may not register, waitlist, message, apply, upload, or edit.

### 5.4 External role research adapter

Input: company careers pages, official current job pages, visible public LinkedIn/job pages, and government sponsorship history.

Output:

- exact-role requirements and current posting state;
- role-level sponsorship only when explicitly stated;
- salary only with source type and currency;
- historical sponsorship labeled as history, never current policy;
- active headcount remains `unknown` unless explicitly confirmed.

## 6. Decision states and confidence

The output state is independent from the four final visit tiers:

```text
STOP      A personalized decision is unsafe because profile or hard inputs are unresolved.
PARTIAL   Preliminary research priority is possible, but exact-role or visit evidence is incomplete.
FULL      Exact-role ranking is supported; a route still requires verified visit access.
```

Each opportunity contains:

```json
{
  "decision_state": "STOP | PARTIAL | FULL",
  "evidence_confidence": 0.0,
  "match_confidence": 0.0,
  "visit_access_confidence": 0.0,
  "decision_confidence": 0.0,
  "confidence_caps": [],
  "review_flags": []
}
```

Default confidence caps:

- employer name only: match confidence at most `0.35`;
- title-only: at most `0.59`;
- exact current role with unresolved hard facts: at most `0.79`;
- a verified route requires visit-access confidence at least `0.80`.

The implementation must preserve Jev score/confidence ranges when supplied. Point estimates may rank opportunities, but overlapping or threshold-crossing ranges create a review flag and prevent `MUST_VISIT`.

## 7. Deterministic prefilter and Jev

### 7.1 Prefilter before Jev

Apply verified deterministic facts before requesting semantic judgments:

- explicit user opt-out;
- exact-role no sponsorship when sponsorship is required;
- verified unmet citizenship, clearance, degree, career-stage, or minimum-experience requirement;
- verified unavailable visit channel for the visit-routing branch;
- duplicate or irrelevant role outside approved areas.

Blocked opportunities remain in the audit output with evidence IDs but do not require the full Jev question set.

### 7.2 Dynamic Jev request planning

For each surviving `company × exact-role` or title-level lead, request only relevant atomic questions:

- always: `best_area`, `role_fit`;
- when candidate evidence exists: `evidence_strength`;
- when a usable conversation channel is plausible: `conversation_leverage`;
- when material facts remain unresolved: `information_gain`;
- when career stage is unclear: `entry_level_accessible`;
- for adjacent moves or career changes: `background_pathway_accessible`;
- only when sponsorship is needed and exact-role evidence is unresolved: sponsorship Noul.

Jev output cannot create source evidence. Unknown evidence remains unknown.

### 7.3 Jev integration boundary

The repository will include:

- a deterministic request planner;
- a typed result validator;
- normalized state/question hashing;
- cache-file support outside committed candidate data;
- request, question-count, provider/model, latency, retry, token, and cost telemetry fields when returned by a callable client;
- an explicit `READY_FOR_JEV` state when no client is configured;
- fixture and user-approved fallback modes that cannot be mislabeled as live Jev.

The repository will not embed API keys. Live TypeSafe/Jev connectivity is claimed only after an observed successful call.

## 8. Ranking and scheduling

### 8.1 Preliminary research priority

`PARTIAL` opportunities receive a research order such as:

```text
HIGH_VERIFY_FIRST
MEDIUM_VERIFY
DISCOVERY_ONLY
LOW_DISCOVERY
```

These labels are not `MUST_VISIT`, and they cannot enter the confirmed schedule.

### 8.2 Final tiers

The existing tiers remain for sufficiently supported opportunities:

- `MUST_VISIT`
- `IF_TIME`
- `APPLY_ONLINE`
- `SKIP`

Only verified source evidence creates a hard demotion. Low-confidence or unresolved critical judgments cap an otherwise eligible opportunity at `IF_TIME` or keep it `PARTIAL`.

### 8.3 Scheduler invariant

The scheduler must enforce:

```text
visit_access == verified
AND session time/channel is usable
```

before assigning any route interval.

`visit_access=unknown` produces `CHECK_SESSION` and never receives a fabricated flexible slot. `visit_access=unavailable` routes to `APPLY_ONLINE` when the role remains application-worthy.

The output preserves session status, access status, confidence, evidence scope, and the reason an opportunity was excluded from the route.

## 9. User-facing output

### STOP

- profile draft;
- unresolved hard inputs;
- exact questions required from the user;
- no company ranking.

### PARTIAL

- approved profile version;
- source coverage and limitations;
- preliminary research priority;
- evidence and confidence per lead;
- exact unknowns and verification questions;
- no confirmed fair-day route.

### FULL

- assumptions and remaining unknowns;
- final tiers;
- verified time-boxed route;
- company-role action cards;
- cited reason, short pitch, and bilingual booth questions;
- apply-online and review queues;
- external actions awaiting confirmation.

## 10. Testing strategy

### 10.1 Unit and contract tests

Add failing tests before implementation for these invariants:

1. Public preview is ingestible without event registration.
2. Login state and registration state are independent.
3. `visit_access=unknown` never enters `visit_schedule`.
4. Employer-card sponsorship cannot become an exact-role hard decision.
5. Title-only evidence cannot produce `FULL` or high match confidence.
6. Deterministic hard filters execute without requiring complete Jev scores.
7. Dynamic Jev plans omit irrelevant questions.
8. Choice confidence, Score confidence/ranges, and Noul probabilities are bounded.
9. Cached Jev results require a matching normalized hash.
10. Output preserves evidence scope and session state.

### 10.2 Scenario matrix

Cover at least 30 scenarios across:

- conventional CS, adjacent-field move, major career change, and nontechnical/hybrid candidate;
- domestic, temporary work authorization, future sponsorship needed, and unresolved status;
- public preview, authenticated not registered, registered read-only, upload, incomplete public page, and no fair source;
- exact role, title only, employer only, stale posting, conflicting sources, and incomplete employer coverage;
- virtual, in-person, fixed sessions, flexible booths, full sessions, unknown access, and schedule conflicts;
- salary hard/soft floors, location constraints, clearance/citizenship, and experience gaps;
- live Jev unavailable, fixture Jev, malformed Jev output, cache hit, and retry metadata.

### 10.3 Live read-only validation

With the user's explicit authorization, validate visible fields without any external mutation:

- Penn authenticated Handshake account, if the user is currently logged in;
- Penn public previews already identified;
- at least three other official university career sources representing:
  - public official page with partial employer data;
  - Handshake login wall;
  - publicly visible historical employer directory.

Suggested schools for coverage are Cornell, UC Berkeley, and one additional university selected from a current official source. Results must record access date, login requirement, available fields, missing fields, and whether the adapter produced `STOP`, `PARTIAL`, or `FULL`.

If login is absent or expires, pause for the user to log in; never request credentials or complete MFA.

### 10.4 Behavioral Skill validation

Run independent synthetic personas only when delegation is explicitly authorized. Otherwise execute the scenario matrix locally. Behavioral validation must distinguish fixture judgment quality from real Jev calibration.

## 11. Repository changes

Expected files:

```text
career-fair-battle-plan/
  SKILL.md
  references/
    intake-and-access.md
    research-and-events.md
    data-contracts.md
    decision-states.md
    source-adapters.md
    jev-judgments.md
  scripts/
    assess_intake.py
    normalize_source.py
    plan_jev_requests.py
    validate_jev_results.py
    rank_battle_plan.py
    run_scenario_matrix.py
  examples/
    sample_*.json
    live-source-fixtures/
tests/
  test_intake_and_policy.py
  test_source_normalization.py
  test_jev_planner.py
  test_rank_battle_plan.py
  test_scenario_matrix.py
  fixtures/
README.md
README.zh-CN.md
career-fair-battle-plan.zip
```

No real CV, account data, session cookie, API key, or private event export may enter the repository. Live observations must be converted to minimal, anonymized fixtures or summarized without private data.

## 12. Migration and compatibility

- Existing v1 inputs remain accepted where possible.
- Missing new fields receive conservative defaults: authentication/registration unknown, evidence scope unverified, and decision state no higher than `PARTIAL` when critical data is absent.
- Existing final tiers remain stable for fully evidenced fixtures unless they previously relied on unknown visit access.
- The CLI stays Python 3.10+ and standard-library only.
- Any breaking schema change must produce a clear validation message and be documented in both READMEs.

## 13. Documentation and release

Update English and Chinese documentation together with:

- the distinction among login, registration, read-only access, and mutation;
- public-preview and partial-decision examples;
- Jev setup, live/fixture/fallback provenance, caching, and cost behavior;
- source adapter boundaries;
- privacy rules for live account testing;
- commands for unit tests, scenario matrix, validation, packaging, and installation.

Before the GitHub update:

1. Run the full unit suite.
2. Run the 30+ scenario matrix.
3. Run the Skill structural validator.
4. Rebuild and inspect the ZIP.
5. Confirm the worktree contains no secrets or private user artifacts.
6. Review the complete diff.
7. Commit with a v2-focused message.
8. Push to `origin/main` only after all gates pass.

## 14. Acceptance criteria

The v2 upgrade is complete only when:

- all unit tests and scenario tests pass;
- unknown visit access cannot appear in a confirmed route;
- public/no-registration data produces `PARTIAL`, not a fabricated full battle plan;
- exact-role hard constraints require exact-role evidence;
- blocked opportunities do not require unnecessary Jev judgments;
- Jev provenance and cost metadata are explicit;
- three or more university source patterns have been tested read-only;
- English and Chinese README content is synchronized;
- the packaged ZIP matches the repository Skill;
- no secret, private CV, account data, or session information is committed;
- GitHub `main` contains the verified release commit.
