# Career Fair Battle Plan v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the Skill so prior CV/fair inputs and new public, uploaded, or authenticated read-only sources produce evidence-scoped preliminary decisions, cost-aware Jev requests, and a route only when visit access is verified.

**Architecture:** Keep the project dependency-free and JSON-first. Separate intake/access policy, source normalization, decision readiness, deterministic prefiltering, Jev request planning/validation, ranking, and scheduling. Preserve v1 inputs through conservative migration defaults, and replay anonymized versions of all prior scenarios after every affected layer is complete.

**Tech Stack:** Python 3.10+ standard library, JSON, Markdown, `unittest`, Codex Skill validator, browser-visible read-only source inspection, TypeSafe/Jev-compatible typed request and response contracts.

**Spec:** `docs/superpowers/specs/2026-09-25-career-fair-battle-plan-v2-design.md`

## Global Constraints

- Candidate ranking is forbidden until `candidate_profile.approved` is exactly `true`.
- Authentication, fair registration, read-only authorization, and mutation permission are independent states.
- Account inspection is visible and read-only. Never request, store, or transmit passwords, MFA codes, CAPTCHA answers, cookies, tokens, or private session material.
- Never register, waitlist, message, apply, follow, save, upload, or edit without a separate confirmation immediately before that action.
- Public previews and user uploads may support `PARTIAL`; they may not fabricate exact-role eligibility or a confirmed route.
- Employer-card and historical sponsorship evidence may guide research but cannot create an exact-role hard rejection or hard positive.
- Deterministic hard filters run before Jev planning. Filtered opportunities remain auditable and do not consume a full Jev question set.
- Jev outputs are judgments, not evidence. They cannot change an unknown source fact to known.
- Fixture, fallback, cache, and live Jev provenance must remain distinguishable.
- `visit_access != "verified"` can never receive a route interval.
- Python remains standard-library only. No API keys, real CVs, account exports, private event data, or browsing session data enter Git.
- English and Chinese documentation must describe the same commands, states, guarantees, and limitations.

## Review Focus

- Contradictory access combinations must fail clearly rather than being silently coerced.
- Partial employer coverage, such as 6 visible cards out of 11 advertised employers, must remain explicit and must not be described as the full fair.
- Title-only or employer-card work-authorization text must not become exact-role sponsorship evidence.
- Unknown session access must yield `CHECK_SESSION`, never an invented flexible slot.
- Stale, malformed, or hash-mismatched Jev cache data must not be accepted as a current live result.

## Target File Map

```text
career-fair-battle-plan/
  SKILL.md
  agents/openai.yaml
  references/
    data-contracts.md
    decision-states.md
    intake-and-access.md
    jev-judgments.md
    research-and-events.md
    source-adapters.md
  scripts/
    assess_intake.py
    decision_readiness.py
    normalize_source.py
    plan_jev_requests.py
    rank_battle_plan.py
    run_scenario_matrix.py
    validate_jev_results.py
  examples/
    sample_input.json
    sample_output.json
    scenario_matrix.json
    scenario_matrix_results.json
    live-source-fixtures/
      handshake-public-preview.json
      official-public-partial.json
      official-login-wall.json
      historical-public-directory.json
tests/
  fixtures/
    regression-domestic-public-preview.json
    regression-sponsor-public-preview.json
    regression-high-evidence.json
    regression-transition-sponsor.json
    regression-sparse-ambiguous.json
    regression-jev-baseline.json
  test_intake_and_policy.py
  test_jev_planner.py
  test_rank_battle_plan.py
  test_readme_installation.py
  test_source_normalization.py
  test_scenario_matrix.py
docs/validation/
  2026-09-25-live-read-only-sources.md
README.md
README.zh-CN.md
career-fair-battle-plan.zip
```

---

### Task 1: Freeze the current baseline and anonymize prior inputs

**Files:**
- Create: `tests/fixtures/regression-domestic-public-preview.json`
- Create: `tests/fixtures/regression-sponsor-public-preview.json`
- Create: `tests/fixtures/regression-high-evidence.json`
- Create: `tests/fixtures/regression-transition-sponsor.json`
- Create: `tests/fixtures/regression-sparse-ambiguous.json`
- Create: `tests/fixtures/regression-jev-baseline.json`
- Modify: `tests/test_scenario_matrix.py`

**Prior local inputs to replay, never copy verbatim if they contain identifying or private data:**

```text
/private/tmp/penn-no-registration-source.json
/private/tmp/cfbp-no-register-domestic/
/private/tmp/cfbp-no-register-sponsor/
/private/tmp/cfbp-eval-high-evidence/
/private/tmp/cfbp-eval-transition-sponsor/
/private/tmp/cfbp-eval-sparse-ambiguous/
/private/tmp/career-fair-jev-baseline-20260924/
```

- [ ] Run the unmodified baseline suite.

Run: `python3 -m unittest discover -s tests -v`

Expected: all current v1 tests pass; record the exact count in the implementation log without claiming v2 correctness.

- [ ] Create the six committed regression fixtures by retaining only synthetic candidate fields, source scope, normalized evidence, judgments, and expected state. Replace real account paths, private URLs, names, and identifiers with `fixtures.invalid` or generic labels.

Each fixture must contain this metadata:

