# Career Fair Battle Plan

[English](README.md) | [简体中文](README.zh-CN.md)

An open-source Codex skill that helps job seekers allocate limited career-fair time across employers, exact roles, and sessions. It supports career changes, adjacent-field moves, sponsorship constraints, uncertain target areas, and both virtual and in-person events.

## What it optimizes

The project answers **“Where should I spend my limited fair time?”**, not merely “Should I apply?” It produces four auditable outcomes:

- `MUST_VISIT`
- `IF_TIME`
- `APPLY_ONLINE`
- `SKIP`

## Architecture

- **LLM/Codex:** understands the résumé, builds a user-approved profile, summarizes evidence, and writes human-facing guidance.
- **TypeSafe Jev:** returns atomic typed Choice, Score, and Noul judgments when live API access is configured.
- **Deterministic Python:** applies hard constraints, weights, confidence gates, evidence integrity, fair capacity, and schedule conflicts.
- **Read-only browser access:** inspects visible authenticated Handshake pages after the user logs in. It never handles passwords, MFA, or CAPTCHAs.

## Required inputs

- résumé or equivalent background material;
- school, degree/program, graduation date, and target role type;
- desired, pivot, and avoided areas;
- work authorization and sponsorship requirement;
- location, salary, and headcount preferences;
- fair name, date, timezone, format, link, and available company/session data.

The candidate profile must be explicitly approved before company research or ranking begins.

## Workflow

1. Assess candidate and fair-data completeness.
2. Require user login plus read-only authorization for live Handshake retrieval.
3. Build and approve the candidate profile and target-area set.
4. Normalize the fair into `company × exact role` opportunities.
5. Apply cheap filters before deeper research.
6. Collect cited evidence for the role, sponsorship, headcount, salary, eligibility, and sessions.
7. Run Jev typed judgments, or clearly report that Jev is unavailable.
8. Rank opportunities in deterministic code and generate a time-feasible battle plan.

Missing or conflicting evidence remains `unknown`; historical H-1B/PERM activity does not prove that a current role sponsors.

## Repository layout

```text
career-fair-battle-plan/
├── SKILL.md
├── agents/openai.yaml
├── examples/
├── references/
└── scripts/
tests/
```

The installable skill entrypoint is [`career-fair-battle-plan/SKILL.md`](career-fair-battle-plan/SKILL.md).

## Quick start

```bash
python3 career-fair-battle-plan/scripts/assess_intake.py intake.json

python3 career-fair-battle-plan/scripts/rank_battle_plan.py \
  career-fair-battle-plan/examples/sample_input.json \
  -o career-fair-battle-plan/examples/sample_output.json

python3 career-fair-battle-plan/scripts/run_scenario_matrix.py \
  career-fair-battle-plan/examples/scenario_matrix.json \
  -o career-fair-battle-plan/examples/scenario_matrix_results.json

python3 -m unittest discover -s tests -v
```

The deterministic scripts use only the Python standard library.

## Jev access

Live Jev evaluation requires current TypeSafe API access and `TYPESAFE_API_KEY`. No credentials are included. The deterministic demo does not prove live Jev connectivity; recheck the official TypeSafe documentation before integration because the API may evolve.

## Privacy and permissions

- Send an approved condensed profile to Jev, not the full résumé.
- Keep API keys and credentials outside version control.
- The user enters passwords and completes MFA themselves.
- Never bypass authentication or inspect hidden private endpoints.
- Registration, waitlists, messages, emails, applications, uploads, follows, saves, and profile edits require explicit confirmation immediately before execution.

## Validation

- 36 deterministic behavior tests;
- 22 editable parameterized scenarios;
- 10 independent agent simulations: 3 no-skill baselines and 7 skill-enabled forward tests;
- official `quick_validate.py` package validation.

Authenticated Handshake read-only access was manually validated. Live Jev API connectivity has not been validated in this repository.

## Current scope

The implemented authenticated source is Handshake. Public web pages and user-supplied exports are also supported. LinkedIn, school portals, and employer ATS integrations are design targets, not completed adapters.

## License

[MIT](LICENSE)