```json
{
  "fixture_metadata": {
    "synthetic_candidate": true,
    "contains_private_account_data": false,
    "real_jev_called": false,
    "derived_from_prior_local_test": true
  }
}
```

- [ ] Add a test that enumerates the six fixture names and asserts their privacy/provenance flags.

```python
REGRESSION_FIXTURES = (
    "regression-domestic-public-preview.json",
    "regression-sponsor-public-preview.json",
    "regression-high-evidence.json",
    "regression-transition-sponsor.json",
    "regression-sparse-ambiguous.json",
    "regression-jev-baseline.json",
)

def test_prior_regression_fixtures_are_synthetic_and_private_free(self):
    for name in REGRESSION_FIXTURES:
        payload = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
        metadata = payload["fixture_metadata"]
        self.assertTrue(metadata["synthetic_candidate"])
        self.assertFalse(metadata["contains_private_account_data"])
        self.assertFalse(metadata["real_jev_called"])
```

- [ ] Run the focused test.

Run: `python3 -m unittest tests.test_scenario_matrix -v`

Expected: existing matrix test plus the fixture privacy test pass.

- [ ] Commit.

```bash
git add tests/fixtures tests/test_scenario_matrix.py
git commit -m "test: preserve anonymized v1 regression inputs"
```

---

### Task 2: Separate source, authentication, registration, and authorization states

**Files:**
- Modify: `career-fair-battle-plan/scripts/assess_intake.py`
- Modify: `tests/test_intake_and_policy.py`

**Interface:**

```python
def assess_intake(document: dict[str, Any]) -> dict[str, Any]:
    """Return access_state, decision_state, permitted actions, and missing fields."""
```

- [ ] Replace the old Handshake-public test with failing tests for public preview and independent registration.

```python
def test_public_handshake_preview_does_not_require_login_or_registration(self):
    intake = load_module("assess_public_preview", INTAKE_SCRIPT)
    payload = complete_intake("PUBLIC_PREVIEW")
    payload["fair"]["platform"] = "handshake"
    payload["access"].update({
        "authentication_state": "LOGGED_OUT",
        "registration_state": "NOT_REGISTERED",
        "authorization_scope": "NONE",
        "mutation_allowed": False,
    })

    result = intake.assess_intake(payload)

    self.assertEqual(result["state"], "READY_FOR_INGESTION")
    self.assertEqual(result["decision_state"], "PARTIAL")
    self.assertEqual(result["access_state"]["registration_state"], "NOT_REGISTERED")

def test_authenticated_and_not_registered_is_valid_read_only_state(self):
    intake = load_module("assess_auth_no_registration", INTAKE_SCRIPT)
    payload = complete_intake("AUTHENTICATED_READ_ONLY")
    payload["access"].update({
        "authentication_state": "LOGGED_IN",
        "registration_state": "NOT_REGISTERED",
        "authorization_scope": "READ_ONLY",
        "mutation_allowed": False,
    })

    result = intake.assess_intake(payload)

    self.assertEqual(result["state"], "READY_FOR_INGESTION")
    self.assertEqual(result["access_state"]["registration_state"], "NOT_REGISTERED")
```

- [ ] Add malformed/contradictory-state tests.

```python
def test_read_only_authorization_rejects_mutation_permission(self):
    payload = complete_intake("AUTHENTICATED_READ_ONLY")
    payload["access"].update({
        "authentication_state": "LOGGED_IN",
        "registration_state": "REGISTERED",
        "authorization_scope": "READ_ONLY",
        "mutation_allowed": True,
    })
    with self.assertRaisesRegex(ValueError, "mutation_allowed"):
        load_module("assess_mutation", INTAKE_SCRIPT).assess_intake(payload)
```

- [ ] Run the tests and confirm they fail because `PUBLIC_PREVIEW` and the new state fields are unsupported.

Run: `python3 -m unittest tests.test_intake_and_policy.IntakeGateTests -v`

Expected: new tests fail before implementation.

- [ ] Implement strict enums and v1 migration in `assess_intake.py`.

```python
SOURCE_MODES = {"UPLOAD", "PUBLIC_WEB", "PUBLIC_PREVIEW", "AUTHENTICATED_READ_ONLY"}
AUTHENTICATION_STATES = {"NOT_REQUIRED", "LOGGED_OUT", "LOGGED_IN", "UNKNOWN"}
REGISTRATION_STATES = {"NOT_REQUIRED", "NOT_REGISTERED", "REGISTERED", "UNKNOWN"}
AUTHORIZATION_SCOPES = {"NONE", "READ_ONLY"}

def _normalized_access(source_mode: str, access: dict[str, Any]) -> dict[str, Any]:
    legacy_logged_in = access.get("user_logged_in")
    authentication_state = access.get("authentication_state")
    if authentication_state is None:
        authentication_state = (
            "LOGGED_IN" if legacy_logged_in is True
            else "LOGGED_OUT" if legacy_logged_in is False
            else "UNKNOWN"
        )
    registration_state = access.get("registration_state", "UNKNOWN")
    legacy_scope = access.get("authorization_scope")
    authorization_scope = "READ_ONLY" if legacy_scope == "read_only" else legacy_scope or "NONE"
    mutation_allowed = access.get("mutation_allowed", False)
    if mutation_allowed is not False:
        raise ValueError("access.mutation_allowed must be false for this read-only skill")
    return {
        "source_mode": source_mode,
        "authentication_state": authentication_state,
        "registration_state": registration_state,
        "authorization_scope": authorization_scope,
        "mutation_allowed": False,
    }
```

- [ ] Return `decision_state="STOP"` for unresolved profile/hard inputs and `PARTIAL` for ingestible incomplete/public-preview inputs. Do not infer `FULL` at intake.

- [ ] Run focused and full tests.

Run: `python3 -m unittest tests.test_intake_and_policy -v`

Expected: all intake and existing policy tests pass.

Run: `python3 -m unittest discover -s tests -v`

Expected: all tests pass.

- [ ] Commit.

```bash
git add career-fair-battle-plan/scripts/assess_intake.py tests/test_intake_and_policy.py
git commit -m "feat: model independent access and registration states"
```

---

### Task 3: Normalize multi-source evidence without promoting its scope

**Files:**
- Create: `career-fair-battle-plan/scripts/normalize_source.py`
- Create: `tests/test_source_normalization.py`
- Create: `career-fair-battle-plan/examples/live-source-fixtures/handshake-public-preview.json`
- Create: `career-fair-battle-plan/examples/live-source-fixtures/official-public-partial.json`
- Create: `career-fair-battle-plan/examples/live-source-fixtures/official-login-wall.json`
- Create: `career-fair-battle-plan/examples/live-source-fixtures/historical-public-directory.json`

**Interfaces:**

```python
def normalize_source(document: dict[str, Any]) -> dict[str, Any]:
    """Normalize a visible/uploaded source into fair coverage, leads, and evidence records."""

def strongest_evidence_level(records: list[dict[str, Any]]) -> str:
    """Return EMPLOYER_NAME, EMPLOYER_CARD, TITLE_ONLY, EXACT_ROLE, or SESSION_VERIFIED."""
```

- [ ] Write failing tests for public-preview normalization and incomplete coverage.

```python
def test_public_preview_preserves_partial_coverage_and_unknown_session(self):
    payload = {
        "adapter": "handshake_public_preview",
        "accessed_at": "2026-09-25",
        "advertised_employer_count": 11,
        "employers": [{
            "name": "Example Trading",
            "job_titles": ["Software Intern"],
            "work_authorization_text": "Employer is willing to sponsor candidates",
            "session_count": 1,
        }],
    }
    result = load_normalizer().normalize_source(payload)
    lead = result["leads"][0]
    sponsor = next(r for r in result["evidence_records"] if r["field"] == "sponsorship")
    self.assertEqual(result["coverage"], {"visible": 1, "advertised": 11, "complete": False})
    self.assertEqual(lead["evidence_level"], "TITLE_ONLY")
    self.assertEqual(lead["visit_access"], "unknown")
    self.assertEqual(sponsor["scope"], "employer_event_card")
```

- [ ] Add tests for official public partial pages, login walls, historical directories, duplicate evidence IDs, invalid dates, and unsupported adapters.

- [ ] Run the focused tests and confirm the module is missing.

Run: `python3 -m unittest tests.test_source_normalization -v`

Expected: import/file-not-found failure before implementation.

- [ ] Implement adapter dispatch with common evidence validation.

```python
ADAPTERS = {
    "handshake_public_preview": _normalize_handshake_public_preview,
    "official_school": _normalize_official_school,
    "handshake_authenticated_read_only": _normalize_handshake_authenticated,
    "external_role_research": _normalize_external_role,
}

EVIDENCE_LEVELS = {
    "EMPLOYER_NAME": 0,
    "EMPLOYER_CARD": 1,
    "TITLE_ONLY": 2,
    "EXACT_ROLE": 3,
    "SESSION_VERIFIED": 4,
}

def normalize_source(document: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(document, dict):
        raise ValueError("source input must be a JSON object")
    adapter = document.get("adapter")
    if adapter not in ADAPTERS:
        raise ValueError(f"unsupported source adapter: {adapter}")
    return ADAPTERS[adapter](document)
```

- [ ] Ensure every evidence record contains `scope`, `field`, `status`, `source_quality`, `source_url` or `artifact_reference`, `published_at`, `accessed_at`, and `freshness`.

- [ ] Make exact session evidence the only normalization path to `visit_access="verified"`.

- [ ] Run focused and full tests.

Run: `python3 -m unittest tests.test_source_normalization -v`

Expected: all normalization tests pass.

Run: `python3 -m unittest discover -s tests -v`

Expected: all tests pass.

- [ ] Commit.

```bash
git add career-fair-battle-plan/scripts/normalize_source.py career-fair-battle-plan/examples/live-source-fixtures tests/test_source_normalization.py
git commit -m "feat: normalize scoped career fair evidence"
```

---

### Task 4: Add decision readiness and confidence caps

**Files:**
- Create: `career-fair-battle-plan/scripts/decision_readiness.py`
- Modify: `tests/test_source_normalization.py`

**Interface:**

```python
def build_decision_readiness(
    opportunity: dict[str, Any],
    candidate_profile: dict[str, Any],
) -> dict[str, Any]:
    """Return decision state, four confidence values, caps, and review flags."""
```

- [ ] Write failing tests for evidence-level caps and unresolved profile state.

```python
def test_title_only_cannot_be_full_or_high_confidence(self):
    readiness = load_readiness().build_decision_readiness(
        {
            "evidence_level": "TITLE_ONLY",
            "visit_access": "unknown",
            "evidence_records": [],
            "judgments": {"role_fit": {"type": "score", "score": 4, "confidence": 0.99}},
        },
        {"approved": True, "needs_sponsorship": False},
    )
    self.assertEqual(readiness["decision_state"], "PARTIAL")
    self.assertLessEqual(readiness["match_confidence"], 0.59)
    self.assertIn("title_only_cap", readiness["confidence_caps"])
```

- [ ] Add coverage for employer-name cap `0.35`, exact-role unresolved-hard-fact cap `0.79`, route threshold `0.80`, overlapping score ranges, and `STOP` when profile approval or sponsorship need is unresolved.

- [ ] Run and confirm missing-module failure.

Run: `python3 -m unittest tests.test_source_normalization.DecisionReadinessTests -v`

Expected: failure before implementation.

- [ ] Implement named constants and the result contract.

```python
MATCH_CONFIDENCE_CAPS = {
    "EMPLOYER_NAME": 0.35,
    "EMPLOYER_CARD": 0.49,
    "TITLE_ONLY": 0.59,
    "EXACT_ROLE": 1.0,
    "SESSION_VERIFIED": 1.0,
}
VERIFIED_ROUTE_CONFIDENCE = 0.80

def build_decision_readiness(opportunity, candidate_profile):
    if candidate_profile.get("approved") is not True:
        return _stop("candidate_profile_not_approved")
    if not isinstance(candidate_profile.get("needs_sponsorship"), bool):
        return _stop("needs_sponsorship_unresolved")
```

- [ ] Implement `_stop(reason)` as a complete STOP result with four zero confidences. Compute evidence, match, and access confidence independently, apply the named cap for the strongest evidence level, and keep `decision_confidence` as the minimum of the confidences required for that decision branch rather than their average.

- [ ] Run focused and full tests, then commit.

```bash
python3 -m unittest tests.test_source_normalization -v
python3 -m unittest discover -s tests -v
git add career-fair-battle-plan/scripts/decision_readiness.py tests/test_source_normalization.py
git commit -m "feat: add scoped decision readiness"
```

---

### Task 5: Move hard filters before Jev and preserve auditable blocked leads

**Files:**
- Modify: `career-fair-battle-plan/scripts/rank_battle_plan.py`
- Modify: `tests/test_rank_battle_plan.py`

**Interfaces:**

```python
def prefilter_opportunity(
    opportunity: dict[str, Any],
    candidate_profile: dict[str, Any],
) -> dict[str, Any]:
    """Return BLOCKED or SURVIVES with reasons, evidence IDs, and required next branch."""

def build_battle_plan(document: dict[str, Any]) -> dict[str, Any]:
    """Rank full leads, prioritize partial leads, and schedule only verified visits."""
```

- [ ] Add a failing test proving a blocked opportunity needs no judgments.

```python
def test_exact_role_no_sponsorship_filters_before_jev_scores_are_required(self):
    ranker = load_ranker()
    item = {
        "company": "Blocked Co",
        "role": "Software Intern",
        "user_interest": 1.0,
        "evidence_level": "EXACT_ROLE",
        "evidence_ids": ["sponsor-no"],
        "evidence": {
            "sponsorship": {"status": "no", "scope": "exact_role", "evidence_id": "sponsor-no"},
            "visit_access": "unknown",
            "session_status": "unknown",
        },
        "judgments": {},
    }
    payload = document(item, needs_sponsorship=True)
    payload["evidence_records"] = [{"claim_id": "sponsor-no", "claim": "Exact role says no."}]

    result = ranker.build_battle_plan(payload)["opportunities"][0]

    self.assertEqual(result["prefilter_state"], "BLOCKED")
    self.assertEqual(result["tier"], "SKIP")
    self.assertFalse(result["jev_required"])
```

- [ ] Add tests for user opt-out, exact citizenship/clearance mismatch, minimum experience mismatch, duplicate role, and unavailable visit channel. Assert each blocked result preserves reasons and evidence IDs.

- [ ] Add a failing test that employer-card sponsorship `no` does not hard-filter a sponsor-needing candidate.

- [ ] Run focused tests and confirm current code fails by demanding Score answers first.

Run: `python3 -m unittest tests.test_rank_battle_plan -v`

Expected: new prefilter tests fail before implementation.

- [ ] Extract deterministic prefiltering before `_score_value` calls. Require full judgments only for surviving `FULL` ranking candidates.

- [ ] Assign incomplete surviving leads a preliminary priority:

```python
PRELIMINARY_PRIORITIES = (
    "HIGH_VERIFY_FIRST",
    "MEDIUM_VERIFY",
    "DISCOVERY_ONLY",
    "LOW_DISCOVERY",
)
```

- [ ] Preserve v1 exact-role outputs when their evidence and judgments are complete, except where unknown access previously created a route.

- [ ] Run focused/full tests and commit.

```bash
python3 -m unittest tests.test_rank_battle_plan -v
python3 -m unittest discover -s tests -v
git add career-fair-battle-plan/scripts/rank_battle_plan.py tests/test_rank_battle_plan.py
git commit -m "refactor: prefilter opportunities before Jev scoring"
```

---

### Task 6: Enforce safe scheduling and preserve source/session state in output

**Files:**
- Modify: `career-fair-battle-plan/scripts/rank_battle_plan.py`
- Modify: `tests/test_rank_battle_plan.py`

- [ ] Write the exact regression test for the observed unknown-access bug.

```python
def test_unknown_visit_access_never_gets_fixed_or_flexible_schedule(self):
    ranker = load_ranker()
    item = opportunity("Unknown Access Co", "Software Intern")
    item["evidence"].update({"visit_access": "unknown", "session_status": "unknown"})

    plan = ranker.build_battle_plan(document(item))
    result = plan["opportunities"][0]

    self.assertEqual(result["route_action"], "CHECK_SESSION")
    self.assertNotIn("assigned_session", result)
    self.assertFalse(any(v["company"] == "Unknown Access Co" for v in plan["visit_schedule"]))
    self.assertEqual(result["evidence"]["visit_access"], "unknown")
    self.assertEqual(result["evidence"]["session_status"], "unknown")
```

- [ ] Add tests for unavailable access -> `APPLY_ONLINE`, verified fixed session, verified flexible booth, full session, schedule conflict, and access confidence below `0.80`.

- [ ] Add a test proving exact evidence `scope` survives the output.

- [ ] Run focused tests and confirm the unknown-access case fails under v1 flexible allocation.

- [ ] Change visit candidate selection to this invariant:

```python
def _is_schedulable(item: dict[str, Any]) -> bool:
    evidence = item["evidence"]
    return (
        evidence.get("visit_access") == "verified"
        and item["visit_access_confidence"] >= 0.80
        and evidence.get("session_status") in {"verified", "available"}
    )
```

- [ ] Remove the output cleanup that drops access/session fields. Add `route_action` and `route_exclusion_reason` instead.

- [ ] Run focused/full tests and commit.

```bash
python3 -m unittest tests.test_rank_battle_plan -v
python3 -m unittest discover -s tests -v
git add career-fair-battle-plan/scripts/rank_battle_plan.py tests/test_rank_battle_plan.py
git commit -m "fix: schedule only verified career fair access"
```

---

### Task 7: Build dynamic, cost-aware Jev request plans

**Files:**
- Create: `career-fair-battle-plan/scripts/plan_jev_requests.py`
- Create: `tests/test_jev_planner.py`

**Interface:**

```python
def build_jev_plan(document: dict[str, Any]) -> dict[str, Any]:
    """Return READY_FOR_JEV, NOT_NEEDED, or STOP plus atomic typed requests."""
```

- [ ] Write failing tests for question selection.

```python
def test_dynamic_plan_omits_irrelevant_questions(self):
    payload = base_planner_document()
    payload["candidate_profile"].update({
        "needs_sponsorship": False,
        "background_transition": "none",
    })
    payload["opportunities"][0].update({
        "career_stage_clear": True,
        "material_unknowns": [],
        "conversation_channel": "unavailable",
    })

    request = load_planner().build_jev_plan(payload)["requests"][0]
    names = [question["name"] for question in request["questions"]]

    self.assertEqual(names, ["best_area", "role_fit", "evidence_strength"])
    self.assertNotIn("sponsorship_evidence_supports_eligibility", names)
    self.assertNotIn("conversation_leverage", names)
```

- [ ] Add cases for career transition, unclear stage, material unknowns, plausible conversation, sponsor-needed unresolved exact role, exact sponsorship already resolved, and prefiltered `BLOCKED`.

- [ ] Add a token-minimization assertion that the request state excludes raw CV text and contains only a condensed profile, approved areas, source-scoped evidence summary, and hard constraints.

- [ ] Run and confirm missing-module failure.

- [ ] Implement deterministic question builders for `choice`, `score`, and `noul`, with allowed target areas plus `other` for `best_area`.

```python
def _question_names(profile, opportunity):
    names = ["best_area", "role_fit"]
    if opportunity.get("evidence_records"):
        names.append("evidence_strength")
    if opportunity.get("conversation_channel") in {"verified", "plausible"}:
        names.append("conversation_leverage")
    if opportunity.get("material_unknowns"):
        names.append("information_gain")
    if not opportunity.get("career_stage_clear", False):
        names.append("entry_level_accessible")
    if profile.get("background_transition") in {"adjacent", "major"}:
        names.append("background_pathway_accessible")
    if profile["needs_sponsorship"] and opportunity.get("exact_role_sponsorship") == "unknown":
        names.append("sponsorship_evidence_supports_eligibility")
    return names
```

- [ ] Return `NOT_NEEDED` when all leads are filtered, and `READY_FOR_JEV` with no false provider/model claim when no live client is configured.

- [ ] Run tests and commit.

```bash
python3 -m unittest tests.test_jev_planner -v
python3 -m unittest discover -s tests -v
git add career-fair-battle-plan/scripts/plan_jev_requests.py tests/test_jev_planner.py
git commit -m "feat: plan minimal Jev questions per opportunity"
```

---

### Task 8: Validate Jev results, hashes, ranges, cache, and telemetry

**Files:**
- Create: `career-fair-battle-plan/scripts/validate_jev_results.py`
- Modify: `tests/test_jev_planner.py`

**Interfaces:**

```python
def compute_request_hash(request: dict[str, Any]) -> str:
    """SHA-256 of canonical JSON state and ordered questions."""

def validate_jev_result(request: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    """Validate typed answers, provenance, hash, cache state, and telemetry."""
```

- [ ] Add failing boundary tests for Choice confidence, Score value/confidence/ranges, and Noul probabilities.

```python
def test_hash_mismatched_cache_is_rejected(self):
    validator = load_validator()
    request = minimal_request()
    result = minimal_result(request_hash="0" * 64, provenance="cache")

    with self.assertRaisesRegex(ValueError, "request_hash"):
        validator.validate_jev_result(request, result)

def test_fixture_result_cannot_claim_live_provenance(self):
    result = minimal_result(
        request_hash=load_validator().compute_request_hash(minimal_request()),
        provenance="fixture",
    )
    result["telemetry"]["provider"] = "live-jev"
    with self.assertRaisesRegex(ValueError, "fixture"):
        load_validator().validate_jev_result(minimal_request(), result)
```

- [ ] Add tests for stale cache timestamp, missing answer, extra answer, wrong type, reversed ranges, retry count, negative cost/tokens/latency, and valid live/fixture/cache results.

- [ ] Run and confirm missing-module failure.

- [ ] Implement canonical hashing.

```python
def compute_request_hash(request):
    normalized = {
        "state": request["state"],
        "questions": request["questions"],
    }
    encoded = json.dumps(
        normalized,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
```

- [ ] Validate provenance against `live`, `fixture`, `fallback`, and `cache`; require provider/model/timestamp only for observed live calls; preserve `request_count`, `question_count`, `latency_ms`, `retry_count`, `input_tokens`, `output_tokens`, and `cost_usd` when supplied.

- [ ] Do not add a network client or API key. Keep live connectivity as an explicit unverified boundary until an observed call succeeds.

- [ ] Run focused/full tests and commit.

```bash
python3 -m unittest tests.test_jev_planner -v
python3 -m unittest discover -s tests -v
git add career-fair-battle-plan/scripts/validate_jev_results.py tests/test_jev_planner.py
git commit -m "feat: validate Jev provenance and cache safety"
```

---

### Task 9: Expand the matrix to 30+ cases and replay every prior input

**Files:**
- Modify: `career-fair-battle-plan/scripts/run_scenario_matrix.py`
- Modify: `career-fair-battle-plan/examples/scenario_matrix.json`
- Regenerate: `career-fair-battle-plan/examples/scenario_matrix_results.json`
- Modify: `tests/test_scenario_matrix.py`
- Use: `tests/fixtures/regression-*.json`

- [ ] Extend the runner to support `intake`, `normalize`, `jev_plan`, `jev_validate`, and `rank` scenario kinds.

```python
RUNNERS = {
    "intake": lambda payload: intake.assess_intake(payload),
    "normalize": lambda payload: normalizer.normalize_source(payload),
    "jev_plan": lambda payload: planner.build_jev_plan(payload),
    "jev_validate": lambda payload: validator.validate_jev_result(
        payload["request"], payload["result"]
    ),
    "rank": lambda payload: ranker.build_battle_plan(payload),
}
```

- [ ] Change the count assertion to require at least 36 scenarios, with IDs unique and every required dimension represented.

```python
self.assertGreaterEqual(report["summary"]["total"], 36)
self.assertEqual(report["summary"]["failed"], 0)
self.assertEqual(len(ids), len(set(ids)))
```

- [ ] Include these candidate groups: conventional CS, adjacent-field transition, major career change, nontechnical/hybrid, sparse CV, and user-declared pivot.

- [ ] Include these policy groups: domestic/no sponsorship, temporary authorization, future sponsorship, unresolved sponsorship, hard/soft salary floor, location, citizenship/clearance, experience gap, and explicit avoid area.

- [ ] Include these source/access groups: upload, public web, public preview not registered, authenticated not registered, registered read-only, incomplete official page, login wall, no fair source, partial 6/11 coverage, stale listing, and conflicting sources.

- [ ] Include these session groups: verified fixed, verified flexible, full, unavailable, unknown, conflicting intervals, and insufficient access confidence.

- [ ] Include these Jev groups: not needed after hard filter, ready without client, fixture valid, malformed, stale cache, hash mismatch, cache hit, and retry telemetry.

- [ ] Replay all six prior regression fixtures and assert these minimum outcomes:

```text
domestic public preview       -> PARTIAL, no visit_schedule
sponsor public preview        -> PARTIAL, sponsor-card scope not exact-role
high evidence                 -> FULL candidates allowed; only verified sessions scheduled
transition plus sponsorship   -> background-pathway and sponsor questions included where unresolved
sparse ambiguous              -> STOP or PARTIAL, never fabricated FULL
Jev baseline                  -> fixture provenance retained; no live-call claim
```

- [ ] Run the matrix and inspect failures rather than weakening expectations.

Run: `python3 career-fair-battle-plan/scripts/run_scenario_matrix.py career-fair-battle-plan/examples/scenario_matrix.json -o /private/tmp/scenario_matrix_results.json`

Expected: exit `0`, summary total at least `36`, failed `0`.

- [ ] Copy the verified generated result into the committed example using `apply_patch`, then rerun its test.

Run: `python3 -m unittest tests.test_scenario_matrix -v`

Expected: all matrix and regression replay tests pass.

- [ ] Run the full suite and commit.

```bash
python3 -m unittest discover -s tests -v
git add career-fair-battle-plan/scripts/run_scenario_matrix.py career-fair-battle-plan/examples/scenario_matrix.json career-fair-battle-plan/examples/scenario_matrix_results.json tests/test_scenario_matrix.py
git commit -m "test: cover v2 decisions with scenario matrix"
```

---

### Task 10: Update the Skill, contracts, examples, and bilingual documentation

**Files:**
- Modify: `career-fair-battle-plan/SKILL.md`
- Modify: `career-fair-battle-plan/references/data-contracts.md`
- Modify: `career-fair-battle-plan/references/intake-and-access.md`
- Modify: `career-fair-battle-plan/references/jev-judgments.md`
- Modify: `career-fair-battle-plan/references/research-and-events.md`
- Create: `career-fair-battle-plan/references/decision-states.md`
- Create: `career-fair-battle-plan/references/source-adapters.md`
- Modify: `career-fair-battle-plan/examples/sample_input.json`
- Regenerate: `career-fair-battle-plan/examples/sample_output.json`
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Modify: `tests/test_readme_installation.py`

- [ ] Add failing documentation tests for all runnable commands, Python version, public-preview behavior, read-only account boundary, decision states, Jev provenance, cache location, scenario command, Skill validation, ZIP installation, and no-registration limitations in both languages.

- [ ] Run the documentation tests and confirm missing v2 content.

Run: `python3 -m unittest tests.test_readme_installation -v`

Expected: new assertions fail before docs are updated.

- [ ] Rewrite `SKILL.md` as a router to the six focused references. Keep the profile approval checkpoint before source/ranking work.

- [ ] Document exact JSON contracts for access state, evidence record, opportunity confidence, Jev request/result, STOP/PARTIAL/FULL output, preliminary priorities, final tiers, and action cards.

- [ ] Document source boundaries for Handshake, LinkedIn-visible pages, official school pages, uploads, and employer careers. State that platform visibility can change and missing data stays unknown.

- [ ] Document Jev-first cost control accurately: deterministic filters first; Jev for surviving semantic questions only; no embedded client/key; fixture/fallback/live labels are mandatory.

- [ ] Generate `sample_output.json` by running the actual pipeline scripts on `sample_input.json`; do not hand-author an impossible route.

- [ ] Update both READMEs with matching installation and usage sequences:

```bash
git clone https://github.com/SSSls/career-fair-battle-plan.git
cd career-fair-battle-plan
python3 --version
python3 -m unittest discover -s tests -v
python3 career-fair-battle-plan/scripts/assess_intake.py career-fair-battle-plan/examples/sample_input.json
python3 career-fair-battle-plan/scripts/run_scenario_matrix.py career-fair-battle-plan/examples/scenario_matrix.json
```

- [ ] Run focused/full tests and Skill validation.

Run: `python3 -m unittest tests.test_readme_installation -v`

Run: `python3 -m unittest discover -s tests -v`

Run: `python3 /Users/sunchunxuan/.codex/skills/.system/skill-creator/scripts/quick_validate.py career-fair-battle-plan`

Expected: tests pass and validator prints `Skill is valid!`.

- [ ] Commit.

```bash
git add career-fair-battle-plan README.md README.zh-CN.md tests/test_readme_installation.py
git commit -m "docs: publish v2 workflow in English and Chinese"
```

---

### Task 11: Perform current, read-only source validation across Penn and three other schools

**Files:**
- Create: `docs/validation/2026-09-25-live-read-only-sources.md`
- Modify only if a reproducible adapter defect is observed: `career-fair-battle-plan/examples/live-source-fixtures/*.json`
- Modify only after a failing test: relevant script and test file

- [ ] Inspect the user-opened Penn Handshake event only if the browser visibly shows a logged-in session. Record authentication and registration independently. Do not register, waitlist, save, message, apply, upload, or edit.

- [ ] If the login is absent or expired, stop authenticated inspection and ask the user to log in themselves; never request credentials or complete MFA.

- [ ] Validate a Penn public preview without relying on account state.

- [ ] Validate current official sources for Cornell, UC Berkeley, and one additional university chosen from a current official page. Use official sources for event metadata and public visibility claims.

- [ ] For every source record:

```text
accessed_at
school and fair label
URL or public artifact label
source mode
authentication state
registration state if visible
fields visible
fields missing
coverage visible/advertised
adapter result
decision state
whether any mutation occurred: no
```

- [ ] Convert only minimal, nonprivate field shapes into fixture updates. Do not commit account-only employer/session details, screenshots containing identity, URLs with private tokens, or browser/session metadata.

- [ ] Run the applicable normalizer and pipeline on each minimal fixture. If any assertion fails, add one focused failing test, make the smallest implementation correction, and rerun the full suite before continuing.

- [ ] Explicitly distinguish observed current results from historical/public examples in the validation report.

- [ ] Run the full suite and commit the sanitized validation report and fixture corrections.

```bash
python3 -m unittest discover -s tests -v
git add docs/validation career-fair-battle-plan/examples/live-source-fixtures tests career-fair-battle-plan/scripts
git commit -m "test: validate read-only university source patterns"
```

---

### Task 12: Package, audit, and release to GitHub

**Files:**
- Regenerate: `career-fair-battle-plan.zip`
- Inspect: all tracked and untracked files

- [ ] Run all verification gates from a clean command sequence.

```bash
python3 -m unittest discover -s tests -v
python3 career-fair-battle-plan/scripts/run_scenario_matrix.py career-fair-battle-plan/examples/scenario_matrix.json -o /private/tmp/cfbp-v2-matrix.json
python3 /Users/sunchunxuan/.codex/skills/.system/skill-creator/scripts/quick_validate.py career-fair-battle-plan
```

Expected: unit suite passes; matrix has at least 36 total and 0 failed; validator prints `Skill is valid!`.

- [ ] Rebuild the ZIP from the Skill directory without temporary files or caches.

Run: `ditto -c -k --sequesterRsrc --keepParent career-fair-battle-plan /private/tmp/career-fair-battle-plan.zip`

- [ ] Inspect the archive before replacing the tracked ZIP.

Run: `unzip -l /private/tmp/career-fair-battle-plan.zip`

Expected: one `career-fair-battle-plan/` root; no `.DS_Store`, `__pycache__`, `.env`, credentials, tests, private fixtures, or browser data.

- [ ] Replace `career-fair-battle-plan.zip` using the verified artifact and confirm its SHA-256.

- [ ] Scan tracked and untracked text for secrets and private artifacts.

Run: `git status --short`

Run: `git grep -n -I -E '(AKIA[0-9A-Z]{16}|-----BEGIN (RSA|OPENSSH|EC) PRIVATE KEY-----|api[_-]?key[[:space:]]*[:=]|access[_-]?token[[:space:]]*[:=]|session[_-]?cookie)' -- . ':!docs/superpowers/plans/2026-09-25-career-fair-battle-plan-v2.md'`

Expected: no actual secrets; documentation-only words are manually reviewed.

- [ ] Scan for private temp paths and real candidate/account material.

Run: `git grep -n -I '/private/tmp\|pennkey\|MFA code\|session token' -- .`

Expected: only this plan may mention `/private/tmp`; no account identifier, token, real CV, or private export is tracked.

- [ ] Review formatting and the complete diff.

Run: `git diff --check`

Run: `git diff --stat origin/main...HEAD`

Run: `git diff origin/main...HEAD`

- [ ] Commit the package only after all gates pass.

```bash
git add career-fair-battle-plan.zip
git commit -m "release: package career fair battle plan v2"
```

- [ ] Confirm the final commit set and push.

Run: `git status --short --branch`

Expected: clean worktree and branch ahead of `origin/main` only by reviewed v2 commits.

Run: `git push origin main`

Expected: push succeeds and GitHub `main` points to the verified release commit.

- [ ] Verify the remote without changing it.

Run: `git ls-remote --heads origin main`

Expected: remote `main` SHA equals local `git rev-parse HEAD`.

---

## Spec Coverage Checklist

- [ ] Candidate profile approval and hard-input STOP gate: Tasks 2 and 4.
- [ ] Public preview plus independent login/registration states: Tasks 2 and 11.
- [ ] Multi-source evidence adapters and scope: Task 3.
- [ ] STOP/PARTIAL/FULL and confidence caps: Task 4.
- [ ] Hard filters before Jev: Task 5.
- [ ] Verified-only scheduling and state-preserving output: Task 6.
- [ ] Dynamic minimal Jev questions: Task 7.
- [ ] Jev typing, provenance, cache, telemetry, and cost boundary: Task 8.
- [ ] Prior inputs plus 36-or-more scenarios: Tasks 1 and 9.
- [ ] Skill, examples, English/Chinese installation docs: Task 10.
- [ ] Penn account read-only plus three other school patterns: Task 11.
- [ ] ZIP, privacy/secret audit, commit, and GitHub synchronization: Task 12.

## Plan Self-Review Gates

- [ ] Search this plan for unresolved implementation markers.

Run: `rg -n 'TO''DO|T''BD|FIX''ME|place''holder|similar'' to|and so'' on' docs/superpowers/plans/2026-09-25-career-fair-battle-plan-v2.md`

Expected: no matches.

- [ ] Confirm every new Python interface has a named test task and every new file appears in the target map.

- [ ] Confirm type consistency: source access enums are uppercase; evidence status is lowercase; decision states and preliminary/final tiers are uppercase; `visit_access` remains lowercase `verified|unknown|unavailable` for v1 compatibility.

- [ ] Confirm review-focus coverage:
  - malformed/contradictory access: Task 2;
  - partial 6/11 coverage: Tasks 3 and 9;
  - title/employer-card sponsor scope: Tasks 3, 4, and 5;
  - unknown access route exclusion: Task 6;
  - stale/malformed/hash-mismatched Jev data: Task 8.

- [ ] Check Markdown whitespace.

Run: `git diff --check -- docs/superpowers/plans/2026-09-25-career-fair-battle-plan-v2.md`

Expected: no errors.
